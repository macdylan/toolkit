#!/usr/bin/python
#
# This script is used to generate iPhone ringtone from iTunes m4a files.
# Usage: ./make_iphone_ringtone.py <path_containing_m4a_files>
# Author:: Santa Zhang (santa1987@gmail.com)

print """
This script is used to generate iPhone ringtone from iTunes m4a files.
Usage: ./make_iphone_ringtone.py <path_containing_m4a_files>
Author:: Santa Zhang (santa1987@gmail.com)
"""

import os
import sys

def like_track_no(str):
  for c in str:
    if c.isdigit() or c == "-":
      continue
    else:
      return False
  return True

def main_fname(f):
  idx = f.rfind(".")
  if idx >= 0:
    f = f[:idx]
  return f

def smart_strip(f):
  sp = f.split()
  if like_track_no(sp[0]):
    f = f[len(sp[0]):].strip()
  f = main_fname(f)
  return f

def my_exec(cmd):
  print "[cmd] %s" % cmd
  os.system(cmd)

if len(sys.argv) != 1:
  m4a_folder = sys.argv[1]
  os.chdir(m4a_folder)
  for f in os.listdir("."):
    if f.endswith(".m4a"):
      ringtone_f = smart_strip(f) + ".m4r"
      print "%s ==> %s" % (f, ringtone_f)
      tmp_f = smart_strip(f) + ".m4a"
      my_exec("ffmpeg -y -i \"%s\" -t 30 -ac 2 -ar 44100 -ab 320 -acodec libfaac \"%s\"" % (f, tmp_f))
      my_exec("mv \"%s\" \"%s\"" % (tmp_f, ringtone_f))


