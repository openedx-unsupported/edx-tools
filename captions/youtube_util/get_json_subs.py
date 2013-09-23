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
        outfile= "subs/" + "subs_" + id + ".srt.sjson"
    
    subs_dict = get_json_subs(id)
    
    ensure_dir(outfile)
    f=open(outfile, "w")
    f.write(json.dumps(subs_dict, indent=2))
    f.close()
    



def get_json_subs(video_id, verbose=True):
    url = 'http://video.google.com/timedtext?lang=en&v=' + video_id
    response = urllib2.urlopen(url)
    xmlString = response.read()
    
    if not xmlString:
        # Try the hack fallback url in a pinch -- solved particular cases in prod:
        # http://video.google.com/timedtext?hl=en&ts=&type=track&name=Captions&lang=en&v=XXXX
        # Docs for doing this more properly at: http://nettech.wikia.com/wiki/YouTube
        url = 'http://video.google.com/timedtext?hl=en&ts=&type=track&name=Captions&lang=en&v=' + video_id
        print "Trying fallback:", url,
        response = urllib2.urlopen(url)
        xmlString = response.read()
        if xmlString: print "... got data"
        else: print "... nope"
    
    sub_starts = []
    sub_ends = []
    sub_texts = []
    
    try:
        tree = ElementTree.fromstring(xmlString)
        
        for element in tree.iter():
            if element.tag == "text":
                start = float(element.get("start"))
                # hack: in practice, sometimes "dur" was missing
                try:
                    duration = float(element.get("dur"))
                except:
                    duration = 0.5
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
