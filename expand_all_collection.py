# for windows only

import os
import sys
import time

if os.path.exists("../collections") == False:
  os.makedirs("../collections")

for entry in os.listdir("../collections"):
  entry_path = "../collections/" + entry
  if os.path.isfile(entry_path) == False or entry_path.endswith(".txt") == False:
    continue
  
  fname = entry_path
  name = os.path.splitext(os.path.split(fname)[1])[0]
  
  # open file, create junctions
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
