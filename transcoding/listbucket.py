#!/usr/bin/env python

import boto
import sys

if len(sys.argv) != 3:
    print("usage: %s <bucket> <path>" % sys.argv[0])
    print("\tYou probably want the path to include the trailing slash")
    print()
    print("\texample: %s prod-edx MathLearning/VideoLarge/" % sys.argv[0])
    sys.exit(1)

conn = boto.connect_s3()
bucket = conn.get_bucket(sys.argv[1])

search = sys.argv[2]

for k in bucket.list(prefix=search):
    if k.name == search:
        continue
    print(k.name[len(search):])

