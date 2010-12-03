#!/usr/bin/env python

# Convertion tools for video, picture, text.
#
# Author: Santa Zhang (santa1987@gmail.com)
#

import sys
import os
import time
import shutil
from utils import *

def jc_dos2unix_print_help():
  print "convert dos text file to unix text file"
  print "usage: justconvert.py dos2unix <textfile>"

def jc_dos2unix():
  if len(sys.argv) <= 2:
    jc_dos2unix_print_help()
  else:
    fname = sys.argv[2]
    if os.path.exists(fname) == False:
      print "[error] cannot find file '%s'!" % fname
      exit()
    bak_fname = fname + ".bak"
    if os.path.exists(bak_fname):
      i = 1
      while os.path.exists(bak_fname):
        bak_fname =  fname + (".bak.%d" % i)
        i += 1
    print "backup file is '%s'" % bak_fname
    shutil.move(fname, bak_fname)
    if os.path.exists(bak_fname) == False:
      print "[error] failed to create backup file '%s'!" % bak_fname
      exit()
    fin = open(bak_fname)
    fout = open(fname, "w")
    for line in fin.readlines():
      line = line.splitlines()[0]
      fout.write(line + "\n")
    fin.close()
    fout.close()
    print "done converting '%s'" % fname



def jc_print_help():
  print "justconvert.py: convertion tools for video, picture & text files"
  print "usage: justconvert.py <command>"
  print
  print "  dos2unix     convert dos text file to unix text file"
  print "  help         display this info"
  print
  print "author: Santa Zhang (santa1987@gmail.com)"


if __name__ == "__main__":
  if len(sys.argv) == 1 or sys.argv[1] == "help":
    jc_print_help()
  elif sys.argv[1] == "dos2unix":
    jc_dos2unix()
  else:
    print "command '%s' not understood, see 'justconvert.py help' for more info" % sys.argv[1]

