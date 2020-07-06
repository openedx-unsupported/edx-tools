#!/usr/bin/env python

from __future__ import absolute_import
import csv
import json
import sys

from collections import defaultdict

FIELDNAMES = ['student_id', 'module_id', 'grade', 'max_grade', 'answers']


def process_answers(inputs, answers):
    result = list()

    for key in inputs:
        ans = answers.get(key, [])

        if not ans:
            ans = []
        elif type(ans) is not list:
            ans = [ans]

        result.append([a.encode('utf-8') for a in ans])

    return result


def process_row(row):
    try:
        state = row['state'].replace('\\\\', '\\')  # fix some incorrect json encodings
        state = json.loads(state)
    except ValueError:
        state = {}

    # the list of inputs is either in the correct_map or the input_state fields
    inputs = sorted(state.get('correct_map', {}).keys())
    if not inputs:
        inputs = sorted(state.get('input_state', {}).keys())

    answers = state.get('student_answers', {})
    row['answers'] = process_answers(inputs, answers)

    return row


def process_file(csvfile, writer):
    reader = csv.DictReader(csvfile, delimiter='\t')

    for row in reader:
        row = process_row(row)
        writer.writerow(row)


def run():
    filename = sys.argv[1]

    writer = csv.DictWriter(sys.stdout, delimiter='\t', fieldnames=FIELDNAMES, extrasaction='ignore')
    writer.writeheader()

    with open(filename, 'rb') as csvfile:
        process_file(csvfile, writer)


if __name__ == '__main__':
    run()
