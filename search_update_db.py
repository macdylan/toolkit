# update search database

import os
import pickle

tag_table = {}

search_sources = []
f = open("search_sources", "r")
search_sources = map(str.strip, f.readlines())
f.close()

def update_tags(arg, dirname, fnames):
  global tag_table
  print "updating tags in folder %s" % dirname
  img_set = os.path.split(arg)[1]
  for fname in fnames:
    fpath = dirname + os.path.sep + fname
    if os.path.isfile(fpath) == False or fpath.endswith(".txt") == False:
      continue
    f = open(fpath, "r")
    tags = map(str.strip, f.readlines())
    tags += img_set,
    id = os.path.splitext(os.path.split(fpath)[1])[0]
    img_id = "%s %s" % (img_set, id)
    for tag in tags:
      if tag_table.has_key(tag) == False:
        tag_table[tag] = set()
      tag_table[tag].add(img_id)
    f.close()

for source in search_sources:
  os.path.walk(source + "/tags", update_tags, source)

f = open("search_db", "wb")
pickle.dump(tag_table, f)
f.close()
