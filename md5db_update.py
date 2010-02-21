# update search database

import os
import pickle
import json

md5_table = {}

search_sources = []
f = open("search_sources", "r")
search_sources = map(str.strip, f.readlines())
f.close()

def update_md5table(arg, dirname, fnames):
  global md5_table
  img_set = os.path.split(arg)[1]
  print "updating md5 in folder %s" % dirname
  for fname in fnames:
    fpath = dirname + os.path.sep + fname
    if os.path.isfile(fpath) == False or fpath.endswith(".txt") == False:
      continue
    f = open(fpath, "r")
    info = json.loads(f.read())
    md5 = info[u"md5"]
    id = os.path.splitext(os.path.split(fpath)[1])[0]
    md5_table[md5] = "%s %s" % (img_set, id)
    f.close()

for source in search_sources:
  os.path.walk(source + "/info", update_md5table, source)

f = open("md5_db", "wb")
pickle.dump(md5_table, f)
f.close()
