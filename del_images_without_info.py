import os

f = open("search_sources", "r")
search_sources = f.read().split()
f.close()

print search_sources

def is_image(fpath):
  fpath = fpath.lower()
  return os.path.isfile(fpath) and (fpath.endswith(".jpg") or fpath.endswith(".png") or fpath.endswith(".gif"))

images_without_info = []

def images_walker(arg, dirname, fnames):
  global images_without_info
  print "checking dir %s" % dirname
  source = arg
  for f in fnames:
    fpath = dirname + "/" + f
    if is_image(fpath) == False:
      continue
    id = int(os.path.splitext(os.path.split(fpath)[1])[0])
    bucket_size = 100
    bucket_id = id / bucket_size
    bucket_name = "%d-%d" % (bucket_id * bucket_size, bucket_id * bucket_size + bucket_size - 1)
    info_fpath = source + "/info/" + bucket_name + "/" + str(id) + ".txt"
    if os.path.exists(info_fpath) == False:
      print "[missing info] %s" % fpath
      images_without_info += fpath,

for source in search_sources:
  for type in ["jpeg", "sample", "preview", "original"]:
    if os.path.exists(source + "/" + type):
      os.path.walk(source + "/" + type, images_walker, source)

print "list of images missing info: (also written to 'missing_info.txt')"
f = open("missing_info.txt", "w")
for img in images_without_info:
  print img
  f.write(img + "\n")
f.close()

choice = raw_input("really delete them? [y/N]")
if choice == "y":
  for img in images_without_info:
    print "[del] %s" % img
    os.remove(img)
