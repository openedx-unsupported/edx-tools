from __future__ import absolute_import
from __future__ import print_function
from xml.dom.minidom import parse, parseString
import json

dom=parse('course.xml')

course = dom.getElementsByTagName('course')[0]
name=course.getAttribute("name")
chapters = course.getElementsByTagName('chapter')
ch=list()
for c in chapters:
    sections=list()
    for s in c.getElementsByTagName('section'):
        sections.append({'name':s.getAttribute("name"), 
                         'time':s.getAttribute("time"), 
                         'format':s.getAttribute("format"), 
                         'due':s.getAttribute("due")})
    ch.append({'name':c.getAttribute("name"), 
              'sections':sections})

print(json.dumps(ch, indent=2))
