# This script is used to replace images into highres version

import os

# where is the image
IMAGE_ROOT = "G:\\pictures"

# don't copy images larger than 8M
IMAGE_MAX_SIZE = 8 * 1024 * 1024

def is_image(fname):
  fname = fname.lower()
  for ext in [".jpg", ".png", ".gif", ".swf", ".bmp"]:
    if fname.endswith(ext):
      return True
  return False

def has_highres_image_set(set_name):
  if set_name in ["moe_imouto", "nekobooru", "konachan", "danbooru"]:
    return True
  else:
    return False

def get_bucket_name(id_in_set):
  BUCKET_SIZE = 100
  bucket_id = id_in_set / BUCKET_SIZE
  bucket_name = "%d-%d" % (bucket_id * BUCKET_SIZE, bucket_id * BUCKET_SIZE + BUCKET_SIZE - 1)
  return bucket_name

def get_highres_image(set_name, image_id, ext_name):
  if has_highres_image_set(set_name):
    bucket_name = get_bucket_name(int(image_id))
    image_fn = IMAGE_ROOT + "\\" + set_name + "_highres\\" + bucket_name + "\\" + image_id + "." + ext_name
    if os.path.exists(image_fn):
      return image_fn
  return None

def split_image_fname(fname):
  image_set = None
  image_id = None
  splt = fname.split()
  image_set = splt[0]
  image_id = splt[1].split(".")[0]
  ext_name = splt[1].split(".")[1]
  return (image_set, image_id, ext_name)

def util_execute(cmd):
  print "[cmd] %s" % cmd
  os.system(cmd)

def replace_highres(folder):
  for f in os.listdir(folder):
    image_set, image_id, ext_name = split_image_fname(f)
    highres_image = get_highres_image(image_set, image_id, ext_name)
    if highres_image == None:
      continue
    else:
      if os.stat(highres_image).st_size > IMAGE_MAX_SIZE:
        print "Image too big, skip: %s" % highres_image
      else:
        dest_fn = "%s %s.%s" % (image_set + "_highres", image_id, ext_name)
        util_execute("copy \"%s\" \"%s\\%s\"" % (highres_image, folder, dest_fn))
        util_execute("del \"%s\\%s\"" % (folder, f))
      

if __name__ == "__main__":
  folders = ["D:\\Santa\\Pictures\\ACG Cellphone", "D:\\Santa\\Pictures\\ACG Wallpaper", "D:\\Santa\\Pictures\\Other Photos"]
  for folder in folders:
    replace_highres(folder)
