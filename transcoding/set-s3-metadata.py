#!/usr/bin/env python

import boto

conn = boto.connect_s3()
bucket = conn.get_bucket('prod-edx')

search = 'MathLearning/VideoLarge/'

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

