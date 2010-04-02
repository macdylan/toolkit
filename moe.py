# One script to manage all my pictures.
#
# Author: Santa Zhang (santa1987@gmail.com)
#

# Database models:
#
# images(id, set_name, id_in_set, md5)
# tags(id, name)
# images_has_tags(image_id, tag_id)
# albums(id, name)
# albums_has_images(album_id, image_id)
# black_list(set_name, start_id, end_id)

# The sqlite3 database which will be used.
SQLITE3_DB = "moe.db3"

import sys, os, json, hashlib, sqlite3, shutil
# Open the sqlite3 connection.
DB_CONN = sqlite3.connect(SQLITE3_DB)

# Create tables if necessary.
DB_CONN.execute("create table if not exists images(id integer primary key, set_name text, id_in_set int unique, md5 text, rating int)")
DB_CONN.execute("create table if not exists tags(id integer primary key, name text unique)")
DB_CONN.execute("create table if not exists images_has_tags(image_id int, tag_id int)")
DB_CONN.execute("create table if not exists albums(id integer primary key, name text unique)")
DB_CONN.execute("create table if not exists albums_has_images(album_id int, image_id int)")
DB_CONN.execute("create table if not exists black_list(set_name text, start_id int, end_id int)")
DB_CONN.execute("create table if not exists settings(key text, value text)")

# Create indexes if necessary.
DB_CONN.execute("create index if not exists images_index on images(id, set_name, id_in_set, md5, rating)")
DB_CONN.execute("create index if not exists tags_index on tags(id, name)")
DB_CONN.execute("create index if not exists images_has_tags_index on images_has_tags(image_id, tag_id)")
DB_CONN.execute("create index if not exists albums_has_imags_index on albums_has_images(album_id, image_id)")
DB_CONN.execute("create index if not exists settings_index on settings(key, value)")

# Insert basic config data if necessary.
c = DB_CONN.cursor()
c.execute("select value from settings where key = 'images_root'")
ret = c.fetchall()
if len(ret) == 0:
  print "Please input the 'image_root' where all images will be saved to:"
  image_root = raw_input()
  c.execute("insert into settings(key, value) values('images_root', '%s')" % image_root)
  DB_CONN.commit()

def db_commit():
  DB_CONN.commit()

def db_add_image(fpath, image_set, id_in_set):
  print "[db.add] %s" % fpath
  bucket_name = util_get_bucket_name(id_in_set)
  dest_folder = db_get_setting("images_root") + os.path.sep + image_set + os.path.sep + bucket_name
  dest_file = dest_folder + os.path.sep + os.path.split(fpath)[1]
  if os.path.exists(dest_file):
    print "file exists: the file '%s' exists" % dest_file
    return False
  md5 = util_md5_of_file(fpath)
  # Check if md5 already in db
  image_found = db_get_image_by_md5(md5)
  if image_found != None:
    print "md5 duplicate: same as '%s %d'" % (image_found[1], image_found[2])
    return False
  util_make_dirs(dest_folder)
  shutil.copyfile(fpath, dest_file)
  c = DB_CONN.cursor()
  c.execute("insert into images(set_name, id_in_set, md5) values('%s', %d, '%s')" % (image_set, id_in_set, md5))
  return True

def db_get_image_by_md5(md5):
  c = DB_CONN.cursor()
  c.execute("select * from images where md5 = '%s'" % md5)
  ret = c.fetchone()
  return ret

def db_get_image_by_id_in_set(image_set, id_in_set):
  c = DB_CONN.cursor()
  c.execute("select id from images where set_name = '%s' and id_in_set = %d" % (image_set, id_in_set))
  ret = c.fetchone()
  return ret

def db_set_image_tags(image_set, id_in_set, tags):
  img = db_get_image_by_id_in_set(image_set, id_in_set)
  db_clear_image_tags(img[0])
  db_add_image_tags(img[0], tags)

def db_get_image_tags():
  pass

def db_add_image_tags(image_id, tags):
  for tag in tags:
    db_add_tag(tag)
    tag = db_get_tag_by_name(tag)
    tag_id = tag[0]
    c = DB_CONN.cursor()
    c.execute("insert into images_has_tags(image_id, tag_id) values(%d, %d)" % (image_id, tag_id))

def db_remove_image_tags():
  pass

def db_clear_image_tags(image_id):
  c = DB_CONN.cursor()
  c.execute("delete from images_has_tags where image_id = %d" % image_id)

def db_del_image():
  pass

def db_add_tag(tag_name):
  c = DB_CONN.cursor()
  ret = db_get_tag_by_name(tag_name)
  if ret == None:
    c.execute("insert into tags(name) values(\"%s\")" % tag_name.replace("'", "\\'"))

def db_get_tag_by_name(tag_name):
  c = DB_CONN.cursor()
  c.execute("select id from tags where name = \"%s\"" % tag_name.replace("'", "\\'"))
  ret = c.fetchone()
  return ret

def db_add_album():
  pass

def db_get_album_images():
  pass

def db_add_album_images():
  pass

def db_del_album_images():
  pass

def db_del_album():
  pass

db_setting_images_root = None
def db_get_setting(key):
  if key == "images_root":
    global db_setting_images_root
    if db_setting_images_root == None:
      c = DB_CONN.cursor()
      c.execute("select value from settings where key = 'images_root'")
      ret = c.fetchall()
      db_setting_images_root = ret[0][0]
    return db_setting_images_root

def util_is_image(fname):
  fname = fname.lower()
  for ext in [".jpg", ".png", ".gif", ".swf", ".bmp"]:
    if fname.endswith(ext):
      return True
  return False

def util_make_dirs(path):
  if os.path.exists(path) == False:
    print "[mkdir] %s" % path
    os.makedirs(path)

def util_md5_of_file(fpath):
  m = hashlib.md5()
  f = open(fpath, "rb")
  m.update(f.read())
  f.close()
  return m.hexdigest()

def util_get_bucket_name(id_in_set):
  BUCKET_SIZE = 100
  bucket_id = id_in_set / BUCKET_SIZE
  bucket_name = "%d-%d" % (bucket_id * BUCKET_SIZE, bucket_id * BUCKET_SIZE + BUCKET_SIZE - 1)
  return bucket_name

def util_get_image_info(image_set, id_in_set):
  c = DB_CONN.cursor()
  c.execute("select id, md5 from images where set_name = '%s' and id_in_set = %d" % (image_set, id_in_set))
  ret = c.fetchone()
  if ret == None:
    return None
  info = {}
  info["image_set"] = image_set
  info["id"] = ret[0]
  info["md5"] = ret[1]
  c = DB_CONN.cursor()
  c.execute("select tags.name from tags, images_has_tags where tags.id = images_has_tags.tag_id and images_has_tags.image_id = %d" % info["id"])
  ret_all = c.fetchall()
  info["tags"] = []
  for ret in ret_all:
    info["tags"] += ret[0],
  info["tags"].sort()
  # TODO check this
  c.execute("select albums.name from albums, albums_has_images where albums.id = albums_has_images.album_id and albums_has_images.image_id = %d" % info["id"])
  ret_all = c.fetchall()
  info["albums"] = []
  for ret in ret_all:
    info["albums"] += ret[0],
  info["albums"].sort()
  return info

# Import images.
def moe_import():
  image_set = raw_input("image set name: ")
  image_folder = raw_input("image folder: ")
  info_folder = raw_input("info folder: ")
  
  def import_walker(info_folder, dir, files):
    for file in files:
      fpath = dir + os.path.sep + file
      if util_is_image(fpath) == False:
        continue
      id_in_set = int(os.path.splitext(file)[0])
      info_fpath = info_folder + dir[len(image_folder):] + os.path.sep + str(id_in_set) + ".txt"
      info_file = open(info_fpath)
      json_ret = json.loads(info_file.read())
      info_file.close()
      if db_add_image(fpath, image_set, id_in_set) == True:
        db_set_image_tags(image_set, id_in_set, json_ret[u"tags"].split())
    db_commit()
    
  os.path.walk(image_folder, import_walker, info_folder)

def moe_info():
  def print_info(info):
    print "image set:   %s" % info["image_set"]
    print "id in set:   %d" % info["id"]
    print "md5 sum:     %s" % info["md5"]
    print "tags:"
    for tag in info["tags"]:
      print "        %s" % tag
    for album in info["albums"]:
      print "        %s" % album
      
  if len(sys.argv) == 4:
    info = util_get_image_info(sys.argv[2], int(sys.argv[3]))
    if info == None:
      print "image '%s %d' not found!" % (sys.argv[2], int(sys.argv[3]))
    else:
      print_info(info)
  else:
    # Interactive mode
    print "input empty line to quit"
    image_set = None
    while True:
      input = raw_input("image set or image id in set: ")
      if input == "":
        break
      if " " in input:
        splt = image_set.split()
        image_set = splt[0]
        image_id = int(splt[1])
        info = util_get_image_info(image_set, image_id)
        if info == None:
          print "image '%s %d' not found!" % (image_set, image_id)
        else:
          print_info(info)
      elif str.isdigit(input):
        info = util_get_image_info(image_set, int(input))
        if info == None:
          print "image '%s %d' not found!" % (image_set, int(input))
        else:
          print_info(info)
      else:
        image_set = input
        print "changed active image set to '%s'" % image_set

def moe_import_album():
  pass

def moe_import_black_list():
  fpath = raw_input("black list file path: ")
  f = open(fpath)
  for line in f.readlines():
    line = line.strip()
    splt = line.split()
    image_set = splt[0]
    if "-" in splt[1]:
      splt2 = splt[1].split("-")
      start_id = int(splt2[0])
      end_id = int(splt2[1])
    else:
      start_id = int(splt[1])
      end_id = int(splt[1])
    c = DB_CONN.cursor()
    c.execute("select * from black_list where set_name = '%s' and start_id = %d and end_id = %d" % (image_set, start_id, end_id))
    ret = c.fetchone()
    if ret == None:
      c.execute("insert into black_list(set_name, start_id, end_id) values('%s', %d, %d)" % (image_set, start_id, end_id))
  db_commit()

def moe_import_rating():
  image_set = raw_input("image set name: ")
  rating_folder = raw_input("ratings folder: ")
  
  def import_walker(arg, dir, files):
    print "working on dir: %s" % dir
    for file in files:
      if file.lower().endswith(".txt") == False:
        continue
      fpath = dir + os.path.sep + file
      image_id = int(os.path.splitext(file)[0])
      print image_id
      f = open(fpath)
      rating_text = f.read()
      f.close()
      rating_value = None
      if rating_text == "delete":
        rating_value = 0
      elif rating_text == "so-so":
        rating_value = 1
      elif rating_text == "good":
        rating_value = 2
      elif rating_text == "excellent":
        rating_value = 3
      else:
        continue
      c = DB_CONN.cursor()
      c.execute("select * from images where set_name = '%s' and id_in_set = %d" % (image_set, image_id))
      if c.fetchone() != None:
        c.execute("update images set rating = %d where set_name = '%s' and id_in_set = %d" % (rating_value, image_set, image_id))
    db_commit()
    
  os.path.walk(rating_folder, import_walker, None)

def moe_help():
  print "moe.py: manage all my acg pictures"
  print "usage: moe.py <command>"
  print "available commands:"
  print ""
  print "  help                 display this info"
  print "  import               batch import pictures"
  print "  import-album         import existing album"
  print "  import-black-list    import existing black list file"
  print "  import-rating        import existing rating"
  print "  info                 display info about an image"
  print ""
  print "author: Santa Zhang (santa1987@gmail.com)"

if __name__ == "__main__":
  if len(sys.argv) == 1 or sys.argv[1] == "help":
    moe_help()
  elif sys.argv[1] == "import":
    moe_import()
  elif sys.argv[1] == "import-black-list":
    moe_import_black_list()
  elif sys.argv[1] == "import-rating":
    moe_import_rating()
  elif sys.argv[1] == "info":
    moe_info()
  else:
    print "command '%s' not understood, see 'moe help' for more info" % sys.argv[1]
