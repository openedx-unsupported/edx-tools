from __future__ import absolute_import
from __future__ import print_function
import gdata.youtube
import gdata.youtube.service

from lxml.etree import Element
from lxml import etree
import hashlib
from six.moves import range

def fasthash(string):
    m = hashlib.new("md4")
    m.update(string)
    return m.hexdigest()

def duration_tag(course):
    ''' Tag all videos with durations '''
    yt_service = gdata.youtube.service.YouTubeService()

    videos = course.xpath('//video')

    # Tag videos with durations
    for v in videos: 
        id_dict = dict([l.split(':') for l in v.get('youtube').split(',')])
        youtube = id_dict[[i for i in id_dict if float(i)==1][0]]
        print(youtube)
        entry = yt_service.GetYouTubeVideoEntry(video_id=youtube)
        lecture_duration = entry.media.duration.seconds
        lecture_desc = entry.media.description.text
        if not v.get('duration'):
            v.set("duration", lecture_duration)    
        if not v.get('name'):
            if type(lecture_desc) == str:
                v.set("title", lecture_desc)    
            else:
                v.set("title", "Unavailable")

def update_subs(course):
    ''' Tag all videos with durations '''
    videos = course.xpath('//video')

    # Tag videos with durations
    for v in videos: 
        id_dict = dict([l.split(':') for l in v.get('youtube').split(',')])
        youtube = id_dict[[i for i in id_dict if float(i)==1][0]]
        #if not v.get('duration'):
        #    v.set("duration", "0")    


default_ids = {'video':'youtube',
                 'problem':'filename',
                 'sequential':'id',
                 'html':'filename',
                 'verical':'id', 
                 'tab':'id',
                 'schematic':'id'}

def id_tag(course):
    ''' Tag all course elements with unique IDs '''
   # Tag elements with unique IDs
    elements = course.xpath("|".join(['//'+c for c in default_ids]))
    for elem in elements:
        if elem.get('id'):
            pass
        elif elem.get(default_ids[elem.tag]):
            elem.set('id', elem.get(default_ids[elem.tag]))
        else:
            elem.set('id', fasthash(etree.tostring(elem)))

student_groups = {'lab_3' : 'original',
                  'problem_2' : 'original'}

def ab_filter(course):
    elements = course.xpath("//select")
    for elem in elements: 
        if student_groups[elem.get('filter')]!=elem.get('tag'):
            elem.getparent().remove(elem)
        else:
            pass

def parent_drop():
    pass

for i in range(1):
    course=etree.XML(open('course.xml').read())

    duration_tag(course)
    #id_tag(course)
    #ab_filter(course)
 
print(etree.tostring(course))
