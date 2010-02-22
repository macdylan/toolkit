import hashlib
import os

def md5_on_file(fpath):
  m = hashlib.md5()
  pic_f = open(fpath, "rb")
  m.update(pic_f.read())
  pic_f.close()
  return m.hexdigest()

md5_table = {}

search_sources = []
f = open("search_sources", "r")
search_sources = map(str.strip, f.readlines())
f.close()

def is_image(fpath):
  fpath = fpath.lower()
  return (fpath.endswith(".jpg") or fpath.endswith(".png") or fpath.endswith(".gif")) and os.path.isfile(fpath)

def md5_walker(arg, dirname, fnames):
  global md5_table
  print "collecting md5 in dir %s" % dirname
  for f in fnames:
    fpath = dirname + "/" + f
    if is_image(fpath) == False:
      continue
    md5value = md5_on_file(fpath)
    if md5_table.has_key(md5value) == False:
      md5_table[md5value] = set()
    md5_table[md5value].add(fpath)
    if len(md5_table[md5value]) > 1:
      print "[dup]", md5_table[md5value]

for source in search_sources:
  for type in ["jpeg", "original", "sample"]:
    if os.path.exists(source + "/" + type):
      os.path.walk(source + "/" + type, md5_walker, None)

duplicate_file = open("duplicate_precise.txt", "a")
save_bytes = 0
for k in md5_table.keys():
  if len(md5_table[k]) > 1:
    print "duplicate:"
    duplicate_file.write("duplicate:\n")
    a_file = None
    for f in md5_table[k]:
      if a_file == None:
        a_file = f
      print f
      duplicate_file.write(f + "\n")
    duplicate_file.write("\n\n")
    save_bytes += (len(md5_table[k]) - 1) * os.lstat(a_file).st_size

def pretty_size(s):
  if s < 1024:
    return str(s)
  elif s < 1024 * 1024:
    return "%0.2f KB" % (s / 1024.)
  elif s < 1024 * 1024 * 1024:
    return "%0.2f MB" % (s / 1024. / 1024.)
  elif s < 1024 * 1024 * 1024 * 1024:
    return "%0.2f GB" % (s / 1024. / 1024. / 1024.)

print "you can save %s if you merge the duplicated files" % pretty_size(save_bytes)
choice = raw_input("merge?[y/N] ")
if choice == "y":
  print "TODO merge"

duplicate_file.close()
