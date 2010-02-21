
import pickle
import os

jpeg_size_db = {}
original_size_db = {}
sample_size_db = {}

size_db = (jpeg_size_db, original_size_db, sample_size_db)

search_sources = []
f = open("search_sources", "r")
search_sources = map(str.strip, f.readlines())
f.close()

def update_size(arg, dirname, fnames):
  global jpeg_size_db
  global original_size_db
  global sample_size_db
  
  source, type = arg
  size_table = None
  if type == "jpeg":
    size_table = jpeg_size_db
  elif type == "original":
    size_table = original_size_db
  elif type == "sample":
    size_table = sample_size_db
  
  img_set = os.path.split(source)[1]
  
  print "updating size info in folder %s" % dirname
  for fname in fnames:
    fpath = dirname + os.path.sep + fname
    if os.path.isfile(fpath) == False:
      continue
    size = os.lstat(fpath).st_size
    id = os.path.splitext(os.path.split(fpath)[1])[0]
    img_id = "%s %s" % (img_set, id)
    if size_table.has_key(size) == False:
      size_table[size] = set()
    size_table[size].add(img_id)
  
for source in search_sources:
  for type in ["jpeg", "original", "sample"]:
    top_dir = source + "/" + type
    if os.path.exists(top_dir) == False:
      continue
    os.path.walk(top_dir, update_size, (source, type))

f = open("size_db", "wb")
pickle.dump(size_db, f)
f.close()
