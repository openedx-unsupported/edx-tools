#!/usr/bin/env python
from __future__ import absolute_import
import os

infile = open('subsscrapelist.txt', 'r')

for id in infile.readlines():
    # trim off # comments
    if id.find('#') != -1:
        id = id[:id.find('#')]
    # newline cleanup
    id = id.strip()
    if id:
        os.system("python get_json_subs.py " + id);
