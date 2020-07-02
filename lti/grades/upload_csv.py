#!/usr/bin/env python
"""
Send grades to an OpenEdX LTI component
"""
from __future__ import print_function
from __future__ import absolute_import
from argparse import ArgumentParser
import base64
import csv
import hashlib
import json
import re
import six.moves.urllib.request, six.moves.urllib.parse, six.moves.urllib.error

import mock
from oauthlib.oauth1 import Client  # pylint: disable=F0401
import requests
import six
from six.moves import input


def _main():
    """
    Send grades to an OpenEdX LTI component via command-line
    """
    arguments = _parse_command_line_arguments()
    try:
        mapping = _get_uid_to_anon_map(arguments['mapping_csv'])
        test_anon_id = next(six.itervalues(mapping))

        print("Fetching LTI units for course_id: {course_id}".format(
            course_id=arguments['course_id'],
        ))
        endpoint = _prompt_select_lti_endpoint(
            arguments['platform_url'],
            arguments['course_id']
        )
        endpoint_url = re.sub(
            r'\{anon_user_id\}',
            '',
            endpoint['lti_2_0_result_service_json_endpoint']
        )
        test_url = endpoint_url + test_anon_id
        _validate_lti_passport(
            arguments['lti_key'],
            arguments['lti_secret'],
            test_url
        )
        for row in _generate_valid_grading_rows(arguments['grade_csv']):
            _post_grade(
                mapping,
                endpoint_url,
                arguments['lti_key'],
                arguments['lti_secret'],
                row
            )
    except _LTIToolError as error:
        print(error.message)
        exit()


def _parse_command_line_arguments():
    """
    Parse and return command line arguments
    """
    parser = ArgumentParser(
        description=(
            'Command line tool for sending grades to open edX LTI components'
        ),
    )
    parser.add_argument(
        'course_id',
        type=str,
        help=(
            'The course triplet to operate on, '
            'e.g. StanfordOnline/OpenEdX/Demo'
        ),
    )
    parser.add_argument(
        'grade_csv',
        type=str,
        help=(
            'The path of the CSV file containing the grades. '
            'The first column must be the student user id, '
            'the second the student email address, '
            'the third a numeric score, '
            'the fourth the total possible numeric score, '
            'and the (optional) fifth a short text comment.'
        ),
    )
    parser.add_argument(
        'mapping_csv',
        type=str,
        help=(
            'The path of the CSV file containing the mapping from '
            'user_id to anon_id. This file is downloadable from the '
            'instructor tab of the course.'
        ),
    )
    parser.add_argument(
        'lti_key',
        type=str,
        help='The key part of the LTI Passport configured for the course'
    )
    parser.add_argument(
        'lti_secret',
        type=str,
        help='The secret part of the LTI Passport configured for the course'
    )
    parser.add_argument(
        '--platform-url',
        required=True,
        type=str,
        help='The base URL of an OpenEdx platform instance',
    )
    arguments = vars(parser.parse_args())
    return arguments


def _validate_lti_passport(key, secret, url):
    """
    Sanity-check LTI passport credentials
    """
    resp = _send_lti_2_json_request('GET', url, key, secret)
    if resp.status_code != 200:
        raise _LTIToolError(
            "LTI passport sanity check failed. Your lti_key ({key}) or"
            "lti_secret ({secret}) are probably incorrect.".format(
                key=key,
                secret=secret,
            )
        )


def _prompt_select_lti_endpoint(platform_url, course_id):
    """
    Prompt for an LTI endpoint
    """
    url = "{platform_url}/courses/{course_triplet}/lti_rest_endpoints/".format(
        platform_url=platform_url,
        course_triplet=course_id,
    )
    response = requests.get(url)
    if response.status_code != 200:
        raise _LTIToolError(
            "No course was found. Your course_id ({course_id}) may be "
            "invalid.".format(
                course_id=course_id,
            )
        )
    endpoints = sorted(response.json(), key=lambda e: e['display_name'])
    _print_all_endpoints(endpoints)
    choice_num = int(input('Enter the number of your endpoint: '))
    return endpoints[choice_num]


def _send_lti_2_json_request(method, url, key, secret, data=None):
    """
    Issue a session-based LTI request
    """
    session = requests.Session()
    request = requests.Request(method, url, data=data)
    request.headers.update({
        'Content-Type': 'application/vnd.ims.lis.v2.result+json',
    })
    request_prepared = session.prepare_request(request)
    auth_header_val = _get_authorization_header(request_prepared, key, secret)
    request.headers.update({
        'Authorization': auth_header_val,
    })
    request_prepared_authorized = session.prepare_request(request)
    response = session.send(request_prepared_authorized)
    return response


def _get_uid_to_anon_map(filename):
    """
    Map user IDs to anonymous user IDs
    """
    mapping = {}
    with open(filename) as file_input:
        reader = _unicode_csv_reader(file_input)
        for row in reader:
            if len(row) < 2:
                print(
                    "BAD ROW: mapping_csv row {row} doesn't have enough "
                    "info".format(
                        row=row,
                    )
                )
                continue
            elif row[0] == 'User ID':
                continue
            else:
                mapping[int(row[0])] = row[1]
    if len(mapping) < 1:
        raise _LTIToolError('Mapping CSV file had no useful data!')
    return mapping


def _generate_valid_grading_rows(filename):
    """
    Yield valid grading rows from a file
    """
    with open(filename) as file_input:
        reader = _unicode_csv_reader(file_input)
        row_num = 0
        for row in reader:
            row_num += 1
            if len(row) < 4:
                print(
                    "BAD ROW: grading_csv row {row_number} ({row}) "
                    "doesn't have enough info".format(
                        row_number=row_num,
                        row=row,
                    )
                )
                continue
            try:
                if len(row) == 4:
                    yield tuple([
                        int(row[0]),
                        six.text_type(row[1]),
                        float(row[2]),
                        float(row[3]),
                    ])
                else:
                    yield tuple([
                        int(row[0]),
                        six.text_type(row[1]),
                        float(row[2]),
                        float(row[3]),
                        six.text_type(row[4]),
                    ])
            except ValueError:
                print(
                    "BAD ROW: grading_csv row {row_number} ({row}) "
                    "has bad values".format(
                        row_number=row_num,
                        row=row,
                    )
                )
                continue


def _post_grade(mapping, url_base, key, secret, grade_row):
    """
    Post a grade to the LTI endpoint
    """
    comment = ''
    uid, email, grade, total = grade_row[:4]
    if len(grade_row) >= 5:
        comment = grade_row[4]
    if uid not in mapping:
        print(
            "GRADE POST FAILED: user id {user_id} (email: {email}) "
            "is not in provided mapping file".format(
                user_id=uid,
                email=email,
            )
        )
        return
    url = url_base + mapping[uid]

    payload = {
        '@context': 'http://purl.imsglobal.org/ctx/lis/v2/Result',
        '@type': 'Result',
        'comment': comment,
        'resultScore': grade/total,
    }

    resp = _send_lti_2_json_request(
        'PUT',
        url,
        key,
        secret,
        data=json.dumps(payload),
    )
    if resp.status_code != 200:
        print(
            "GRADE POST FAILED: user id {user_id} (email: {email}). "
            "Request was unsuccessful".format(
                user_id=uid,
                email=email,
            )
        )
    else:
        print(
            "GRADE POST SUCCESSFUL: user id {user_id} "
            "(email: {email}).".format(
                user_id=uid,
                email=email,
            )
        )


def _unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    """
    Yield CSV entries as UTF-8 encoded strings
    """
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(_utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [six.text_type(cell, 'utf-8') for cell in row]


def _utf_8_encoder(unicode_csv_data):
    """
    Yield CSV lines as UTF-8 encoded strings
    """
    for line in unicode_csv_data:
        yield line.encode('utf-8')


def _print_all_endpoints(endpoints):
    """
    Print all LTI endpoints to stdout
    """
    print('Select an LTI Unit:')
    for i, endpoint in enumerate(endpoints):
        print("  {choice}. {display_name} ({url})".format(
            choice=i,
            display_name=endpoint['display_name'],
            url=endpoint['lti_2_0_result_service_json_endpoint']
        ))


def _get_authorization_header(request, client_key, client_secret):
    """
    Get proper HTTP Authorization header for a given request

    Arguments:
        request: Request object to log Authorization header for

    Returns:
        authorization header
    """
    sha1 = hashlib.sha1()
    body = request.body or ''
    sha1.update(body)
    oauth_body_hash = six.text_type(base64.b64encode(
        sha1.digest()  # pylint: disable=too-many-function-args
    ))
    client = Client(client_key, client_secret)
    params = client.get_oauth_params(None)
    params.append((u'oauth_body_hash', oauth_body_hash))
    mock_request = mock.Mock(
        uri=six.text_type(six.moves.urllib.parse.unquote(request.url)),
        headers=request.headers,
        body=u'',
        decoded_body=u'',
        oauth_params=params,
        http_method=six.text_type(request.method),
    )
    sig = client.get_oauth_signature(mock_request)
    mock_request.oauth_params.append((u'oauth_signature', sig))

    _, headers, _ = client._render(  # pylint: disable=protected-access
        mock_request
    )
    return headers['Authorization']


class _LTIToolError(Exception):
    """
    Throw application-specific exceptions
    """
    pass


if __name__ == '__main__':
    _main()
