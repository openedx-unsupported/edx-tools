#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function
from collections import deque
import json
from pprint import pprint
import sys
import six


def load_nodes():
    filename = sys.argv[1]

    with open(filename) as f:
        nodes = json.load(f)

    return add_parents_and_children(nodes)


def add_parents_and_children(nodes):
    for k in nodes.keys():
        node = nodes[k]
        node['parent'] = node.get('parent')
        for child in node.get('children', []):
            if child not in nodes:
                nodes[child] = {}
            nodes[child]['parent'] = k

    return nodes


def get_root(nodes):
    root = six.iterkeys(nodes)

    while nodes[root].get('parent'):
        root = nodes[root]['parent']

    return root


def traverse(nodes, root, func):
    queue = deque([root])
    while queue:
        key = queue.popleft()
        children = nodes[key].get('children', [])
        queue.extend(children)
        func(nodes, key)


def print_problem(nodes, key):
    node = nodes[key]
    display_name = node.get('metadata', {}).get('display_name')
    category = node.get('category')

    if category == 'problem':
        display_name = display_name if display_name else 'blank'
        print(u'{0} "" {1}'.format(key, display_name).encode('utf-8'))


def run():
    nodes = load_nodes()
    root = get_root(nodes)
    traverse(nodes, root, print_problem)


if __name__ == '__main__':
    run()
