#!/usr/bin/python

# This script works on MacOS, only for personal use!
# Santa Zhang (santa1987@gmail.com)

import os

def is_pic(fn):
  fn = fn.lower()
  if fn.endswith(".gif") or fn.endswith(".png") or fn.endswith(".jpg"):
    return True
  return False

def my_exec(cmd):
  print "[cmd] %s" % cmd
  os.system(cmd)

def do_sync_from_to(from_dir, to_dir):
  print "Sync %s => %s" % (from_dir, to_dir)
  from_dir_ls = os.listdir(from_dir)
  to_dir_ls = os.listdir(to_dir)
  for to_f in to_dir_ls:
    if not is_pic(to_f):
      continue
    if to_f not in from_dir_ls:
      print "[del] %s" % to_f
      my_exec("rm \"%s/%s\"" % (to_dir, to_f))
  for from_f in from_dir_ls:
    if not is_pic(from_f):
      continue
    if from_f not in to_dir_ls:
      print "[add] %s" % from_f
      my_exec("convert \"%s/%s\" -size 1280x800 \"%s/%s\"" % (from_dir, from_f, to_dir, from_f))

pc_base = "/Users/santa/Dropbox/Photos/"
psp_base = "/Volumes/NO NAME/Picture/"

do_sync_from_to(pc_base + "Other Photos", psp_base + "Other Photos")
do_sync_from_to(pc_base + "ACG Cellphone", psp_base + "ACG Cellphone")
do_sync_from_to(pc_base + "ACG Wallpaper", psp_base + "ACG Wallpaper")

