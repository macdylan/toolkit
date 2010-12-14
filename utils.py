#!/usr/bin/env python

# General utilities. And also provide useful routines for other scripts.
#
# Author: Santa Zhang (santa1987@gmail.com)
#

import sys
import os
import time

def get_config(key, default_value=None):
  module_name = os.path.basename(sys.argv[0])
  if "." in module_name:
    module_name = os.path.splitext(module_name)[0]
  conf_fn = os.path.join(os.path.split(__file__)[0], "toolkit.conf")
  value = None
  
  if key.startswith(module_name):
    full_key = key
  else:
    full_key = module_name + "." + key
  
  f = None
  try:
    f = open(conf_fn)
    for line in f.readlines():
      line = line.strip()
      if line.startswith(";") or line.startswith("#") or line == "":
        continue
      idx = line.find("=")
      if idx < 0:
        continue
      if (line[:idx] == full_key + ".windows" and os.name == "nt") or (line[:idx] == full_key + ".posix" and os.name == "posix") or (line[:idx] == full_key) or (line[:idx] == key + ".windows" and os.name == "nt") or (line[:idx] == key + ".posix" and os.name == "posix") or (line[:idx] == key):
        value = line[(idx + 1):]
        break
  finally:
    if f != None:
      f.close()
  
  if default_value != None and value == None:
    value = default_value
  if value == None:
    raise Exception("Config '%s' not found!" % key)
  else:
    return value

def is_hex(text):
  text = text.lower()
  for c in text:
    if ('0' <= c and c <= '9') or ('a' <= c and c <= 'f'):
      continue
    else:
      return False
  return True

def is_ascii(text):
  for c in text:
    if ord(c) >= 128 or ord(c) < 0:
      return False
  return True
  
def is_image(fname):
  fname = fname.lower()
  for ext in [".jpg", ".png", ".gif", ".swf", ".bmp"]:
    if fname.endswith(ext):
      return True
  return False

def write_log(text):
  print text
  main_name = os.path.basename(sys.argv[0])
  if "." in main_name:
    main_name = os.path.splitext(main_name)[0]
  log_fn = os.path.join(os.path.split(__file__)[0], main_name + ".log")
  f = open(log_fn, "a")
  tm = time.strftime("%Y.%m.%d %H:%M:%S", time.localtime())
  f.write("[%s] %s\n" % (tm, text))
  f.close()

