#!/usr/bin/env python

import sys
import boto

if len(sys.argv) == 3:
    bucket_name = sys.argv[1]
    search = sys.argv[2]
else:
    print "usage", sys.argv[0], "bucket path"
    print "    example:", sys.argv[0], "prod-edx SciWrite/VideoLarge/"
    sys.exit(1)

conn = boto.connect_s3()
bucket = conn.get_bucket(bucket_name)

for k in bucket.list(prefix=search):
    if k.name == search:
        # don't fiddle with the "directory" itself, just its contents
        continue

    print k
    metadata = {'Content-Type': 'video/mp4',
            'Content-Disposition': 'attachment',
            }

    # trick: copy a key to itself can change metadata
    k = k.copy(k.bucket.name, k.name, metadata, preserve_acl=True)

