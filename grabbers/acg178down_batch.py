# call acg178down.py in a batch

import sys
import os

def my_exec(cmd):
  print "[cmd] %s" % cmd
  os.system(cmd)

if len(sys.argv) == 1:
  print "usage: acg178down_batch.py url_list_file"
else:
  list_f = open(sys.argv[1], "r")

  for l in list_f.readlines():
    l = l.strip()
    if len(l) == 0:
      continue
    my_exec("acg178down.py %s" % l)

  list_f.close()
