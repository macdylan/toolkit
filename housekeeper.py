# One script to manage my important collections.
#
# Author: Santa Zhang (santa1987@gmail.com)
#

import sys
import os
import re

from utils import *

def hk_read_crc32_dict(crc32_dict_fn):
  crc32_dict = {}
  if os.path.exists(crc32_dict_fn):
    f = open(crc32_dict_fn)
    for line in f.readlines():
      line = line.strip()
      if line.startswith(";") or line.startswith("#") or line == "":
        continue
      idx = line.find(" ")
      if idx < 0:
        continue
      crc32_dict[line[(idx + 1):]] = line[:idx]
    f.close()
  return crc32_dict

# if return None, then no info
# first try to get data from dict
# if not found, then get data from fname
def hk_try_get_crc32_info(fname, crc32_dict):
  if crc32_dict.has_key(fname):
    return crc32_dict[fname]
  splt = re.split("\[|\]|\(|\)|_", fname)
  for sp in splt:
    if len(sp) == 8 and is_hex(sp):
      return sp
  return None

def hk_calc_crc32_from_file(crc32_bin, fpath):
  crc = None
  cmd = "%s \"%s\"" % (crc32_bin, fpath)
  pipe = os.popen(cmd)
  crc = pipe.readlines()[0].split()[0]
  pipe.close()
  if crc == None:
    raise Exception("Failed to calc crc32 for '%s'! Binary is '%s'." % (fpath, crc32_bin))
  return crc

def hk_check_crc32_walker(crc32_bin, folder, files):
  write_log("[dir] %s" % folder)
  crc32_dict_fn = folder + os.path.sep + "housekeeper.crc32"
  crc32_dict = hk_read_crc32_dict(crc32_dict_fn)
  if os.path.exists(crc32_dict_fn):
    write_log("[dict] %s" % crc32_dict_fn)
    
  for fn in files:
    if fn.startswith("housekeeper."):
      # ignore housekeeper's data
      continue
    fpath = folder + os.path.sep + fn
    if os.path.isdir(fpath):
      continue
    crc32_info = hk_try_get_crc32_info(fn, crc32_dict)
    if crc32_info == None:
      write_log("[ignore] %s" % fpath)
    else:
      calc_crc32 = hk_calc_crc32_from_file(crc32_bin, fpath)
      if calc_crc32 == crc32_info:
        write_log("[pass] %s" % fpath)
      else:
        write_log("[failure] %s" % fpath)
      

def hk_check_crc32():
  crc32_bin = get_config("crc32_bin")
  root_dir = raw_input("The root directory to start with? ")
  os.path.walk(root_dir, hk_check_crc32_walker, crc32_bin)


def hk_check_ascii_fnames_walker(arg, folder, files):
  write_log("[dir] %s" % folder)
  for fn in files:
    fpath = folder + os.path.sep + fn
    if is_ascii(fpath):
      write_log("[pass] %s" % fpath)
    else:
      write_log("[failure] %s" % fpath)
    

def hk_check_ascii_fnames():
  root_dir = raw_input("The root directory to start with? ")
  os.path.walk(root_dir, hk_check_ascii_fnames_walker, None)

def hk_help():
  print "housekeeper.py helper script to manage my important collections"
  print "usage: housekeeper.py <command>"
  print "available commands:"
  print
  print "  check-crc32          check file integrity by crc32"
  print "  check-ascii-fnames   make sure all file has ascii-only name"
  print
  print "author: Santa Zhang (santa1987@gmail.com)"

if __name__ == "__main__":
  if len(sys.argv) == 1 or sys.argv[1] == "help":
    hk_help()
  elif sys.argv[1] == "check-crc32":
    hk_check_crc32()
  elif sys.argv[1] == "check-ascii-fnames":
    hk_check_ascii_fnames()
  else:
    print "command '%s' not understood, see 'housekeeper help' for more info" % sys.argv[1]
