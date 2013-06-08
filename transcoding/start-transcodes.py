#!/usr/bin/env python

import boto.elastictranscoder 
import re

transcoder = boto.elastictranscoder.connect_to_region('us-west-1')

pipeline_id = "1370295917356-5w004x"
preset_id = "1351620000001-000060"   # 320x240 aka 240p

filelist = open("/Users/sef/medstats-videos.txt")
for f in filelist:
    in_key = f.strip()
    out_key = re.sub('VideoLarge', 'Video240p', in_key)

    params_in = { 'Key':    in_key,
        'FrameRate':        'auto',
        'Resolution':       'auto',
        'AspectRatio':      'auto',
        'Interlaced':       'auto',
        'Container':        'auto',
    }

    params_out =  { 'Key':  out_key,
        'ThumbnailPattern': '',
        'Rotate':           'auto',
        'PresetId':         preset_id,
    } 
    
    print "START pipeline =", pipeline_id
    print "      params_in =", params_in
    print "      params_out =", params_out

    revtal = transcoder.create_job(pipeline_id=pipeline_id,
            input_name=params_in, 
            output=params_out)

    print "SUBMITTED revtal =", revtal
    print "-------------------------------------------------------"

