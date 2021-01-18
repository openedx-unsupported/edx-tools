import gdata.youtube
import gdata.youtube.service

import sys

id=sys.argv[1]

yt_service = gdata.youtube.service.YouTubeService()
entry = yt_service.GetYouTubeVideoEntry(video_id=id)

lecture_number = entry.media.title.text.split('|')[0]
lecture_desc = entry.media.description.text.split('\n')[0]
lecture_duration = entry.media.duration.seconds
 
print(id, "|", lecture_desc,"|", lecture_duration)
