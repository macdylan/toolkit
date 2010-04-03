# One script to manage all my pictures.
#
# Author: Santa Zhang (santa1987@gmail.com)
#

# Database models:
#
# images(id, set_name, id_in_set, md5, rating, ext, file_size)
# tags(id, name)
# images_has_tags(image_id, tag_id)
# albums(id, name)
# albums_has_images(album_id, image_id)
# black_list(set_name, start_id, end_id)

# The sqlite3 database which will be used.
SQLITE3_DB = "moe.db3"

import sys, os, json, hashlib, sqlite3, shutil, urllib2, re, time, socket, traceback
from urllib2 import HTTPError
from select import *
# Open the sqlite3 connection.
DB_CONN = sqlite3.connect(SQLITE3_DB)

# Create tables if necessary.
DB_CONN.execute("create table if not exists images(id integer primary key, set_name text, id_in_set int, md5 text, rating int, ext text, file_size int)")
DB_CONN.execute("create table if not exists tags(id integer primary key, name text unique)")
DB_CONN.execute("create table if not exists images_has_tags(image_id int, tag_id int)")
DB_CONN.execute("create table if not exists albums(id integer primary key, name text unique)")
DB_CONN.execute("create table if not exists albums_has_images(album_id int, image_id int)")
DB_CONN.execute("create table if not exists black_list(set_name text, start_id int, end_id int)")
DB_CONN.execute("create table if not exists settings(key text, value text)")

# Create indexes if necessary.
DB_CONN.execute("create index if not exists images_index on images(id, set_name, id_in_set, md5, rating, ext, file_size)")
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
c.execute("select value from settings where key = 'tmp_folder'")
ret = c.fetchall()
if len(ret) == 0:
  print "Please input the 'tmp_folder' where temp results will be saved:"
  tmp_foler = raw_input()
  c.execute("insert into settings(key, value) values('tmp_folder', '%s')" % tmp_foler)
  DB_CONN.commit()

def db_commit():
  DB_CONN.commit()
  
def db_image_in_black_list(image_set, id_in_set):
  c = DB_CONN.cursor()
  c.execute("select * from black_list where set_name = '%s' and start_id <= %d and %d <= end_id" % (image_set, id_in_set, id_in_set))
  if c.fetchone() != None:
    return True
  else:
    return False

def db_add_image(fpath, image_set, id_in_set):
  print "[db.add] %s" % fpath
  bucket_name = util_get_bucket_name(id_in_set)
  dest_folder = db_get_setting("images_root") + os.path.sep + image_set + os.path.sep + bucket_name
  dest_file = dest_folder + os.path.sep + os.path.split(fpath)[1]
  file_ext = os.path.splitext(fpath)[1]
  md5 = util_md5_of_file(fpath)
  # Check if md5 already in db
  image_found = db_get_image_by_md5(md5)
  if image_found != None:
    print "md5 duplicate: same as '%s %d'" % (image_found[1], image_found[2])
    return False
  util_make_dirs(dest_folder)
  if os.path.exists(dest_file):
    print "[warning] the file '%s' exists" % dest_file
  else:
    shutil.move(fpath, dest_file)
  c = DB_CONN.cursor()
  c.execute("select * from images where set_name = '%s' and id_in_set = %d" % (image_set, id_in_set))
  if c.fetchone() == None:
    file_size = os.stat(dest_file).st_size
    c.execute("insert into images(set_name, id_in_set, md5, ext, file_size) values('%s', %d, '%s', '%s', %d)" % (image_set, id_in_set, md5, file_ext, file_size))
  return True

def db_get_image_by_md5(md5):
  c = DB_CONN.cursor()
  c.execute("select * from images where md5 = '%s'" % md5)
  ret = c.fetchone()
  return ret

def db_get_image_by_id_in_set(image_set, id_in_set):
  c = DB_CONN.cursor()
  c.execute("select * from images where set_name = '%s' and id_in_set = %d" % (image_set, id_in_set))
  ret = c.fetchone()
  return ret

def db_set_image_tags(image_set, id_in_set, tags):
  img = db_get_image_by_id_in_set(image_set, id_in_set)
  if img == None:
    print "[failure] cannot set tags on '%s %d': image not found" % (image_set, id_in_set)
    return
  db_clear_image_tags(img[0])
  db_add_image_tags(img[0], tags)

def db_get_image_tags(image_set, id_in_set):
  img = db_get_image_by_id_in_set(image_set, id_in_set)
  if img == None:
    return None
  image_id = img[0]
  c.execute("select tags.name from tags, images_has_tags where tags.id = images_has_tags.tag_id and images_has_tags.image_id = %d" % image_id)
  ret_all = c.fetchall()
  tags = []
  for ret in ret_all:
    tags += ret[0],
  tags.sort()
  return tags

def db_add_image_tags(image_id, tags):
  for tag in tags:
    db_add_tag(tag)
    tag = db_get_tag_by_name(tag)
    tag_id = tag[0]
    c = DB_CONN.cursor()
    c.execute("insert into images_has_tags(image_id, tag_id) values(%d, %d)" % (image_id, tag_id))

def db_clear_image_tags(image_id):
  c = DB_CONN.cursor()
  c.execute("delete from images_has_tags where image_id = %d" % image_id)

def db_del_image(image_set, id_in_set):
  img = db_get_image_by_id_in_set(image_set, id_in_set)
  if img == None:
    return None
  image_id = img[0]
  c.execute("delete from images_has_tags where image_id = %d" % image_id)
  c.execute("delete from albums_has_images where image_id = %d" % image_id)
  c.execute("delete from images where id = %d" % image_id)
  db_commit()
  # Delete file after commit.
  fpath = db_get_setting("images_root") + os.path.sep + img[1] + os.path.sep + util_get_bucket_name(img[2]) + os.path.sep + str(img[2]) + img[5]
  print "[del] %s" % fpath
  os.remove(fpath)

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

def db_add_album(album_name):
  c = DB_CONN.cursor()
  c.execute("select * from albums where name = '%s'" % album_name)
  if c.fetchone() == None:
    c.execute("insert into albums(name) values('%s')" % album_name)

def db_get_album_images(album_name):
  c = DB_CONN.cursor()
  c.execute("select id from albums where name = '%s'" % album_name)
  ret = c.fetchone()
  if ret == None:
    return None
  else:
    album_id = ret[0]
    c.execute("select image_id from albums_has_images where album_id = %d" % album_id)
    ret_all = c.fetchall()
    img_list = []
    for ret in ret_all:
      c.execute("select * from images where id = %d" % ret[0])
      img = c.fetchone()
      if img != None:
        img_list += img, 
    return img_list

def db_add_album_image(album_name, image_set, id_in_set):
  c = DB_CONN.cursor()
  c.execute("select id from albums where name = '%s'" % album_name)
  ret = c.fetchone()
  if ret == None:
    return False
  album_id = ret[0]
  img = db_get_image_by_id_in_set(image_set, id_in_set)
  if img == None:
    return False
  image_id = img[0]
  c.execute("select * from albums_has_images where album_id = %d and image_id = %d" % (album_id, image_id))
  if c.fetchone() == None:
    c.execute("insert into albums_has_images(album_id, image_id) values(%d, %d)" % (album_id, image_id))
  return True

def db_get_image_albums(image_set, id_in_set):
  c = DB_CONN.cursor()
  img = db_get_image_by_id_in_set(image_set, id_in_set)
  if img == None:
    return None
  image_id = img[0]
  c.execute("select albums.name from albums, albums_has_images where albums.id = albums_has_images.album_id and albums_has_images.image_id = %d" % image_id)
  ret_all = c.fetchall()
  albums = []
  for ret in ret_all:
    albums += ret[0],
  albums.sort()
  return albums

db_setting_images_root = None
db_setting_tmp_folder = None
def db_get_setting(key):
  if key == "images_root":
    global db_setting_images_root
    if db_setting_images_root == None:
      c = DB_CONN.cursor()
      c.execute("select value from settings where key = 'images_root'")
      ret = c.fetchone()
      db_setting_images_root = ret[0]
    return db_setting_images_root
  elif key == "tmp_folder":
    global db_setting_tmp_folder
    if db_setting_tmp_folder == None:
      c = DB_CONN.cursor()
      c.execute("select value from settings where key = 'tmp_folder'")
      ret = c.fetchone()
      db_setting_tmp_folder = ret[0]
    return db_setting_tmp_folder

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
  img = db_get_image_by_id_in_set(image_set, id_in_set)
  if img == None:
    return None
  info = {}
  info["image_set"] = image_set
  info["id"] = img[0]
  info["md5"] = img[3]
  info["tags"] = db_get_image_tags(image_set, id_in_set)
  info["albums"] = db_get_image_albums(image_set, id_in_set)
  return info

def util_download_danbooru_image(image_set, id_in_set, image_url, image_size = 0, image_md5 = None):
  images_root = db_get_setting("images_root")
  image_url = "http://" + urllib2.quote(image_url[7:])
  image_ext = image_url[image_url.rfind("."):]
  dest_image = images_root + os.path.sep + image_set + os.path.sep + util_get_bucket_name(id_in_set) + os.path.sep + str(id_in_set) + image_ext
  if os.path.exists(dest_image):
    db_add_image(dest_image, image_set, id_in_set)
    print "[skip] '%s %d' already downloaded" % (image_set, id_in_set)
    return False
  tmp_folder = db_get_setting("tmp_folder")
  util_make_dirs(tmp_folder + os.path.sep + image_set)
  try:
    download_fpath = tmp_folder + os.path.sep + image_set + os.path.sep + str(id_in_set) + image_ext
    print "[download] '%s %d'" % (image_set, id_in_set)
    image_data = urllib2.urlopen(image_url).read()
    download_file = open(download_fpath, "wb")
    download_file.write(image_data)
    download_file.close()
    
    if image_size != 0 and os.stat(download_fpath).st_size != image_size:
      print "[failure] downloaded '%s %d' has wrong size, discarded" % (image_set, id_in_set)
      os.remove(download_fpath)
      return False
    
    if image_md5 != None and image_md5 != util_md5_of_file(download_fpath):
      print "[failure] downloaded '%s %d' has wrong md5 sum, discarded" % (image_set, id_in_set)
      os.remove(download_fpath)
      return False
    
    return True
  except:
    traceback.print_exc()
    time.sleep(1)

def util_mirror_danbooru_site(site_url):
  SOCKET_TIMEOUT = 30
  socket.setdefaulttimeout(SOCKET_TIMEOUT)
  tmp_folder = db_get_setting("tmp_folder")
  print "mirroring danbooru-like site: %s" % site_url
  
  if site_url.find("danbooru") != -1:
    image_set_base = "danbooru"
    image_set_highres = "danbooru_highres"
  elif site_url.find("konachan") != -1:
    image_set_base = "konachan"
    image_set_highres = "konachan_highres"
  elif site_url.find("imouto") != -1:
    image_set_base = "moe_imouto"
    image_set_highres = "moe_imouto_highres"
  elif site_url.find("nekobooru") != -1:
    image_set_base = "nekobooru"
    image_set_highres = "nekobooru_highres"
  else:
    print "site '%s' not supported yet!"
    return
  
  # Start mirroring from page 1.
  page_id = 1
  while True:
    try:
      query_url = site_url + ("/post/index.json?page=%d" % page_id)
      print "working on page %d" % page_id
      
      # Go on to next page
      page_id += 1
      
      try:
        query_reply = "\n".join(urllib2.urlopen(query_url).readlines())
      except HTTPError, e:
        print "server response code: " + str(e.code)
      
      info_list = []
      try:
        info_list.extend(json.loads(query_reply))
      except:
        # json decode failure, the site is probably down for maintenance... (danbooru.donmai.us, usually)
        # on this condition, we wait for a few minutes
        print "site down for maintenance, wait for 2 minutes, on %s" % time.asctime()
        print "when resumed, will restart from page 1"
        time.sleep(120) # wait 2 minutes
        page_id = 1
        continue
      
      if len(info_list) == 0:
        print "no more images"
        print "restart downloading from page 1"
        page_id = 1
        continue
      
      for info in info_list:
        try:
          id_in_set = int(info[u"id"])
          if db_image_in_black_list(image_set_base, id_in_set):
            print "[skip] '%s %d' is in black list" % (image_set_base, id_in_set)
            continue
          if db_get_image_by_md5(info[u"md5"]) != None:
            print "[skip] '%s %d' has duplicated md5" % (image_set_base, id_in_set)
            continue
          if info.has_key(u"sample_file_size"):
            sample_file_size = info[u"sample_file_size"]
          else:
            sample_file_size = 0
          if util_download_danbooru_image(image_set_base, id_in_set, info[u"sample_url"], sample_file_size):
            image_url = "http://" + urllib2.quote(info[u"sample_url"][7:])
            image_ext = image_url[image_url.rfind("."):]
            download_fpath = tmp_folder + os.path.sep + image_set_base + os.path.sep + str(id_in_set) + image_ext
            db_add_image(download_fpath, image_set_base, id_in_set)
            db_commit()
            os.remove(download_fpath)
          db_set_image_tags(image_set_base, id_in_set, info[u"tags"].split())
          db_commit()
          if info.has_key(u"file_size"):
            highres_file_size = info[u"file_size"]
          else:
            highres_file_size = 0
          if highres_file_size != 0 and highres_file_size == sample_file_size:
            print "[skip] highres file is same as sample file"
            continue
          if util_download_danbooru_image(image_set_highres, id_in_set, info[u"file_url"], highres_file_size, info[u"md5"]):
            image_url = "http://" + urllib2.quote(info[u"file_url"][7:])
            image_ext = image_url[image_url.rfind("."):]
            download_fpath = tmp_folder + os.path.sep + image_set_highres + os.path.sep + str(id_in_set) + image_ext
            db_add_image(download_fpath, image_set_highres, id_in_set)
            db_commit()
            os.remove(download_fpath)
          db_set_image_tags(image_set_highres, id_in_set, info[u"tags"].split())
          db_commit()
        except:
          traceback.print_exc()
          time.sleep(1)
      
    except:
      traceback.print_exc()
      time.sleep(1)

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
      try:
        if db_add_image(fpath, image_set, id_in_set) == True:
          if os.path.exists(info_fpath):
            info_file = open(info_fpath)
            json_ret = json.loads(info_file.read())
            info_file.close()
            db_set_image_tags(image_set, id_in_set, json_ret[u"tags"].split())
      except:
        traceback.print_exc()
        time.sleep(1)
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
    # Interactive mode.
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

def moe_info_album():
  if len(sys.argv) == 3:
    img_list = db_get_album_images(sys.argv[2])
    for img in img_list:
      if img[4] == None:
        rating = "?"
      else:
        rating = str(img[4])
      print "%-10s %6d%s %s %s" % (img[1], img[2], img[5], rating, img[3])
    print "<%d images>" % len(img_list)
  else:
    print "usage: moe info-album <album-name>"

def moe_import_album():
  print "input an empty line to quit"
  while True:
    input = raw_input("album file: ")
    if input == "":
      break
    album_name = os.path.splitext(os.path.split(input)[1])[0]
    f = open(input)
    db_add_album(album_name)
    for line in f.readlines():
      line = line.strip()
      splt = line.split()
      image_set = splt[0]
      id_in_set = int(splt[1])
      db_add_album_image(album_name, image_set, id_in_set)
    f.close()
    db_commit()

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
      if file.lower().endswith(".rank.txt"):
        # A hack for ranking files generated by my PSP toolkit.
        image_id = int(os.path.splitext(file)[0].split(".")[0].split("_")[-1])
      else:
        image_id = int(os.path.splitext(file)[0])
      f = open(fpath)
      rating_text = f.read()
      f.close()
      rating_value = None
      if rating_text == "delete":
        rating_value = 0
      elif rating_text == "soso":
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

def moe_mirror_danbooru():
  util_mirror_danbooru_site("http://danbooru.donmai.us")

def moe_mirror_konachan():
  util_mirror_danbooru_site("http://konachan.com")

def moe_mirror_moe_imouto():
  util_mirror_danbooru_site("http://moe.imouto.org")

def moe_mirror_nekobooru():
  util_mirror_danbooru_site("http://nekobooru.net")

def moe_cleanup():
  # Delete images with rating 0
  c = DB_CONN.cursor()
  c.execute("select set_name, id_in_set from images where rating = 0")
  ret_all = c.fetchall()
  for ret in ret_all:
    db_del_image(ret[0], ret[1])
  # TODO delete empty folder, compact black list, delete thumbs.db, delete tags with 0 images, vacuum the db

def moe_find_ophan():
  images_root = db_get_setting("images_root")
  if len(sys.argv) == 3:
    image_set = sys.argv[2]
  else:
    image_set = raw_input("image set: ")
  
  ophan_list = []
  def find_ophan_walker(ophan_list, dir, files):
    print "working in dir: %s" % dir
    for file in files:
      if util_is_image(file) == False:
        continue
      id_in_set = int(os.path.splitext(os.path.split(file)[1])[0])
      if db_get_image_by_id_in_set(image_set, id_in_set) == None:
        ophan_list += dir + os.path.sep + file,
  
  os.path.walk(images_root + os.path.sep + image_set, find_ophan_walker, ophan_list)
  for ophan in ophan_list:
    print ophan
  print "<%d ophan found>" % len(ophan_list)
  if len(ophan_list) > 0:
    print "what to do with those ohpans?"
    print "(d)elete them all"
    print "(m)ove them to a place"
    print "(w)rite to a listing file"
    choice = raw_input()
    if choice == "d":
      for ophan in ophan_list:
        os.remove(ophan)
    elif choice == "m":
      dest_dir = raw_input("move to dir: ")
      for ophan in ophan_list:
        shutil.move(ophan, dest_dir)
    elif choice == "w":
      fname = raw_input("name of file: ")
      f = open(fname, "w")
      for ophan in ophan_list:
        f.write(ophan + "\n")
      f.close()

def moe_help():
  print "moe.py: manage all my acg pictures"
  print "usage: moe.py <command>"
  print "available commands:"
  print ""
  print "  cleanup              delete images with rating 0, and compact the black list"
  print "  find-ophan           find images that are in images root, but not in database"
  print "  help                 display this info"
  print "  import               batch import pictures"
  print "  import-album         import existing album"
  print "  import-black-list    import existing black list file"
  print "  import-rating        import existing rating"
  print "  info                 display info about an image"
  print "  info-album           display info about an album"
  print "  mirror-all           mirror all known sites"
  print "  mirror-danbooru      mirror danbooru.donmai.us"
  print "  mirror-konachan      mirror konachan.com"
  print "  mirror-moe-imouto    mirror moe.imouto.org"
  print "  mirror-nekobooru     mirror nekobooru.com"
  print ""
  print "author: Santa Zhang (santa1987@gmail.com)"

if __name__ == "__main__":
  if len(sys.argv) == 1 or sys.argv[1] == "help":
    moe_help()
  elif sys.argv[1] == "cleanup":
    moe_cleanup()
  elif sys.argv[1] == "find-ophan":
    moe_find_ophan()
  elif sys.argv[1] == "import":
    moe_import()
  elif sys.argv[1] == "import-album":
    moe_import_album()
  elif sys.argv[1] == "import-black-list":
    moe_import_black_list()
  elif sys.argv[1] == "import-rating":
    moe_import_rating()
  elif sys.argv[1] == "info":
    moe_info()
  elif sys.argv[1] == "info-album":
    moe_info_album()
  elif sys.argv[1] == "mirror-danbooru":
    moe_mirror_danbooru()
  elif sys.argv[1] == "mirror-konachan":
    moe_mirror_konachan()
  elif sys.argv[1] == "mirror-moe-imouto":
    moe_mirror_moe_imouto()
  elif sys.argv[1] == "mirror-nekobooru":
    moe_mirror_nekobooru()
  else:
    print "command '%s' not understood, see 'moe help' for more info" % sys.argv[1]