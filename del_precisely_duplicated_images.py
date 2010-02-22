import os
import shutil

record_f = open("duplicate_precise.txt", "r")
duplicate_list = []

a_set = None
for line in record_f.readlines():
  line = line.strip()
  if line == "":
    if a_set != None:
      duplicate_list += a_set,
      a_set = None
  elif line == "duplicate:":
    a_set = set()
  else:
    a_set.add(line)

print "There are %d duplicating records" % len(duplicate_list)

def pretty_size(s):
  if s < 1024:
    return str(s)
  elif s < 1024 * 1024:
    return "%0.2f KB" % (s / 1024.)
  elif s < 1024 * 1024 * 1024:
    return "%0.2f MB" % (s / 1024. / 1024.)
  elif s < 1024 * 1024 * 1024 * 1024:
    return "%0.2f GB" % (s / 1024. / 1024. / 1024.)

saved_bytes = 0

real_duplist = []

print "checking existance of every file"
for s in duplicate_list:
  real_s = set()  # real set, checked existence
  a_file = None
  for f in s:
    if os.path.exists(f):
      real_s.add(f)
      if a_file == None:
        a_file = f
  if a_file != None:
    saved_bytes += (len(real_s) - 1) * os.lstat(a_file).st_size
  real_duplist += real_s,

print "checked, has %d existing duplicated images" % len(real_duplist)

def my_exec(cmd):
  print "[cmd] %s" % cmd
  os.system(cmd)

print "you can save %s if they are merged" % pretty_size(saved_bytes)
print "merged files will be moved to the image source's tmp folder"
choice = raw_input("really merge? [y/N]")
if choice == "y":
  for dup_set in real_duplist:
    primary = dup_set.pop()
    for dup_file in dup_set:
      print "[del] %s" % dup_file
      os.remove(dup_file)
      print "[hardlink] %s -> %s" % (dup_file, primary)
      my_exec('mklink "%s" "%s" /H' % (dup_file, primary))
    
  