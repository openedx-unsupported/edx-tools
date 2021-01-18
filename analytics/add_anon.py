# take a collection and add anonymous id's to it
# invoke like this:
#     python add_anon.py forum/contents ep101-anon.csv -w \
#     -f '{"course_id":"HumanitiesSciences/EP101/Environmental_Physiology"}' 


from pymongo import MongoClient
from optparse import OptionParser
import csv
import json

DEFAULT_MATCH_FIELD="author_id"
DEFAULT_ANONID_FIELD="anon_id"

usage = """usage: %prog [options] db/coll anonid_file

Add anonymous ID's to a mongo collection on the local machine. Iterates
through all docs in a collection, optionally filtering, and adds a new
key into each doc.

Required parameters:
- \"db/coll\" the mongo database and collection to instrument.
- \"anonid_file\" the name of a file that has mapping from user_id to 
  anonymous_id.  Assumes csv in format id,anon, the edX format."""

parser = OptionParser(usage=usage)
parser.add_option("-w", dest="dry_run", action="store_false", default=True,
        help="write anon_ids into collection, default is to do a dry run")
parser.add_option("-m", dest="match_field", default=DEFAULT_MATCH_FIELD,
        help="field to match on (default=\"%s\")" % DEFAULT_MATCH_FIELD)
parser.add_option("-a", dest="anonid_field", default=DEFAULT_ANONID_FIELD,
        help="field to write anon_id into (default=\"%s\")" % DEFAULT_ANONID_FIELD)
parser.add_option("-f", dest="find_str", default=None,
        help="search clause, json string")
(options, args) = parser.parse_args()
if len(args) != 2:
    parser.error("expected two required options, got %d" % len(args))
(dbname, _, collection) = args[0].partition("/")
anonid_file = args[1]

# load anonymous mapping file
with open(anonid_file, "rb") as csvfile:
    anonid_reader = csv.reader(csvfile)
    anonid_map = {k:v for (k,v) in anonid_reader}

client = MongoClient()
db = client[dbname]
coll = db[collection]
if options.find_str:
    find_dict = json.loads(options.find_str)
    curs = coll.find(find_dict)
else:
    curs = coll.find()

match = 0
write = 0
error = 0
skip = 0
for rec in curs:
    recid = rec[options.match_field]
    if recid not in anonid_map:
        print("anonid not found for id=\"%s\"" % recid, file=sys.stderr)
        error += 1
        continue
    anonid = anonid_map[recid]
    match += 1
    if options.dry_run:
        continue
    if options.anonid_field in rec:
        if rec[options.anonid_field] != anonid:
            print("anonid collision for id=\"%s\"" % recid, file=sys.stderr)
            error += 1
        else:
            skip += 1
        continue
    rec[options.anonid_field] = anonid
    coll.save(rec)
    write += 1

print("match = %d, write = %d, skip = %d, error = %d" % 
        (match, write, skip, error))

