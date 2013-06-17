#!/usr/bin/env python
import os

infile = open('subsscrapelist.txt', 'r')

#for id in infile:
for id in infile.readlines():
    id = id[:-1] #trim off newline
    if id:
        os.system("python get_json_subs.py "+id);
