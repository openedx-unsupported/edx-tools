#!/usr/bin/env python

import os
import datetime
from dateutil import parser
import subprocess
import re
from optparse import OptionParser, OptionError
from collections import OrderedDict
import matplotlib.pyplot as plt

DEFAULT_REPO_DIR = "../../edx-platform"
DEFAULT_FROM_BRANCH = "edx-west/release"
DEFAULT_TO_BRANCH = "master"
DEFAULT_DIFF_FILENAME = "diff"

def main():
    options = parsecommandline()
    os.chdir(options.repodir)

    from_branch = options.frombranch
    from_branch_origin = "origin/"+from_branch
    to_branch = options.tobranch
    to_branch_origin = "origin/"+to_branch

    (start_date, end_date) = calculate_dates(options, from_branch_origin, to_branch_origin)
    print "scanning from %s to %s" % (start_date.strftime("%Y-%m-%d"), \
                end_date.strftime("%Y-%m-%d"))

    (difflines, diffblocks) = branch_diffs(from_branch_origin, to_branch_origin, 
            start_date, end_date)

    plt.figure(1)
    plt.subplot(211)
    plt.title("Size of diff between %s and %s" % (from_branch, to_branch))
    plt.plot(difflines.keys(), difflines.values())

    plt.subplot(212)
    plt.title("Changes between %s and %s" % (from_branch, to_branch))
    plt.plot(diffblocks.keys(), diffblocks.values())

    plt.savefig("diff")


def parsecommandline():
    usage = """usage: %prog [options]

Generate graphs comparing branches in an edx repo checked out closeby."""

    parser = OptionParser(usage=usage)

    parser.add_option("-d", dest="repodir", default=DEFAULT_REPO_DIR,
            help="relative path to the edx-platform repo " + \
                    "(default \"%s\")" % DEFAULT_REPO_DIR)
    parser.add_option("-f", dest="frombranch", default=DEFAULT_FROM_BRANCH,
            help="branch comparing from, do not include \"origin\" " + \
                    "(default \"%s\")" % DEFAULT_FROM_BRANCH)
    parser.add_option("-t", dest="tobranch", default=DEFAULT_TO_BRANCH,
            help="branch comparing to, do not include \"origin\" " + \
                    "(default \"%s\")" % DEFAULT_TO_BRANCH)
    parser.add_option("-s", dest="startdate", default=None,
            help="date to begin with, default is oldest date common to both branches." + \
                    "Use this to force an older date (ie past rebases).")
    parser.add_option("-e", dest="enddate", default=None,
            help="date to end with (default today)")
    parser.add_option("-g", dest="diff_filename", default=DEFAULT_DIFF_FILENAME,
            help="file for diff graph relative to repo dir " +\
                    "(default \"%s\")" % DEFAULT_DIFF_FILENAME)

    options, args = parser.parse_args()
    if args:
        raise OptionError("unknown option")

    return options


def calculate_dates(options, from_branch_origin, to_branch_origin):
    """
    Either parse date strings given on the command line, or figure out defaults.
    end is easy (today), start means looking at branches.
    """
    if options.startdate:
        start_date = parser.parse(options.startdate).date()
    else:
        fromdate = beginning_of_branch(from_branch_origin)
        todate = beginning_of_branch(to_branch_origin)
        start_date = min(fromdate,todate).date()

    if options.enddate:
        end_date = parser.parse(options.enddate).date()
    else:
        end_date = datetime.date.today()

    return (start_date, end_date)


def beginning_of_branch(name):
    commit = oldest_commit_on_branch(name)
    date = date_from_git_commithash(commit)
    print "oldestcommit on", name, "is", commit, " date =", date.strftime("%Y-%m-%d")
    return date

def oldest_commit_on_branch(branchname):
    gitcmd = ['git', 'rev-list', '--first-parent', '-1', branchname]
    hashstr = subprocess.check_output(gitcmd)
    return hashstr.strip()

def date_from_git_commithash(commithash):
    # Consider %ad instead for the author date. This is committer date.
    gitcmd = ['git', 'show', '-s', '--format=%ci', commithash]
    datestr = subprocess.check_output(gitcmd)
    return parser.parse(datestr)


def branch_diffs(from_branch, to_branch, start_date, end_date):
    """
    Scan over date range, running "gid diff" between braches, and count 
    differences. Returns two ordered dicts by date, one of size of diff 
    in lines, one in blocks.

    Date range cleveness from stack overflow (http://goo.gl/frxo0).
    """
    def daterange(start_date, end_date):
        for n in range(int ((end_date - start_date).days)):
            yield start_date + datetime.timedelta(n)

    difflines = OrderedDict()
    diffblocks = OrderedDict()
    for d in daterange(start_date, end_date):
        diffcmd = ["git", "diff", "%s@{%s}" % (from_branch, d), "%s@{%s}" % (to_branch, d)]
        diffoutput = subprocess.check_output(diffcmd)
        lines = 0
        blocks = 0
        diff_block_re = re.compile('^--- ')
        for line in diffoutput.splitlines():
            lines += 1
            if diff_block_re.match(line):
                blocks += 1
        difflines[d] = lines
        diffblocks[d] = blocks
        print "diff:", d.strftime('%Y-%m-%d'), lines, blocks

    return (difflines, diffblocks)


if __name__ == '__main__':
    main()

