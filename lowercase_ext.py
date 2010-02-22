import os
import random

path = raw_input("Path(including subdirs) [.]?\n")
if path == "":
  path = "."

def lowercase_ext(arg, dirname, fnames):
  for f in fnames:
    spltname = os.path.splitext(f)
    if spltname[1] != spltname[1].lower():
      tmpname = "%s_tmp_%d" % (f, random.randint(0, 10000))
      os.rename(dirname + os.path.sep + f, dirname + os.path.sep + tmpname)
      newname = spltname[0] + spltname[1].lower()
      os.rename(dirname + os.path.sep + tmpname, dirname + os.path.sep + newname)
      print "lowerfy: %s  ->  %s" % (f, newname)

os.path.walk(path, lowercase_ext, None)
