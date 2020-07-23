#!/usr/bin/env python
#
# This relies on a pretty current boto, as elastictranscoder support 
# was just added.  I use v.2.9.5.
# 
# Assumes that you have credentials to access AWS via boto, see:
# http://boto.readthedocs.org/en/latest/boto_config_tut.html
#
# Doesn't explicity rely on the aws command line tools, but they are 
# referenceed here, get them at http://aws.amazon.com/cli/

from __future__ import absolute_import
from __future__ import print_function
import boto.elastictranscoder 
import re

# 
# SETTINGS
#
# Pipeline -- use this command to get the show the pipelines, use the ID:
#     aws elastictranscoder list-pipelines
pipeline_id = "1370295917356-5w004x"

# Output Format
# Uncomment the one you want.  There are others available or you can create 
# your own, get the ID from this command:
#     aws elastictanscoder list-presets
# preset_id = "1351620000001-000001"   # Generic 1080p
# preset_id = "1351620000001-000010"   # Generic 720p
# preset_id = "1351620000001-000020"   # Generic 480p 16:9
# preset_id = "1351620000001-000030"   # Generic 480p 4:3
# preset_id = "1351620000001-000040"   # Generic 360p 16:9
# preset_id = "1351620000001-000050"   # Generic 360p 16:9
preset_id = "1351620000001-000060"   # Generic 320x240

# Region
reg='us-west-1'

# List of videos to encode
# can be an explicit list with entries that look like this (case sensitive, 
# no leading slash):
#      MedStats/VideoLarge/Unit 8 Module 5.mp4
# This is the old-style command (older version of the aws tools):
#      aws s3 list-objects --bucket=prod-edx --output=text --prefix="MedStats/VideoLarge" | cut -f4 | grep -v ^$
# The new AWS CLI looks like this:
#      aws s3 ls s3://prod-edx/SciWrite/VideoLarge/ | awk '{print "SciWrite/VideoLarge/"$4}' | grep -i 'mp4$'
filelist = open("/Users/sef/Desktop/SciWrite/sciwrite-videos-all.txt")

# Path Substitution
# Folder to rename from to rename to
from_dir = 'VideoLarge'
to_dir = 'Video240p'


#
# ACTUALLY DO THE TRANSCODES
# 

transcoder = boto.elastictranscoder.connect_to_region(reg)

for f in filelist:
    in_key = f.strip()
    out_key = re.sub(from_dir, to_dir, in_key)

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
    
    print("START pipeline =", pipeline_id)
    print("      params_in =", params_in)
    print("      params_out =", params_out)

    revtal = transcoder.create_job(pipeline_id=pipeline_id,
            input_name=params_in, 
            output=params_out)

    print("SUBMITTED revtal =", revtal)
    print("-------------------------------------------------------")

