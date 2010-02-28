import json
import pickle
import os
import re
import shutil
import time
import hashlib

def my_makedirs(path):
  if os.path.exists(path) == False:
    os.makedirs(path)

my_makedirs("../mypic/info")
my_makedirs("../mypic/sample")
my_makedirs("../mypic/tags")

print "loading database"
f = open("md5_db", "rb")
md5_table = pickle.load(f)
f.close()
f = open("size_db", "rb")
jpeg_size_db, original_size_db, sample_size_db = pickle.load(f)
f.close()
f = open("search_db", "rb")
tag_table = pickle.load(f)
f.close()
imported_to_mypic = False
print "database loaded"


def extract_md5_from_fname(fpath):
  main_fname = id = os.path.splitext(os.path.split(fpath)[1])[0]
  # either "md5".ext or sample-"md5".ext
  if main_fname.startswith("sample-"):
    check_name = main_fname[7:]
  else:
    check_name = main_fname
  if len(check_name) != 32:
    print "length not match, not md5 value"
    return None
  if re.search("^[a-z0-9]*$", check_name) == None:
    print "regexp not match, not md5 value"
    return None
  return check_name

log_file = open("import_mypic_logfile.log", "a")
collection_file = open("imported_collection.txt", "a")
batch_collection_file = None

def write_collection(image_name):
  global collection_file
  global batch_collection_file
  
  image_name = image_name.strip()
  if image_name != "":
    collection_file.write(image_name + "\n")
    if batch_collection_file != None:
      batch_collection_file.write(image_name + "\n")

def image_name_to_path_not_checked(img_name, type, ext_with_dot):
  img_set, id_str = img_name.split()
  id = int(id_str)
  bucket_size = 100
  bucket_id = id / bucket_size
  bucket_name = "/%d-%d" % (bucket_size * bucket_id, bucket_id * bucket_size + bucket_size - 1)
  fpath = "../" + img_set + "/" + type + "/" + bucket_name + "/" + id_str + ext_with_dot
  return fpath

def image_name_to_path(img_name, type):
  img_set, id_str = img_name.split()
  id = int(id_str)
  bucket_size = 100
  bucket_id = id / bucket_size
  bucket_name = "/%d-%d" % (bucket_size * bucket_id, bucket_id * bucket_size + bucket_size - 1)
  for ext in ("jpg", "png", "gif"):
    fpath = "../" + img_set + "/" + type + "/" + bucket_name + "/" + id_str + "." + ext
    if os.path.exists(fpath):
      return fpath
  return None

def load_image_info(img_name):
  img_set, id_str = img_name.split()
  id = int(id_str)
  bucket_size = 100
  bucket_id = id / bucket_size
  bucket_name = "/%d-%d" % (bucket_size * bucket_id, bucket_id * bucket_size + bucket_size - 1)
  fpath = "../" + img_set + "/info/" + bucket_name + "/" + id_str + ".txt"
  if os.path.exist(fpath):
    info_f = fopen(fpath, "r")
    info = json.loads(info_f.read())
    info_f.close()
    return info
  else:
    return None

def import_file_real(fpath, dest):
  print fpath, dest
  
def extract_image_name_in_fname(fpath):
  main_fname = os.path.splitext(os.path.split(fpath)[1])[0]
  main_fname = main_fname.lower()
  for head in ("moe", "moe_imouto", "konachan", "konachan.com -", "danbooru", "nekobooru"):
    if main_fname.startswith(head + " "):
      splt = main_fname.split()
      if splt[0] == "moe":
        img_name = "moe_imouto " + splt[1]
      elif splt[0] == "konachan.com":
        img_name = "konachan " + splt[2]
      else:
        img_name = splt[0] + " " + splt[1]
      return img_name
  return None

def prepare_folder_by_image_name(image_name):
  img_set, id_str = image_name.split()
  id = int(id_str)
  bucket_size = 100
  bucket_id = id / bucket_size
  bucket_name = "/%d-%d" % (bucket_size * bucket_id, bucket_id * bucket_size + bucket_size - 1)
  for type in ("jpeg", "original", "sample", "tags", "info"):
    dir_path = "../" + img_set + "/" + type + "/" + bucket_name
    my_makedirs(dir_path)

def import_by_image_name(fpath, image_name):
  prepare_folder_by_image_name(image_name)
  if image_name_to_path(image_name, "original") != None:
    # image exists
    print "image exists"
    log_file.write(fpath + "\n" + "by image name, already exists\n" + image_name + " (image name)" + "\n\n\n")
    write_collection(image_name + "\n")
    
    # still copy file
    ext_with_dot = os.path.splitext(fpath)[1]
    src = fpath
    dst = image_name_to_path_not_checked(image_name, "sample", ext_with_dot)
    print "[copy] %s ==> %s" % (src, dst)
    shutil.copyfile(src, dst)
  else:
    # image not exist
    print 'image not exist, quality not known, copy to "sample" folder'
    log_file.write(fpath + "\n" + "by image name, as sample image\n" + image_name + " (image name, quality not known, as sample)" + "\n\n\n")
    write_collection(image_name + "\n")
    # copy file!
    ext_with_dot = os.path.splitext(fpath)[1]
    src = fpath
    dst = image_name_to_path_not_checked(image_name, "sample", ext_with_dot)
    print "[copy] %s ==> %s" % (src, dst)
    shutil.copyfile(src, dst)
    
    # fake image tags
    tag_fname = image_name_to_path_not_checked(image_name, "tags", ".txt")
    tag_f = open(tag_fname, "w")
    main_fname = os.path.splitext(os.path.split(fpath)[1])[0]
    main_fname_splt = main_fname.split()
    fake_tags = []
    for i in range(2, len(main_fname_splt)):
      tag_f.write(main_fname_splt[i] + "\n")
      fake_tags += main_fname_splt[i],
    tag_f.close()
    
    # fake image info
    info_fname = image_name_to_path_not_checked(image_name, "info", ".txt")
    if os.path.exists(info_fname) == False:
      info_f = open(info_fname, "w")
      info_table = {}
      info_table["import_source"] = fpath
      info_table["md5"] = md5_on_file(fpath)
      info_table["tags"] = " ".join(fake_tags)
      info_table["import_time"] = int(time.time())
      json.dump(info_table, info_f)
      info_f.close()

def md5_on_file(fpath):
  m = hashlib.md5()
  pic_f = open(fpath, "rb")
  m.update(pic_f.read())
  pic_f.close()
  return m.hexdigest()

def bucket_cmp(b1, b2):
  v1 = int(b1.split("-")[0])
  v2 = int(b2.split("-")[0])
  if v1 < v2:
    return -1
  elif v1 == v2:
    return 0
  else:
    return 1

def img_fname_cmp(b1, b2):
  v1 = int(b1.split(".")[0])
  v2 = int(b2.split(".")[0])
  if v1 < v2:
    return -1
  elif v1 == v2:
    return 0
  else:
    return 1

def import_mypic(fpath, tags):
  global log_file
  global collection_file
  global imported_to_mypic
  id = 1  # default start id
  
  # find proper id
  dir_list = os.listdir("../mypic/sample")
  dir_list.sort(cmp = bucket_cmp, reverse = True)
  determined_id = False
  for d in dir_list:
    f_list = os.listdir("../mypic/sample/" + d)
    f_list.sort(cmp = img_fname_cmp, reverse = True)
    
    for f in f_list:
      f = f.lower()
      if f.endswith(".jpg") or f.endswith(".png") or f.endswith(".gif"):
        v = int(f.split(".")[0])
        id = v + 1
        determined_id = True
      
      if determined_id == True:
        break
        
    if determined_id == True:
      break
  
  print "import mypic with id=%d" % id
  image_name = "mypic %d" % id
  prepare_folder_by_image_name(image_name)
  
  # copy file!
  ext_with_dot = os.path.splitext(fpath)[1]
  src = fpath
  dst = image_name_to_path_not_checked(image_name, "sample", ext_with_dot)
  print "[copy] %s ==> %s" % (src, dst)
  if os.path.exists(dst):
    print "[error] file already exists, not copied!"
    return
  shutil.copyfile(src, dst)
  
  # write image tags
  tag_fname = image_name_to_path_not_checked(image_name, "tags", ".txt")
  tag_f = open(tag_fname, "w")
  for tag in tags:
    tag_f.write(tag + "\n")
  tag_f.close()
  
  # write image info
  info_fname = image_name_to_path_not_checked(image_name, "info", ".txt")
  if os.path.exists(info_fname) == False:
    info_f = open(info_fname, "w")
    info_table = {}
    info_table["import_source"] = fpath
    info_table["md5"] = md5_on_file(fpath)
    info_table["tags"] = " ".join(tags)
    info_table["import_time"] = int(time.time())
    json.dump(info_table, info_f)
    info_f.close()
  
  log_file.write(fpath + "\n" + "import as my picture\n" + dst + "\n\n\n")
  write_collection(image_name + "\n")
  
  # update sizedb, md5db, & tags db
  imported_to_mypic = True
  md5_val = md5_on_file(src)
  md5_table[md5_val] = image_name
  
  fsize = os.lstat(src).st_size
  if sample_size_db.has_key(fsize) == False:
    sample_size_db[fsize] = set()
  sample_size_db[fsize].add(image_name)
  
  for tag in tags:
    if tag_table.has_key(tag) == False:
      tag_table[tag] = set()
    tag_table[tag].add(image_name)
  

def import_file(fpath, default_tags = None):
  global log_file
  global collection_file
  
  ever_found = False
  
  image_name = extract_image_name_in_fname(fpath)
  if image_name != None:
    print "extracted image name '%s'" % image_name
    import_by_image_name(fpath, image_name)
    ever_found = True
  
  if ever_found:
    return
  
  md5_value = extract_md5_from_fname(fpath)
  if md5_value != None:
    print "searching with suggested md5 value: %s" % md5_value
    if md5_table.has_key(md5_value):
      prepare_folder_by_image_name(md5_table[md5_value])
      if os.path.splitext(fpath)[1].lower() == ".png":
        dest = image_name_to_path_not_checked(md5_table[md5_value], "original", os.path.splitext(fpath)[1])
        log_file.write(fpath + "\n" + "by md5 value (as original, PNG given)\n" + dest + "\n\n\n")
      else:
        dest = image_name_to_path_not_checked(md5_table[md5_value], "sample", os.path.splitext(fpath)[1])
        log_file.write(fpath + "\n" + "by md5 value (as sample, quality not known)\n" + dest + "\n\n\n")
      print "[copy] %s ==> %s" % (fpath, dest)
      shutil.copyfile(fpath, dest)
      write_collection(md5_table[md5_value] + "\n")
      ever_found = True
  
  if ever_found:
    return
    
  fsize = os.lstat(fpath).st_size
  md5_str = md5_on_file(fpath)
  print "searching with fsize=%d, md5=%s" % (fsize, md5_str)
  for type in ("jpeg", "original", "sample"):
    if type == "jpeg":
      table = jpeg_size_db
    elif type == "original":
      table = original_size_db
    elif type == "sample":
      table = sample_size_db
    else:
      table = None
      
    if table.has_key(fsize):
      result_set = table[fsize]
      for result in result_set:
        img_path = image_name_to_path(result, type)
        if img_path == None:
          continue
        img_md5 = md5_on_file(img_path)
        if img_md5 == md5_str:
          print "found to be %s" % result
          log_file.write(fpath + "\n" + "by md5 value & fsize\n" + img_path + "\n\n\n")
          write_collection(result + "\n")
          ever_found = True
          break
  
  if ever_found:
    return
  
  # move to "mypic"
  print "the image is not in moe library, it will be moved into 'mypic' folder"
  if default_tags == None:
    input = raw_input("input tags, separated by space: ")
    tags = input.split()
  else:
    tags = default_tags
  import_mypic(fpath, tags)

def has_subdir(top_dir):
  for f in os.listdir(top_dir):
    if os.path.isdir(top_dir + "/" + f):
      return True
  return False

def is_image(fpath):
  fpath = fpath.lower()
  return os.path.isfile(fpath) and (fpath.endswith(".jpg") or fpath.endswith(".png") or fpath.endswith(".gif"))

def import_dir(top_dir):
  global batch_collection_file
  
  default_batch_collection_fname = "imported_collection." + os.path.split(top_dir)[1] + ".txt"
  if os.path.exists(default_batch_collection_fname):
    i = 2
    while True:
      col_name = "imported_collection." + os.path.split(top_dir)[1] + "_" + str(i) + ".txt"
      if os.path.exists(col_name) == False:
        break
      i += 1
    batch_collection_file = open(col_name, "a")
  else:
    batch_collection_file = open(default_batch_collection_fname, "a")
    
  if has_subdir(top_dir):
    print "[warning] subdir not visitted"
  input = raw_input("input default tags, separated by space: ")
  tags = input.split()
  for f in os.listdir(top_dir):
    fpath = top_dir + "/" + f
    if is_image(fpath):
      print "[batch] %s" % fpath
      import_file(fpath, tags)
  batch_collection_file.close()
  batch_collection_file = None

print "input empty line to quit"
while True:
  input = raw_input("file or folder path: ")
  input = input.strip()
  if input == "":
    break
  elif os.path.exists(input) == False:
    print "file or folder not found"
    continue
  elif os.path.isfile(input):
    import_file(input)
  elif os.path.isdir(input):
    import_dir(input)

log_file.close()
collection_file.close()

if imported_to_mypic:
  print "updating database"
  f = open("size_db", "wb")
  size_db = (jpeg_size_db, original_size_db, sample_size_db)
  pickle.dump(size_db, f)
  f.close()

  f = open("search_db", "wb")
  pickle.dump(tag_table, f)
  f.close()
  
  f = open("md5_db", "wb")
  pickle.dump(md5_table, f)
  f.close()
