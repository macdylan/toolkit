#!/usr/bin/python

# script to fetch images

import shutil
import os

base_folder = None
source_name = None

print "input base folder name: (danbooru|konachan|moe_imouto|nekobooru)"
print "after that, input image id like '103002' or '104848-104866'"
print "input nothing if you wanna quit"

def try_copy(image_path, id, ext):
  global source_name
  if os.path.exists(image_path):
    new_name = source_name + " " + str(id) + "." + ext
    print image_path + "  -->  ../" + new_name
    shutil.copy(image_path, "../%s" % new_name)
    return True
  return False

def do_fetch(id):
  global base_folder
  bucket_size = 100
  bucket_id = id / bucket_size
  bucket = "%d-%d" % (bucket_id * bucket_size, bucket_id * bucket_size + bucket_size - 1)
  try_jpg = try_copy(base_folder + "/sample/" + bucket + "/" + str(id) + ".jpg", id, "jpg")
  try_png = try_copy(base_folder + "/sample/" + bucket + "/" + str(id) + ".png", id, "png")
  try_gif = try_copy(base_folder + "/sample/" + bucket + "/" + str(id) + ".gif", id, "gif")
  if try_jpg == False and try_png == False and try_gif == False:
    print "%d not found in %s" % (id, base_folder)
  
while True:
  input = raw_input()
  input = input.lower()
  if input == "danbooru":
    source_name = input
    base_folder = "../danbooru"
  elif input == "konachan":
    source_name = input
    base_folder = "../konachan"
  elif input == "moe_imouto":
    source_name = input
    base_folder = "../moe_imouto"
  elif input == "nekobooru":
    source_name = input
    base_folder = "../nekobooru"
  elif input == "mypic":
    source_name = input
    base_folder = "../mypic"
  elif input == "" or input == "exit" or input == "quit":
    break
  else:
    if "-" in input:
      splt = input.split('-')
      start_id = int(splt[0])
      end_id = int(splt[1])
      print "fetch %d to %d from %s" % (start_id, end_id, base_folder)
      for i in range(start_id, end_id + 1):
        do_fetch(i)
    else:
      do_fetch(int(input))
