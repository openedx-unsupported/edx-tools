from xml.dom.minidom import *
data=[s.split('|') for s in open('video_list.txt').readlines()]
impl = getDOMImplementation()
doc = xml.dom.minidom.Document()
main=doc.createElement("course")
main.setAttribute("name", "6.002 Spring 2012")
doc.appendChild(main)

chapter=doc.createElement("chapter")
chapter.setAttribute("name", "Main")

main.appendChild(chapter)

for (youtube_id,name,time) in data:
    section=doc.createElement("section")
    section.setAttribute("time", time.strip())
    section.setAttribute("name", name.strip())
    section.setAttribute("due", "")
    vid=doc.createElement("video")
    vid.setAttribute("youtube", youtube_id.strip())
    vid.setAttribute("name", "Blackboard")

    #n=doc.createTextNode("Blackboard")
    #vid.appendChild(n)

    section.appendChild(vid)
    chapter.appendChild(section)

print doc.toprettyxml()
#f=open('video_list.xml','w')
#f.write(doc.toprettyxml())
#f.close()
