"""
Takes a .srt file and produces a new .srt file which renumbers the captions from one,
and restarts the timing from 0 (subtracting the first timestamp from all timestamps)

Args:
    the filename of the original .srt file

Returns:
    a new .srt file is written, with the old filename with 'chopped_' prepended 
    e.g. 'myvideo.srt' -> 'chopped_.srt'

"""
from __future__ import absolute_import
import sys
import re
from datetime import datetime, timedelta

if len(sys.argv) < 2:
    sys.exit('Usage: %s input-filename' % sys.argv[0])

count = 1 # we'll want to re-write the caption numbers starting from 1
srt_file = open(sys.argv[1])
out_filename = "chopped_"+sys.argv[1]
out_file = open(out_filename,'w')

state = 0 #at first we're at a new caption block
atStart = 1 #at first we're at the start of the file

def datify(timeString):
    '''
    take a string like '00:14:08' and return a datetime object with the date set to jan 1, 2000
    and the time set to the time corresponding to the string that was sent
    '''
    timeParts=re.split(':',timeString)
    myHours=int(timeParts[0])
    myMinutes=int(timeParts[1])
    mySeconds=int(timeParts[2])
    return (datetime(2000,1,1,myHours,myMinutes,mySeconds))

for row in srt_file:
 
    if (state==2):
        # this is a caption, not a caption number or a timestamp
        out_file.write(row)

    if (state==1):
        # this is a set of timestamps - we need to subtract the offset and write the new ones to the file
        
        times = re.split('-->',row)
        startTimeParts=re.split(',',times[0])
        endTimeParts=re.split(',',times[1])

        startTime = startTimeParts[0]
        endTime=endTimeParts[0]

        startMilli=startTimeParts[1]
        endMilli=endTimeParts[1]

        st=datify(startTime)

        if (atStart==1):
            # this is the first one in the file, so it's the offset
            offset = st
            atStart=0

        et = datify(endTime)

        st = str(st - offset)
        et = str(et - offset)

        out_file.write(st + "," + startMilli + "--> " + et + "," + endMilli)
        
        state +=1 # we're done with the timestamps, up next are the captions

    if (state==0):
        # this is the caption number - we need to rewrite these starting with 1

        out_file.write(str(count)+"\n")
        state +=1 # we're done w/ the caption number, next up is the timestamp

    if (row == "\n"):
        count +=1 #this will be the caption number for the next caption
        state = 0 #next up will be a new block, starting with a caption number
  



