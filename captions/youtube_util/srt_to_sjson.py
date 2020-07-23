from __future__ import absolute_import
from __future__ import print_function
import six.moves.urllib.request, six.moves.urllib.error, six.moves.urllib.parse
from xml.etree import ElementTree
import sys, os, json, re, string
from six import unichr


def main():
    id=sys.argv[1]
    try:
        outfile=sys.argv[2]
    except:
        outfile= "subs_" + id+".sjson"
    
    subs_dict = srt_to_sjson(id)
    
    f=open(outfile, "w")
    f.write(json.dumps(subs_dict, indent=2))
    f.close()
    print("file written to "+outfile)
    

def parse_ms(srt_time_format):
    hour, min, sec = srt_time_format.split(":")
    sec, ms = sec.split(",")
    sec = int(hour)*3600 + int(min)*60 + int(sec)
    return sec*1000 + int(ms)
                    

def srt_to_sjson(srt_file, verbose=True):

    f=open(srt_file, "r")
    
    sub_starts = []
    sub_ends = []
    sub_texts = []
    
    try:
        
        while True:
            line = f.readline()
            if line =="":
                break
            if "-->" in line:
                start, end = line.split("-->")
                text = f.readline()
                if text:
                    #Start and end are an int representing the millisecond timestamp
                    sub_starts.append(parse_ms(start))
                    sub_ends.append(parse_ms(end))
                    sub_texts.append(unescape(text))
    except Exception as e:
        if verbose:
            print("error parsing subtitles from" + srt_file + ":" , e)
        pass #There probably wasn't any captions available
        
    subs_dict={'start':sub_starts,
               'end':sub_ends,
               'text':sub_texts}
    return subs_dict
    
def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)
        
from six.moves.html_entities import name2codepoint
# for some reason, python 2.5.2 doesn't have this one (apostrophe)
name2codepoint['#39'] = 39

def unescape(s):
    "unescape HTML code refs; c.f. http://wiki.python.org/moin/EscapingHtml"
    s = s.replace('\n', ' ')
    return re.sub('&(%s);' % '|'.join(name2codepoint),
              lambda m: unichr(name2codepoint[m.group(1)]), s)
    

if __name__ == "__main__":
    main()
