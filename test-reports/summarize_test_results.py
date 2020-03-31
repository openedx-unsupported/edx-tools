"""
summarize_test_results.py

$ python summarize_test_results.py reports/ > test_summary.html

where the "reports" directory is inside the archive of an edx-platform
CI test run output by Jenkins.
"""

import collections
import csv
import os
import re
import six
import sys
import textwrap
from xml.sax.saxutils import escape

import click
from lxml import etree

# Currently, both nose test results and pytest test results are saved
# to the same nose-like filename. The name may change in the future -
# but, for now, don't let the name confuse you!
TEST_RESULT_XML_FILENAMES = ['lms_test_report.xml', 'cms_test_report.xml', 'nosetests.xml', 'xunit.xml']


class HtmlOutlineWriter(object):
    HEAD = textwrap.dedent(r"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8" />
        <style>
        html {
            font-family: sans-serif;
        }
        .toggle-box {
            display: none;
        }

        .toggle-box + label {
            cursor: pointer;
            display: block;
            line-height: 21px;
            margin-bottom: 5px;
        }

        .toggle-box + label + div {
            display: none;
            margin-bottom: 10px;
        }

        .toggle-box:checked + label + div {
            display: block;
        }

        .toggle-box + label:before {
            color: #888;
            content: "\25B8";
            display: block;
            float: left;
            height: 20px;
            line-height: 20px;
            margin-right: 5px;
            text-align: center;
            width: 20px;
        }

        .toggle-box:checked + label:before {
            content: "\25BE";
        }

        .error, .skipped {
            margin-left: 2em;
        }

        .count {
            font-weight: bold;
        }

        .test {
            margin-left: 2em;
        }

        .stdout {
            margin-left: 2em;
            font-family: Consolas, monospace;
        }
        </style>
        </head>
        <body>
    """)

    SECTION_START = textwrap.dedent(u"""\
        <div class="{klass}">
        <input class="toggle-box {klass}" id="sect_{id:05d}" type="checkbox">
        <label for="sect_{id:05d}">{html}</label>
        <div>
    """)

    SECTION_END = "</div></div>"

    def __init__(self, fout):
        self.fout = fout
        self.section_id = 0
        self.fout.write(self.HEAD)

    def start_section(self, html, klass=None):
        self.fout.write(self.SECTION_START.format(
            id=self.section_id, html=html, klass=klass or "",
        ))
        self.section_id += 1

    def end_section(self):
        self.fout.write(self.SECTION_END)

    def write(self, html):
        self.fout.write(html)


class Summable(object):
    """An object whose attributes can be added together easily.

    Subclass this and define `fields` on your derived class.

    """
    def __init__(self):
        for name in self.fields.values():
            setattr(self, name, 0)

    @classmethod
    def from_element(cls, element):
        """Construct a Summable from an xml element with the same attributes."""
        self = cls()
        for attr, name in six.iteritems(self.fields):
            element_val = element.get(attr)
            if element_val:
                setattr(self, name, int(element_val))
        return self

    def __add__(self, other):
        result = type(self)()
        # De-dup all the attribute names and add them.
        for name in list(set(self.fields.values())):
            setattr(result, name, getattr(self, name) + getattr(other, name))
        return result


class TestResults(Summable):
    """A test result, makeable from a XML <testsuite> element."""

    # fields = ["tests", "errors", "failures", "skip"]
    # Mapping of XML test result to summable attribute name.
    fields = {
        "tests": "tests",
        "errors": "errors",
        "failures": "failures",
        "skip": "skips",
        "skips": "skips"
    }

    def __str__(self):
        msg = "{0.tests:4d} tests, {0.errors} errors, {0.failures} failures, {0.skips} skipped"
        return msg.format(self)


def error_line_from_error_element(element):
    """Given an <error> element, get the important error line from it."""
    line = None
    message = element.get("message")
    if message is not None:
        message_lines = message.splitlines()
        if message_lines:
            line = message_lines[0].strip()

    if line is None:
        if element.text is None:
            return ""
        # The raised error must be extracted from the XML element text
        # from the line that starts with "E      ".
        line = ""
        err_line_regex = re.compile('^E[\s]+(.*)$')
        text = element.text
        if text is not None:
            for error_line in text.splitlines():
                err_match = err_line_regex.match(error_line)
                if err_match:
                    line = err_match.groups()[0]
                    break
        else:
            line = element.get("type")
    return line


def testcase_id(testcase):
    """
    Given a <testcase> element, return the a useful display name
    for the test.
    """
    test_file = testcase.get("file")

    if not test_file:
        test_file = "unknown"
    elif test_file.startswith("djangoapps"):
        # CMS tests don't seem to have the path starting from the top-level
        # directory for some reason.  Perhaps because of where the pytest
        # config is?  We might run into an issue when we collect common tests
        # which might have the same problem.
        test_file = "cms/" + test_file

    return u"{filename}::{classname}::{name}".format(
        filename=test_file,
        classname=testcase.get("classname").split('.')[-1],
        name=testcase.get("name"),
    )


def clipped(text, maxlength=150):
    """Return the text, but at most `maxlength` characters."""
    if len(text) > maxlength:
        text = text[:maxlength-1] + u"\N{HORIZONTAL ELLIPSIS}"
    return text

def get_errors(xml_tree):
    """
    Return a list of errors and their instances sorted by number of times
    each error happens from most to least.
    """
    errors = collections.defaultdict(list)
    for element in xml_tree.xpath(".//error|.//failure"):
        error_line = error_line_from_error_element(element)
        testcases = element.xpath("..")
        if testcases:
            errors[error_line].append(testcases[0])

    errors = sorted(errors.items(), key=lambda kv: len(kv[1]), reverse=True)
    return errors


def report_file(path, html_writer):
    """Report on one test result XML file."""

    with open(path) as xml_file:
        tree = etree.parse(xml_file)                # pylint: disable=no-member
    suite = tree.xpath("//testsuite")[0]

    errors = get_errors(tree)

    results = TestResults.from_element(suite)
    html = u'<span class="count">{number}:</span> {path}: {results}'.format(
        path=escape(path),
        results=results,
        number=results.errors+results.failures,
    )
    html_writer.start_section(html, klass="file")

    for message, testcases in errors:
        html = u'<span class="count">{0:d}:</span> {1}'.format(len(testcases), escape(clipped(message)))
        html_writer.start_section(html, klass="error")
        for testcase in testcases:
            html_writer.start_section(escape(testcase_id(testcase)), klass="test")
            error_element = testcase.xpath("error|failure")[0]
            html_writer.write("""<pre class="stdout">""")
            html_writer.write(escape(error_element.get("message")))
            html_writer.write(u"\n"+escape(error_element.text))
            html_writer.write("</pre>")
            html_writer.end_section()
        html_writer.end_section()

    skipped = collections.defaultdict(list)
    for element in tree.xpath(".//skipped"):
        error_line = error_line_from_error_element(element)
        testcases = element.xpath("..")
        if testcases:
            skipped[error_line].append(testcases[0])

    if skipped:
        total = sum(len(v) for v in skipped.values())
        html_writer.start_section(u'<span class="count">{0:d}:</span> Skipped'.format(total), klass="skipped")
        skipped = sorted(skipped.items(), key=lambda kv: len(kv[1]), reverse=True)
        for message, testcases in skipped:
            html = u'<span class="count">{0:d}:</span> {1}'.format(len(testcases), escape(clipped(message)))
            html_writer.start_section(html, klass="error")
            for testcase in testcases:
                html_writer.write('<div>{}</div>'.format(escape(testcase_id(testcase))))
            html_writer.end_section()

        html_writer.end_section()

    html_writer.end_section()
    return results


DESCRIPTION = textwrap.dedent("""
    Fix all know instances of this issue.  You should be able to find instances
    of this error in the test report posted to the edx-platform-py3 slack channel.

    One failing testcase that can be run as you're testing is:
    {{code}}
    tox -e py35-django111 -- pytest {testcase}
    {{code}}
""")


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def csv_file(path, writer):
    with open(path) as xml_file:
        tree = etree.parse(xml_file)

    errors = get_errors(tree)
    for message, testcases in errors:
        description = DESCRIPTION.format(
            count=len(testcases),
            testcase=testcase_id(testcases[0]),
        )

        writer.writerow([message[:255], description,"placeholder"])

def valid_report_files(start):
    for dirpath, _, filenames in os.walk(start):
        for report_filename in TEST_RESULT_XML_FILENAMES:
            if report_filename in filenames:
                yield os.path.join(dirpath, report_filename)


def main_html(start):
    totals = TestResults()
    html_writer = HtmlOutlineWriter(sys.stdout)
    for report_path in valid_report_files(start):
        results = report_file(report_path, html_writer)
        totals += results
    html_writer.write(escape(str(totals)))


def main_csv(start):
    csv_writer = csv.writer(sys.stdout)
    csv_writer.writerow(["Summary", "Description","Label"])
    for report_path in valid_report_files(start):
        results = csv_file(report_path, csv_writer)


@click.command()
@click.argument('path')
@click.option('-o','--output-type', type=click.Choice(['CSV', 'HTML']), default='HTML')
def main(path, output_type):
    if output_type == "CSV":
        main_csv(path)
    elif output_type == "HTML":
        main_html(path)

if __name__ == "__main__":
    main()
