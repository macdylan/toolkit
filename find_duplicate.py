#!/usr/bin/python

# check duplicate using md5 sum

import sys
import os
import json
import shutil

md5_table = {}

def get_md5sum_from_info(id, basefolder):
  bucket_size = 100
  bucket_id = id / bucket_size
  bucket_name = "%d-%d" % (bucket_id * bucket_size, bucket_id * bucket_size + bucket_size - 1)
  info_path = basefolder + os.path.sep + "info" + os.path.sep + bucket_name + os.path.sep + str(id) + ".txt"
  f = open(info_path)
  info = json.loads(f.read())
  f.close()
  return info[u"md5"]
  
def original_folder_walker(basefolder, dirname, fnames):
  global md5_table
  print "[folder] %s" % dirname
  for fname in fnames:
    file_path = dirname + os.path.sep + fname
    file_path = file_path.lower()
    if file_path.endswith(".jpg") or file_path.endswith(".png"):
      id = int(fname.split(".")[0])
      md5 = get_md5sum_from_info(id, basefolder)
      if md5_table.has_key(md5) == False:
        md5_table[md5] = [id]
      else:
        md5_table[md5] += id,
        print "dup!", md5_table[md5]
      

def do_md5check(basefolder):
  original_folder = basefolder + os.path.sep + "original"
  os.path.walk(original_folder, original_folder_walker, basefolder)

if __name__ == "__main__":
  if len(sys.argv) == 1:
    print "usage: danbooru_md5check.py <basefolder>"
  else:
    do_md5check(sys.argv[1])
  