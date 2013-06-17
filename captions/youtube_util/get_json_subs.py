import urllib2
from xml.etree import ElementTree
import sys
import os
import json
import re

def main():
    id=sys.argv[1]
    try:
        outfile=sys.argv[2]
    except:
        outfile= "subs/" + id+".srt.sjson"
    
    subs_dict = get_json_subs(id)
    
    ensure_dir(outfile)
    f=open(outfile, "w")
    f.write(json.dumps(subs_dict, indent=2))
    f.close()
    

def get_json_subs(video_id, verbose=True):
    response = urllib2.urlopen('http://video.google.com/timedtext?lang=en&v=' + video_id)
    xmlString = response.read()
    
    sub_starts = []
    sub_ends = []
    sub_texts = []
    
    try:
        tree = ElementTree.fromstring(xmlString)
        
        for element in tree.iter():
            if element.tag == "text":
                start = float(element.get("start"))
                duration = float(element.get("dur"))
                text = element.text
                
                end = start + duration
                                
                if text:
                    #Start and end are an int representing the millisecond timestamp
                    sub_starts.append( int(start*1000) )
                    sub_ends.append(int((end + 0.0001)* 1000))
                    sub_texts.append(unescape(text))
    except Exception as e:
        if verbose:
            print "error parsing subtitles from youtube id " + video_id + ":" , e
        pass #There probably wasn't any captions available
            
    subs_dict={'start':sub_starts,
               'end':sub_ends,
               'text':sub_texts}
        
    return subs_dict
    
def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)
        
from htmlentitydefs import name2codepoint
# for some reason, python 2.5.2 doesn't have this one (apostrophe)
name2codepoint['#39'] = 39

def unescape(s):
    "unescape HTML code refs; c.f. http://wiki.python.org/moin/EscapingHtml"
    s = s.replace('\n', ' ')
    return re.sub('&(%s);' % '|'.join(name2codepoint),
              lambda m: unichr(name2codepoint[m.group(1)]), s)
    

if __name__ == "__main__":
    main()
