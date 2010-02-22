# for windows only

import os
import sys
import time

if os.path.exists("../collections") == False:
  os.makedirs("../collections")

print """
usage:

This utility is used to generate hardlinks to danbooru-imsages, make them a collection.
The hard links are generated using "mklink /H" command.
You can safely delete the collection files, and the images in source folders will not be deleted.
You can append to an existing collection, by typing existing collection name as new collection name.
When you've done adding images, input an empty line or 'quit' or 'exit', then this script will automatically generate hard links.
Hard links will not increase disk usage, they are just multiple pointers to same piece of data.
"""

default_name = time.strftime("%Y%m%d", time.localtime())
name = raw_input("collection name[%s]: " % default_name)
if name == "":
  name = default_name

fname = "../collections/%s.txt" % name
print "collection file: %s" % fname

collection_f = None
if os.path.exists(fname):
  print "file already exists, appending to it"
  collection_f = open(fname, "a")
else:
  collection_f = open(fname, "w")

img_set = None
while True:
  print "current image set is", img_set
  input = raw_input("input image id or image set name: ")
  input = input.lower()
  if input == "" or input == "exit" or input == "quit":
    break
  elif input == "moe_imouto":
    img_set = "moe_imouto"
  elif input == "konachan":
    img_set = "konachan"
  elif input == "danbooru":
    img_set = "danbooru"
  elif input == "nekobooru":
    img_set = "nekobooru"
  elif img_set != None:
    id = int(input)
    line = "%s %d\n" % (img_set, id)
    print line
    collection_f.write(line)

collection_f.close()

# reopen the file, create junctions
collection_f = open(fname, "r")

dir_name = "../collections/%s" % name
if os.path.exists(dir_name) == False:
  os.makedirs(dir_name)

for line in collection_f.readlines():
 # try:
    line = line.strip()
    if line == "":
      continue
    splt = line.split()
    img_set = splt[0]
    id = int(splt[1])
    id_found = False
    bucket_size = 100
    bucket_id = id / bucket_size
    bucket_name = "%d-%d" % (bucket_id * bucket_size, bucket_id * bucket_size + bucket_size - 1)
    
    for ext in ("jpg", "gif", "png"):      
      sample_file_path = "../" + img_set + "/sample/" + bucket_name + "/" + str(id) + "." + ext
      if os.path.exists(sample_file_path):
        link_name = dir_name + "/" + img_set + " " + str(id) + "." + ext
        cmd = 'mklink "%s" "%s" /H' % (link_name, sample_file_path)
        print cmd
        os.system(cmd)
        id_found = True
        
    if id_found == False:
      print '"%s %d" not found' % (img_set, id)
      
  #except:
    #print "error processing line: %s" % line
      
collection_f.close()
