#!/usr/bin/python

# used to check md5 sum of pictures downloaded from danbooru sites

import sys
import os
import hashlib
import json
import shutil

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
  print "[folder] %s" % dirname
  for fname in fnames:
    file_path = dirname + os.path.sep + fname
    file_path = file_path.lower()
    if file_path.endswith(".jpg") or file_path.endswith(".png"):
      id = int(fname.split(".")[0])
      m = hashlib.md5()
      f = open(file_path, "rb")
      m.update(f.read())
      f.close()
      d1 = m.hexdigest()
      d2 = get_md5sum_from_info(id, basefolder)
      if d1 == d2:
        print "[passed] %d" % id
      else:
        print "[broken] %d" % id
        broken_folder = basefolder + os.path.sep + "broken"
        os.makedirs(broken_folder)
        shutil.move(file_path, broken_folder + os.path.sep + fname)

def do_md5check(basefolder):
  original_folder = basefolder + os.path.sep + "original"
  os.path.walk(original_folder, original_folder_walker, basefolder)

if __name__ == "__main__":
  if len(sys.argv) == 1:
    print "usage: danbooru_md5check.py <basefolder>"
  else:
    do_md5check(sys.argv[1])
  