#!/usr/bin/env python

# General utilities. And also provide useful routines for other scripts.
#
# Author: Santa Zhang (santa1987@gmail.com)
#

from __future__ import with_statement
from contextlib import closing
import sys
import os
import time
import random
import traceback
import re
from zipfile import ZipFile, ZIP_DEFLATED

def root_required():
  if os.getuid() != 0:
    raise Exception("root required! please run with 'sudo'!")

def is_well_formed_uuid(uuid):
  uuid = uuid.lower()
  if re.match("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", uuid) == None:
    return False
  return True

def zipdir(basedir, archivename):
  ok = True
  assert os.path.isdir(basedir)
  with closing(ZipFile(archivename, "w", ZIP_DEFLATED)) as z:
    for root, dirs, files in os.walk(basedir):
      #NOTE: ignore empty directories
      for fn in files:
        # ignore useless files
        if fn.lower() == ".ds_store" or fn.lower() == "thumbs.db":
          print "exclude useless file '%s' from zip file" % fn
          continue
        try:
          absfn = os.path.join(root, fn)
          zfn = absfn[len(basedir)+len(os.sep):] #XXX: relative path
          z.write(absfn, zfn)
        except Exception as e:
          ok = False
          raise e # re-throw
  return ok

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
  for ext in [".jpg", ".png", ".gif", ".swf", ".bmp", ".pgm"]:
    if fname.endswith(ext):
      return True
  return False

def is_movie(fname):
  fname = fname.lower()
  for ext in [".avi", ".mp4", ".wmv", ".mkv", ".rmvb", ".rm"]:
    if fname.endswith(ext):
      return True
  return False

def is_music(fname):
  fname = fname.lower()
  for ext in [".mp3", ".m4a", ".ape", ".flac", ".tta", ".wav"]:
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

def random_token(size=5):
  token = ""
  alphabet = "abcdefghijklmnopqrst0123456789"
  for i in range(size):
    token += alphabet[random.randint(0, len(alphabet) - 1)]
  return token

