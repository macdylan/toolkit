# search image on tags

import pickle
import os

if os.path.exists("../collections") == False:
  os.makedirs("../collections")

print "loading database"
f = open("search_db", "rb")
tag_table = pickle.load(f)
f.close()
print "database loaded"
print "%d tags inside database" % len(tag_table)

print "input empty line to quit"
print "queries will be automatically saved to 'collections' folder"

def do_search(tags):
  global tag_table
  result_set = None
  used_tags = []
  for tag in tags:
    if tag_table.has_key(tag) == False:
      print "warning: tag '%s' not found" % tag
    else:
      used_tags += tag,
      if result_set == None:
        result_set = tag_table[tag]
      else:
        result_set.intersection_update(tag_table[tag])
        if len(result_set) == 0:
          break
  
  if result_set == None:
    print "no result found"
  else:
    print "%d results found" % len(result_set)
    if len(result_set) != 0:
      search_name = "../collections/search " + (" ".join(used_tags)) + ".txt"
      print "result is automatically saved to %s" % search_name
      result_f = open(search_name, "w")
      for result in result_set:
        result_f.write(result + "\n")
      result_f.close()

while True:
  input = raw_input("query on tags: ")
  if input == "":
    break
  do_search(input.split())
