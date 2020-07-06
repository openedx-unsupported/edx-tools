#!/usr/bin/env python

from __future__ import absolute_import
from pymongo import MongoClient
from xml.etree.cElementTree import fromstring, ParseError
from collections import defaultdict
import csv
import sys
import six

def is_input(tag):
    return tag.endswith(('input', 'group')) or tag in ('textline', 'textbox', 'filesubmission', 'schematic', 'crystallography')

def find_problems(db):
    problems = db.modulestore.find()
    problem_types = {}
    courses = defaultdict(lambda: defaultdict(int))

    for p in problems:
        if not isinstance(p['_id'], dict):
            continue

        course_id = '{org}/{course}'.format(**p['_id'])

        category = p['_id']['category']

        if category == 'problem':
            data = p['definition']['data']
            if not isinstance(data, six.text_type):
                if 'data' not in data:
                    continue
                data = data['data']

            try:
                tree = fromstring(data.encode('utf8'))
            except ParseError as e:
                sys.stderr.write('ERROR: cannot parse "{}": {}\n'.format(str(p), str(e)))
                continue

            for elt in tree.getiterator():
                if is_input(elt.tag):
                    courses[course_id]['capa.' + elt.tag] += 1
        else:
            courses[course_id][category] += 1

    totals = defaultdict(int)
    rows = []
    for coursename in sorted(courses):
        row = defaultdict(int)
        row['course_id'] = coursename
        problems = list(courses[coursename].items())
        # problems.sort(key=lambda x: x[1], reverse=True)
        for problem_type, count in problems:
            row[problem_type] = count
            totals[problem_type] += count
        rows.append(row)

    writer = csv.DictWriter(sys.stdout, ['course_id'] + list(sorted(totals.keys())))
    writer.writeheader()
    writer.writerows(rows)

    row = defaultdict(int)
    row['course_id'] = 'TOTAL'
    for problem_type, count in sorted(list(totals.items()), key=lambda x: x[1], reverse=True):
        row[problem_type] = count
    writer.writerow(row)


if __name__ == '__main__':
    import argparse
    import getpass
    parser = argparse.ArgumentParser()
    parser.usage = '''\n\t%s -H [mongo hostname] -u [mongo username] -p [mongo port] -d [db name]''' % sys.argv[0]
    parser.description = 'prints counts of xblock types per course'
    parser.add_argument('-H', '--host', help='mongo host name', default='localhost')
    parser.add_argument('-u', '--user', help='mongo username', default=None)
    parser.add_argument('-p', '--port', help='mongo port', default=27017, type=int)
    parser.add_argument('-d', '--db', help='mongo db', default='edxapp')

    args = parser.parse_args(sys.argv[1:])

    if args.user:
        password = getpass.getpass('MongoDB password: ')
        host = 'mongodb://{user}:{password}@{host}:{port}/{db}'.format(
                host=args.host, port=args.port, db=args.db, user=args.user, password=password
            )
    else:
        host = args.host
    conn = MongoClient(host, args.port)
    find_problems(getattr(conn, args.db))
