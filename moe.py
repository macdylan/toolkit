#!/usr/bin/env python

# One script to manage all my pictures.
#
# Author: Santa Zhang (santa1987@gmail.com)
#

import sys
import os
import json
import hashlib
import sqlite3
import shutil
import urllib2
import re
import time
import socket
import traceback
import datetime
import urlparse
import random
from urllib2 import HTTPError
from select import *
from utils import *
from xml.etree import ElementTree

# Database models:
#
# images(id, set_name, id_in_set, md5, rating, ext, file_size)
# tags(id, name)
# images_has_tags(image_id, tag_id)
# albums(id, name, description)
# albums_has_images(album_id, image_id)
# black_list(set_name, start_id, end_id)

# The sqlite3 database which will be used.
SQLITE3_DB = None
DB_CONN = None

# read basic config data
g_image_root = None
g_tmp_folder = None

def my_dbexec(DB_CONN, sql):
    #print "[sql] %s" % sql
    DB_CONN.execute(sql)

def init_db_connection():
    global SQLITE3_DB
    global DB_CONN
    global g_image_root
    global g_tmp_folder

    SQLITE3_DB = get_config("db_file")

    # read basic config data
    g_image_root = get_config("image_root")
    g_tmp_folder = get_config("tmp_folder")

    if os.path.exists(SQLITE3_DB) == False:
        print "[warning] database file '%s' not exist, will create new file!" % SQLITE3_DB

    # Open the sqlite3 connection.
    DB_CONN = sqlite3.connect(SQLITE3_DB, 100)

    # Create tables if necessary.
    my_dbexec(DB_CONN, "create table if not exists images(id integer primary key, set_name text, id_in_set int, md5 text, rating int, ext text, file_size int)")
    my_dbexec(DB_CONN, "create table if not exists tags(id integer primary key, name text unique)")
    my_dbexec(DB_CONN, "create table if not exists tag_history(set_name text, id_in_set integer, new_version int)")
    my_dbexec(DB_CONN, "create table if not exists tag_history_head(set_name text, newest_version int)")
    my_dbexec(DB_CONN, "create table if not exists images_has_tags(image_id int, tag_id int)")
    my_dbexec(DB_CONN, "create table if not exists albums(id integer primary key, name text unique, description text)")
    my_dbexec(DB_CONN, "create table if not exists albums_has_images(album_id int, image_id int)")
    my_dbexec(DB_CONN, "create table if not exists black_list(set_name text, start_id int, end_id int)")
    my_dbexec(DB_CONN, "create table if not exists black_list_md5(md5 text)")

    # Create indexes if necessary.
    my_dbexec(DB_CONN, "create index if not exists i_images__file_size on images(file_size)")
    my_dbexec(DB_CONN, "create index if not exists i_images__md5 on images(md5)")
    my_dbexec(DB_CONN, "create index if not exists i_images__rating on images(rating)")
    my_dbexec(DB_CONN, "create index if not exists i_images__set_name__id_in_set on images(set_name, id_in_set)")

    my_dbexec(DB_CONN, "create index if not exists i_tags__name on tags(name)")

    my_dbexec(DB_CONN, "create index if not exists i_tag_history__set_name__id_in_set on tag_history(set_name, id_in_set)")

    my_dbexec(DB_CONN, "create index if not exists i_images_has_tags__tag_id__image_id on images_has_tags(tag_id, image_id)")
    my_dbexec(DB_CONN, "create index if not exists i_images_has_tags__image_id__tag_id on images_has_tags(image_id, tag_id)")

    my_dbexec(DB_CONN, "create index if not exists i_albums__name on albums(name)")

    my_dbexec(DB_CONN, "create index if not exists i_albums_has_images__album_id__image_id on albums_has_images(album_id, image_id)")

    my_dbexec(DB_CONN, "create index if not exists i_black_list__set_name__start_id on black_list(set_name, start_id)")

    my_dbexec(DB_CONN, "create index if not exists i_black_list_md5__md5 on black_list_md5(md5)")

def db_commit():
    DB_CONN.commit()

def db_image_in_black_list(image_set, id_in_set):
  c = DB_CONN.cursor()
  c.execute("select * from black_list where set_name = '%s' and start_id <= %d and %d <= end_id" % (image_set, id_in_set, id_in_set))
  if c.fetchone() != None:
    return True
  else:
    return False

def db_image_in_black_list_md5(md5):
  c = DB_CONN.cursor()
  c.execute("select * from black_list_md5 where md5 = '%s'" % md5)
  if c.fetchone() != None:
    return True
  else:
    return False

def db_add_image(fpath, image_set, id_in_set, final_id_list = None):
  try:
    db_add_image_real(fpath, image_set, id_in_set, final_id_list)
  except:
    print "[error] exception when adding image '%s'!" % fpath
    traceback.print_exc()
    time.sleep(1)
    return False

# add an image into the database
# if final_id_list is provided as an list, the added image's ('image_set', id_in_set) (or the duplicated image's) will be appended to the list
def db_add_image_real(fpath, image_set, id_in_set, final_id_list = None):
  print "[db.add] %s" % fpath
  bucket_name = util_get_bucket_name(id_in_set)
  dest_folder = g_image_root + os.path.sep + image_set + os.path.sep + bucket_name
  file_ext = os.path.splitext(fpath)[1]
  dest_file = dest_folder + os.path.sep + str(id_in_set) + file_ext
  md5 = util_md5_of_file(fpath)
  # Check if md5 already in db
  image_found = db_get_image_by_md5(md5)
  if image_found != None:
    if final_id_list != None:
      final_id_list += (image_found[1], image_found[2]),
    print "md5 duplicate: same as '%s %d'" % (image_found[1], image_found[2])
    return False
  else:
    if final_id_list != None:
      final_id_list += (image_set, id_in_set),
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
    c = DB_CONN.cursor()
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
  c = DB_CONN.cursor()
  c.execute("delete from images_has_tags where image_id = %d" % image_id)
  c.execute("delete from albums_has_images where image_id = %d" % image_id)
  c.execute("delete from images where id = %d" % image_id)
  db_commit()
  # Delete file after commit.
  fpath = g_image_root + os.path.sep + img[1] + os.path.sep + util_get_bucket_name(img[2]) + os.path.sep + str(img[2]) + img[5]
  print "[del] %s" % fpath
  try:
    os.remove(fpath)
  except:
    print "warning: file '%s' not found!" % fpath

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


def util_html_escape(text):
    html_escape_table = {
        '"' : "&quot;",
        "'" : "&apos;",
    }
    return "".join(html_escape_table.get(c, c) for c in text)


def db_add_album(album_name, desc = None):
    c = DB_CONN.cursor()
    c.execute("select * from albums where name = '%s'" % album_name)
    if c.fetchone() == None:
        write_log("[info] adding new album: %s" % album_name)
        if desc == None:
            c.execute("insert into albums(name) values('%s')" % album_name)
        else:
            c.execute("insert into albums(name, description) values('%s', \"%s\")" % (album_name, util_html_escape(desc)))
        db_commit()


def db_del_album(album_name):
    c = DB_CONN.cursor()
    try:
        c.execute("select id from albums where name = '%s'" % album_name)
        query_ret = c.fetchone()
        if query_ret == None:
            return
        album_id = int(query_ret[0])
        write_log("[info] removing album: %s, id = %d" % (album_name, album_id))
        c.execute("delete from albums_has_images where album_id = %d" % album_id)
        c.execute("delete from albums where name = '%s'" % album_name)
    except:
        traceback.print_exc()
        time.sleep(1)
    finally:
        db_commit()

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


def util_time_to_int(time_str):
    #util_time_to_int("Dec 20 2011, 06:07") # konachan, moe_imouto tag history
    #util_time_to_int("2011-12-19 23:51") # danbooru, nekobooru, tag history

    if "," in time_str:
        # konachan, moe_imouto tag history style
        time_str = time_str.replace("Jan", "01")
        time_str = time_str.replace("Feb", "02")
        time_str = time_str.replace("Mar", "03")
        time_str = time_str.replace("Apr", "04")
        time_str = time_str.replace("May", "05")
        time_str = time_str.replace("Jun", "06")
        time_str = time_str.replace("Jul", "07")
        time_str = time_str.replace("Aug", "08")
        time_str = time_str.replace("Sep", "09")
        time_str = time_str.replace("Oct", "10")
        time_str = time_str.replace("Nov", "11")
        time_str = time_str.replace("Dec", "12")
        tm_val = datetime.datetime.strptime(time_str, "%m %d %Y, %H:%M")
    elif "-" in time_str:
        # danbooru, nekobooru style
        tm_val = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    else:
        # exception! don't know how to handle
        raise ValueError("don't know how to parse: '%s'" % time_str)
    int_val = int(time.mktime(tm_val.timetuple()))
    return int_val


def util_int_to_time(time_int):
    return str(time.ctime(time_int))


def util_is_image(fname):
    return is_image(fname)

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
  images_root = g_image_root
  image_url = "http://" + urllib2.quote(image_url[7:])
  image_ext = image_url[image_url.rfind("."):]
  dest_image = images_root + os.path.sep + image_set + os.path.sep + util_get_bucket_name(id_in_set) + os.path.sep + str(id_in_set) + image_ext
  if os.path.exists(dest_image):
    db_add_image(dest_image, image_set, id_in_set)
    print "[skip] '%s %d' already downloaded" % (image_set, id_in_set)
    return False
  tmp_folder = g_tmp_folder
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

def util_mirror_danbooru_site_down_image(info_list, image_set_base, image_set_highres, tmp_folder):
  for info in info_list:
    try:
      id_in_set = int(info[u"id"])
      if db_image_in_black_list(image_set_base, id_in_set):
        print "[skip] '%s %d' is in black list" % (image_set_base, id_in_set)
        continue
      if db_image_in_black_list_md5(info[u"md5"]):
        print "[skip] '%s %d' is in black list (checked by md5)" % (image_set_base, id_in_set)
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
        if os.path.exists(download_fpath):
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
        if os.path.exists(download_fpath):
          os.remove(download_fpath)
      db_set_image_tags(image_set_highres, id_in_set, info[u"tags"].split())
      db_commit()
    except:
      traceback.print_exc()
      time.sleep(1)

def util_mirror_danbooru_site_html(site_url):
  SOCKET_TIMEOUT = 30
  socket.setdefaulttimeout(SOCKET_TIMEOUT)
  tmp_folder = g_tmp_folder
  print "mirroring danbooru-like site: %s (through html request)" % site_url

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
  # Check if need to start downloading from other pages.
  for i in range(len(sys.argv)):
    arg = sys.argv[i]
    if arg.startswith("--page="):
      page_id = int(arg[7:])
    elif arg == "-p":
      if i <= len(sys.argv) - 2:
        page_id = int(sys.argv[i + 1])
      else:
        print "Wrong parameters, please provide page number after '-p'!"
        return

  while True:
    try:
      query_url = site_url + ("/post?page=%d" % page_id)
      print "working on page %d (through html request)" % page_id

      # Go on to next page
      page_id += 1

      # After page 1000, the danbooru site only has html access, with prev/next links on each page
      if image_set_base == "danbooru" and page_id >= 1000:
        util_mirror_danbooru_site_ex(site_url)
        return

      try:
        page_src = "\n".join(urllib2.urlopen(query_url).readlines())
        json_matches = []

        idx = 0
        idx2 = 0
        while True:
          idx = page_src.find("Post.register(", idx2)
          if idx < 0:
            break
          idx2 = page_src.find("})", idx)
          one_match = page_src[(idx + 14):(idx2 + 1)]
          json_matches += one_match,

        query_reply = "[" + ",".join(json_matches) + "]"
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
        print "restart downloading from page 1 in 2 minutes (through html request)"
        page_id = 1
        time.sleep(120) # wait 2 minutes
        continue

      util_mirror_danbooru_site_down_image(info_list, image_set_base, image_set_highres, tmp_folder)

    except:
      traceback.print_exc()
      time.sleep(1)

def util_mirror_danbooru_site(site_url):
  SOCKET_TIMEOUT = 30
  socket.setdefaulttimeout(SOCKET_TIMEOUT)
  tmp_folder = g_tmp_folder
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
  # Check if need to start downloading from other pages.
  for i in range(len(sys.argv)):
    arg = sys.argv[i]
    if arg.startswith("--page="):
      page_id = int(arg[7:])
    elif arg == "-p":
      if i <= len(sys.argv) - 2:
        page_id = int(sys.argv[i + 1])
      else:
        print "Wrong parameters, please provide page number after '-p'!"
        return
  while True:
    try:
      query_url = site_url + ("/post/index.json?page=%d" % page_id)
      print "working on page %d" % page_id

      # Go on to next page
      page_id += 1

      # After page 1000, the danbooru site only has html access, with prev/next links on each page
      if image_set_base == "danbooru" and page_id >= 1000:
        util_mirror_danbooru_site_ex(site_url)
        return

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
        print "restart downloading from page 1 in 2 minutes"
        page_id = 1
        time.sleep(120) # wait 2 minutes
        continue

      util_mirror_danbooru_site_down_image(info_list, image_set_base, image_set_highres, tmp_folder)

    except:
      traceback.print_exc()
      time.sleep(1)

# mirror danbooru main site, which only has html access for page >= 1000
def util_mirror_danbooru_site_ex(site_url, before_id = None):
  SOCKET_TIMEOUT = 30
  socket.setdefaulttimeout(SOCKET_TIMEOUT)
  tmp_folder = g_tmp_folder

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

  tmp_folder = g_tmp_folder
  print "mirroring danbooru main site, after page 1000: %s" % site_url
  page_url = None
  while True:
    try:

      if page_url == None:
        if before_id == None:
          # by default, start from page 1000
          page_url = site_url + "/post/index.html?page=%d" % 1000
        else:
          page_url = site_url + "/post/index.html?before_id=%d" % before_id
      else:
        print "[page] %s" % page_url

      page_src = urllib2.urlopen(page_url).read()
      idx = 0
      idx2 = 0
      while True:
        idx = page_src.find("Post.register({", idx)
        if idx <= 0:
          break
        idx2 = page_src.find(");", idx)
        if idx2 <= 0:
          break
        json_data = page_src[(idx + 14):idx2]
        idx = idx2

        info_list = []
        try:
          info_list = [json.loads(json_data)]
        except:
          # json decode failure, the site is probably down for maintenance... (danbooru.donmai.us, usually)
          # on this condition, we wait for a few minutes
          print "site down for maintenance, wait for 2 minutes, on %s" % time.asctime()
          print "when resumed, will restart current page"
          time.sleep(120) # wait 2 minutes
          continue

        util_mirror_danbooru_site_down_image(info_list, image_set_base, image_set_highres, tmp_folder)

      new_page_url = None

      idx = page_src.find("/post?before_id=")
      if idx <= 0:
        print "[done] last page mirrored! restart job!"
        page_url = None
        continue
      idx2 = page_src.find('"', idx)
      if idx <= 0:
        print "[done] last page mirrored! restart job!"
        page_url = None
        continue

      new_page_url = site_url + page_src[idx:idx2]
      if new_page_url == page_url:
        print "[fatal] failed to find next page! restart job!"
        page_url = None
        continue
      page_url = new_page_url

    except:
      traceback.print_exc()
      time.sleep(1)


def util_execute(cmd):
    print "[cmd] %s" % cmd
    os.system(cmd)

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
      input = raw_input("image set or image id in set (empty to quit): ")
      if input == "":
        break
      if " " in input:
        splt = input.split()
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
        album_name = sys.argv[2]
        img_list = db_get_album_images(album_name)
        c = DB_CONN.cursor()
        c.execute("select description from albums where name = '%s'" % album_name)
        description = c.fetchone()[0]
        if description == None:
            print "no description available for album '%s'" % album_name
        else:
            print description
        print "----"
        for img in img_list:
            if img[4] == None:
                rating = "?"
            else:
                rating = str(img[4])
            print "%-18s %8d%s %s %s" % (img[1], img[2], img[5], rating, img[3])
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

def moe_create_album():
  print "WARNING: the images must be well-formed, better be exported images"
  album_name = raw_input("album name: ")
  folder = raw_input("image folder: ")
  db_add_album(album_name)
  for fn in os.listdir(folder):
    if not util_is_image(fn):
      continue
    main_fn = os.path.splitext(fn)[0]
    set_name, id_in_set = main_fn.split(" ")
    id_in_set = int(id_in_set)
    print set_name, " - ", id_in_set
    db_add_album_image(album_name, set_name, id_in_set)
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

def moe_import_rating_psp():
  image_set = raw_input("image set name: ")
  rating_folder = raw_input("ratings folder: ")

  has_highres = False
  c = DB_CONN.cursor()
  c.execute("select * from images where set_name = \"%s_highres\" limit 1" % image_set)
  ret_all = c.fetchall()
  if len(ret_all) != 0:
    has_highres = True

  def import_walker(arg, dir, files):
    print "working on dir: %s" % dir
    for file in files:
      if file.lower().endswith(".txt") == False:
        continue
      fpath = dir + os.path.sep + file
      if file.lower().endswith(".rank.txt"):
        # A hack for ranking files generated by my PSP toolkit.
        splt_name = os.path.splitext(file)[0].split(".")[0].split("_")[-1]
        if " " in splt_name:
          splt_name = splt_name.split()[-1]
        image_id = int(splt_name)
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
      c.execute("update images set rating = %d where set_name = '%s' and id_in_set = %d" % (rating_value, image_set, image_id))
      if has_highres:
        c.execute("update images set rating = %d where set_name = '%s_highres' and id_in_set = %d" % (rating_value, image_set, image_id))
    db_commit()

  os.path.walk(rating_folder, import_walker, None)

def moe_import_rating_dir():
  print "You need to run `find` in the rating directory exported by `export-big-unrated`,"
  print "and generated the output into a text file."
  print
  rating_txt = raw_input("fpath of the rating txt? ")
  f = open(rating_txt, "r")
  c = DB_CONN.cursor()
  for line in f.readlines():
    try:
      line = line.strip()
      if "/" in line:
        splt = line.split("/")
      else:
        splt = line.split("\\")
      rating, fname = splt[len(splt) - 2], splt[len(splt) - 1]
      fname = os.path.splitext(fname)[0]
      splt = fname.split(" ")
      if rating == "unrated":
        rating = "null"
      set_name, id_in_set = splt[0], int(splt[1])
      print set_name, id_in_set, "--> rating", rating
      if rating != "null":
        rating = "'%s'" % rating
      query = "update images set rating = %s where set_name = '%s' and id_in_set = %d;" % (rating, set_name, id_in_set)
      c.execute(query)
    except:
      traceback.print_exc()
  db_commit()
  f.close()

def moe_sync_rating_helper(set1, set2):
  c = DB_CONN.cursor()
  query = "select id_in_set, rating from images where set_name == '%s' and rating is not null;" % set1
  c.execute(query)
  ret_all = c.fetchall()
  set1_rating = {}
  for ret in ret_all:
    id_in_set, rating = ret
    set1_rating[id_in_set] = rating
  query = "select id_in_set, rating from images where set_name == '%s' and rating is not null;" % set2
  c.execute(query)
  ret_all = c.fetchall()
  set2_rating = {}
  for ret in ret_all:
    id_in_set, rating = ret
    set2_rating[id_in_set] = rating
  update_cnt = 0
  conflict_cnt = 0
  images_root = g_image_root
  for set1_id in set1_rating:
    set1_rt = set1_rating[set1_id]
    if set2_rating.has_key(set1_id) == False:
      query = "select * from images where set_name = '%s' and id_in_set = %d;" % (set2, set1_id)
      c.execute(query)
      if len(c.fetchall()) == 0:
        continue
      write_log("sync: %s: %d -> %s" % (set2, set1_id, set1_rt))
      # mirror rating from set1 to set2
      query = "update images set rating = '%s' where set_name = '%s' and id_in_set = %d;" % (set1_rt, set2, set1_id)
      c.execute(query)
      update_cnt += 1
    else:
      set2_rt = set2_rating[set1_id]
      if set2_rt < set1_rt:
        write_log("conflict: down rate %s: %d -> %s" % (set1, set1_id, set2_rt))
        conflict_cnt += 1
        query = "update images set rating = '%s' where set_name = '%s' and id_in_set = %d;" % (set2_rt, set1, set1_id)
        c.execute(query)
      elif set1_rt < set2_rt:
        write_log("conflict: down rate %s: %d -> %s" % (set2, set1_id, set1_rt))
        conflict_cnt += 1
        query = "update images set rating = '%s' where set_name = '%s' and id_in_set = %d;" % (set1_rt, set2, set1_id)
        c.execute(query)
  db_commit()
  print "done sync %s -> %s, %d updates, %d conflict" % (set1, set2, update_cnt, conflict_cnt)

def moe_sync_rating():
    moe_sync_rating_helper("nekobooru", "nekobooru_highres")
    moe_sync_rating_helper("nekobooru_highres", "nekobooru")
    moe_sync_rating_helper("konachan", "konachan_highres")
    moe_sync_rating_helper("konachan_highres", "konachan")
    moe_sync_rating_helper("moe_imouto", "moe_imouto_highres")
    moe_sync_rating_helper("moe_imouto_highres", "moe_imouto")
    moe_sync_rating_helper("danbooru", "danbooru_highres")
    moe_sync_rating_helper("danbooru_highres", "danbooru")

def moe_highres_rating():
  normal_set = raw_input("The normal res image set:")
  highres_set = raw_input("The highres res image set[%s_highres]:" % normal_set)
  if highres_set == "":
    highres_set = normal_set + "_highres"
  c = DB_CONN.cursor()
  c.execute("select id_in_set, rating from images where set_name = \"%s\" and rating is not NULL" % normal_set)
  ret_all = c.fetchall()
  print "mirroring %d ratings into highres image set" % len(ret_all)
  counter = 0
  for r in ret_all:
    c.execute("update images set rating = %d where id_in_set = %d and set_name = \"%s\"" % (r[1], r[0], highres_set))
    if counter % 100 == 0:
      print "%d done (of %d)" % (counter, len(ret_all))
      db_commit()
    counter += 1
  db_commit()

def moe_mirror_danbooru():
    util_mirror_danbooru_site("http://danbooru.donmai.us")

def moe_mirror_danbooru_1000():
    util_mirror_danbooru_site_ex("http://danbooru.donmai.us")

def moe_mirror_danbooru_before(before_id):
    util_mirror_danbooru_site_ex("http://danbooru.donmai.us", before_id)

def moe_mirror_konachan():
    util_mirror_danbooru_site("http://konachan.com")

def moe_mirror_moe_imouto():
    util_mirror_danbooru_site("http://moe.imouto.org")

def moe_mirror_moe_imouto_html():
    util_mirror_danbooru_site_html("http://moe.imouto.org")

def moe_mirror_konachan_html():
    util_mirror_danbooru_site_html("http://konachan.com")

def moe_mirror_nekobooru():
    util_mirror_danbooru_site("http://nekobooru.net")

def util_download_tu178_image(page_url, title, id_in_set):
  images_root = g_image_root
  image_set = "tu178"
  try:
    page_src = urllib2.urlopen(page_url).read()
    idx = page_src.find("d-box")
    idx = page_src.find("href=\"", idx)
    idx += 6
    idx2 = page_src.find("\"", idx)
    image_url = page_src[idx:idx2].split("?")[0]
    image_ext = image_url[image_url.rfind("."):]

    if db_image_in_black_list(image_set, id_in_set):
      print "[skip] '%s %d' is in black list" % (image_set, id_in_set)
      return

    dest_image = images_root + os.path.sep + image_set + os.path.sep
    dest_image += util_get_bucket_name(id_in_set) + os.path.sep + str(id_in_set) + image_ext
    if os.path.exists(dest_image):
      db_add_image(dest_image, image_set, id_in_set)
      tags = title,
      db_set_image_tags(image_set, id_in_set, tags)
      db_commit()
      print "[skip] '%s %d' already downloaded" % (image_set, id_in_set)
      return

    tmp_folder = g_tmp_folder
    util_make_dirs(tmp_folder + os.path.sep + image_set)
    try:
      download_fpath = tmp_folder + os.path.sep + image_set + os.path.sep + str(id_in_set) + image_ext
      print "[download] '%s %d'" % (image_set, id_in_set)
      image_data = urllib2.urlopen(image_url).read()
      download_file = open(download_fpath, "wb")
      download_file.write(image_data)
      download_file.close()

      db_add_image(download_fpath, image_set, id_in_set)
      tags = title,
      db_set_image_tags(image_set, id_in_set, tags)
      db_commit()
      if os.path.exists(download_fpath):
        os.remove(download_fpath)

    except:
      traceback.print_exc()
      time.sleep(1)

  except:
    traceback.print_exc()
    time.sleep(1)


def moe_mirror_tu178():
  SOCKET_TIMEOUT = 30
  socket.setdefaulttimeout(SOCKET_TIMEOUT)
  tmp_folder = g_tmp_folder
  print "mirroring tu.178.com!"

  # Start mirroring from page 1.
  page_id = 1
  # Check if need to start downloading from other pages.
  for i in range(len(sys.argv)):
    arg = sys.argv[i]
    if arg.startswith("--page="):
      page_id = int(arg[7:])
    elif arg == "-p":
      if i <= len(sys.argv) - 2:
        page_id = int(sys.argv[i + 1])
      else:
        print "Wrong parameters, please provide page number after '-p'!"
        return

  while True:
    try:
      query_url = "http://tu.178.com/?_per_page=1&_page_no=%d" % page_id
      print "working on page %d" % page_id

      # Go on to next page
      page_id += 1
      page_src = "\n".join(urllib2.urlopen(query_url).readlines())
      idx = 0
      while True:
        idx = page_src.find("a-img", idx)
        if idx == -1:
          break
        idx = page_src.find("href='", idx)
        idx += 6
        idx2 = page_src.find("' title", idx)
        sub_url = page_src[idx:idx2]
        idx2 += 9
        idx = page_src.find("\"", idx2)
        title_info = page_src[idx2:idx]
        idx = page_src.find("data_id='", idx)
        idx += 9
        idx2 = page_src.find("'", idx)
        id_in_set = int(page_src[idx:idx2])
        util_download_tu178_image(sub_url, title_info, id_in_set)
    except:
      traceback.print_exc()
      time.sleep(1)

def moe_mirror_all():
    if os.name == "nt":
        os.system("start moe.py mirror-danbooru")
        os.system("start moe.py mirror-konachan-html")
        os.system("start moe.py mirror-nekobooru")
        os.system("start moe.py mirror-moe-imouto-html")
        os.system("start moe.py mirror-tu178")
    else:
        print "Your download job will be running in 5 detached screen session"
        print "run `screen -r` to show them"
        print
        os.system("screen -dm ./moe.py mirror-danbooru")
        os.system("screen -dm ./moe.py mirror-konachan-html")
        os.system("screen -dm ./moe.py mirror-nekobooru")
        os.system("screen -dm ./moe.py mirror-moe-imouto-html")
        os.system("screen -dm ./moe.py mirror-tu178")
        os.system("screen -r")

def moe_cleanup():
    c = DB_CONN.cursor()
    # Get list of image sets.
    image_sets = []
    c.execute("select set_name from images group by set_name")
    ret_all = c.fetchall()
    for ret in ret_all:
        image_sets += ret[0],

    # Delete images with rating 0
    print "deleting images with rating of 0..."
    c.execute("select set_name, id_in_set, md5 from images where rating = 0")
    ret_all = c.fetchall()
    for ret in ret_all:
        set_name, id_in_set, md5 = ret
        c.execute("insert into black_list(set_name, start_id, end_id) values('%s', %d, %d)" % (set_name, id_in_set, id_in_set))
        c.execute("insert into black_list_md5(md5) values('%s')" % (md5))
        db_del_image(set_name, id_in_set)
        if set_name + "_highres" in image_sets:
            db_del_image(set_name + "_highres", id_in_set)

    # Remove empty folders.
    print "removing empty folders..."
    images_root = g_image_root
    def rm_empty_dir_walker(arg, dir, files):
        print "working in dir: %s" % dir
        for file in files:
            fpath = dir + os.path.sep + file
            if file.lower() == "thumbs.db":
                print "[rm] %s" % fpath
                os.remove(fpath)
        if len(os.listdir(dir)) == 0:
            print "[rmdir] %s" % dir
            os.rmdir(dir)
    for image_set in image_sets:
        os.path.walk(images_root + os.path.sep + image_set, rm_empty_dir_walker, None)

    # remove empty albums
    print "removing empty albums..."
    c.execute("select id, name from albums order by name")
    albums = c.fetchall()
    empty_albums = []
    for album in albums:
      id, name = album
      query_sql = "select count(*) from albums_has_images where album_id = %d" % id
      count = int(c.execute(query_sql).fetchone()[0])
      if count == 0:
          write_log("[info] found empty album: %s" % name)
          empty_albums += name,
    for album in empty_albums:
        try:
            db_del_album(album)
        except:
          traceback.print_exc()
          time.sleep(1)
    db_commit()

    # Shrink black list.
    print "shrinking black list..."
    internal_black_list = {}
    for image_set in image_sets:
        internal_black_list[image_set] = set()
    c.execute("select * from black_list")
    ret_all = c.fetchall()
    for ret in ret_all:
        set_name, start_id, end_id = ret
        for i in range(start_id, end_id + 1):
            internal_black_list[set_name].add(i)
        # Synchronize black list for "normal_res" and "high_res" image sets.
        if set_name.endswith("_highres"):
            normal_res_set_name = set_name[:-8]
            for i in range(start_id, end_id + 1):
                internal_black_list[normal_res_set_name].add(i)
        elif (set_name + "_highres") in image_sets:
            high_res_set_name = set_name + "_highres"
            for i in range(start_id, end_id + 1):
                internal_black_list[high_res_set_name].add(i)
    new_black_list = {}
    for image_set in image_sets:
        helper_list = list(internal_black_list[image_set])
        helper_list.sort()
        new_black_list[image_set] = []
        last_i = None
        new_start_id = None
        new_end_id = None
        for i in helper_list:
            if new_start_id == None:
                new_start_id = i
            elif i != last_i + 1:
                new_end_id = last_i
                new_black_list[image_set] += (new_start_id, new_end_id),
                new_start_id = i
                new_end_id = None
            last_i = i
        if new_start_id != None:
            new_end_id = last_i
            new_black_list[image_set] += (new_start_id, new_end_id),
    c.execute("delete from black_list")
    for image_set in image_sets:
        for item in new_black_list[image_set]:
            c.execute("insert into black_list(set_name, start_id, end_id) values('%s', %d, %d)" % (image_set, item[0], item[1]))
    db_commit()

    # Delete images in black list.
    print "deleting images in black list..."
    c.execute("select * from black_list")
    ret_all = c.fetchall()
    print "%d items in black list" % len(ret_all)
    counter = 0
    for ret in ret_all:
        set_name, start_id, end_id = ret
        for i in range(start_id, end_id + 1):
            db_del_image(set_name, i)
        counter += 1
        if counter % 10 == 0:
            print "%d items done (of %d)" % (counter, len(ret_all))
    print "%d items done" % counter


def moe_find_ophan():
  images_root = g_image_root
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

def moe_update_file_size():
  print "executing database query..."
  images_root = g_image_root
  c = DB_CONN.cursor()
  c.execute("select id, set_name, id_in_set, ext from images where file_size is null")
  ret_all = c.fetchall()
  print "%d files in total" % len(ret_all)
  counter = 0
  for ret in ret_all:
    counter += 1
    id, set_name, id_in_set, ext = ret
    image_file = images_root + os.path.sep + set_name + os.path.sep + util_get_bucket_name(id_in_set) + os.path.sep + str(id_in_set) + ext
    file_size = os.stat(image_file).st_size
    c.execute("update images set file_size = %d where id = %d" % (file_size, id))
    if counter % 100 == 0:
      print "%d files done" % counter
      db_commit()
  print "%d files done" % counter
  db_commit()

def moe_add():
  print "WARNING: adding images into moe db will REMOVE the source images!"
  print "WARNIGN: make sure you are just adding a copy of the source images!"
  image_set = raw_input("image set: ")
  image_set = image_set.strip()
  image_path = raw_input("image path (will be moved into library):\n")
  tags = raw_input("input tags (in one line, separate with space):\n")
  c = DB_CONN.cursor()
  c.execute("select max(id_in_set) from images where set_name = '%s'" % image_set)
  ret = c.fetchone()
  if ret == None:
    # First image in a new set.
    id_in_set = 1
  else:
    # Auto increase the image id_in_set.
    id_in_set = ret[0] + 1
  db_add_image(image_path, image_set, id_in_set)
  db_set_image_tags(image_set, id_in_set, tags.split())
  db_commit()

def moe_add_dir():
  print "WARNING: adding images into moe db will REMOVE the source images!"
  print "WARNIGN: make sure you are just adding a copy of the source images!"
  image_set = raw_input("image set: ")
  image_set = image_set.strip()
  image_dir = raw_input("dir path (will be moved into library):\n")
  image_album = raw_input("put the pictures into album (press ENTER to skip adding into album):\n")
  if image_album == "":
    image_album = None
  tags = raw_input("input tags (in one line, separate with space):\n")
  c = DB_CONN.cursor()
  c.execute("select max(id_in_set) from images where set_name = '%s'" % image_set)
  ret = c.fetchone()
  if ret == None:
    # First image in a new set.
    id_in_set = 1
  else:
    # Auto increase the image id_in_set.
    id_in_set = ret[0] + 1
  tag_list = tags.split()
  counter = 0
  list_images = []
  for file in os.listdir(image_dir):
    fpath = image_dir + os.path.sep + file
    if util_is_image(fpath) == False:
      continue
    db_add_image(fpath, image_set, id_in_set, list_images)
    db_set_image_tags(image_set, id_in_set, tag_list)
    id_in_set += 1
    counter += 1
    if counter % 100 == 0:
      db_commit()
  db_commit()
  # add images into album
  if image_album != None:
    db_add_album(image_album)
    counter = 0
    print "adding %d images into '%s'" % (len(list_images), image_album)
    for img in list_images:
      counter += 1
      if (counter % 20) == 0:
        print "%d done" % counter
      db_add_album_image(image_album, img[0], img[1])
    print "%d done" % counter
    db_commit()

def moe_add_dir_tree():
  print "WARNING: adding images into moe db will REMOVE the source images!"
  print "WARNIGN: make sure you are just adding a copy of the source images!"
  image_set = raw_input("image set: ")
  image_set = image_set.strip()
  image_dir = raw_input("dir path (will be moved into library):\n")
  image_album = raw_input("put the pictures into album (press ENTER to skip adding into album):\n")
  if image_album == "":
    image_album = None
  tags = raw_input("input tags (in one line, separate with space):\n")
  c = DB_CONN.cursor()
  c.execute("select max(id_in_set) from images where set_name = '%s'" % image_set)
  ret = c.fetchone()
  if ret == None or ret[0] == None:
    # First image in a new set.
    id_in_set = 1
  else:
    # Auto increase the image id_in_set.
    id_in_set = ret[0] + 1
  tag_list = tags.split()
  walker_args = [id_in_set, []]
  def add_dir_tree_walker(walker_args, dir, files):
    print "working in dir: %s" % dir
    for file in files:
      fpath = dir + os.path.sep + file
      if util_is_image(fpath) == False:
        continue
      db_add_image(fpath, image_set, walker_args[0], walker_args[1])
      db_set_image_tags(image_set, walker_args[0], tag_list)
      walker_args[0] += 1
    db_commit()
  os.path.walk(image_dir, add_dir_tree_walker, walker_args)
  # add images into album
  if image_album != None:
    db_add_album(image_album)
    list_images = walker_args[1]
    counter = 0
    print "adding %d images into '%s'" % (len(list_images), image_album)
    for img in list_images:
      counter += 1
      if (counter % 20) == 0:
        print "%d done" % counter
      db_add_album_image(image_album, img[0], img[1])
    print "%d done" % counter
    db_commit()

def moe_backup_db():
  db_file = get_config("db_file")
  backup_to = get_config("backup_to")
  db_main_fn, db_ext_fn = os.path.splitext(os.path.basename(db_file))
  tm_str = time.strftime("%y%m%d-%H%M%S", time.localtime())
  db_backup_file = os.path.join(backup_to, "%s.backup.%s%s" % (db_main_fn, tm_str, db_ext_fn))
  print "copying '%s' -> '%s'" % (db_file, db_backup_file)
  shutil.copyfile(db_file, db_backup_file)

  db_dump_file = os.path.join(backup_to, "%s.dump.%s.sql" % (db_main_fn, tm_str))
  print "dumping '%s' -> '%s'" % (db_file, db_dump_file)
  sqlite_bin = os.path.join(os.path.split(__file__)[0], "libexec", "sqlite3.exe")
  cmd = "%s \"%s\" .dump  > \"%s\"" % (sqlite_bin, db_file, db_dump_file)
  os.system(cmd)

  print "archiving..."
  db_dump_archive = os.path.join(backup_to, "%s.dump.%s.zip" % (db_main_fn, tm_str))
  if zipfile(db_dump_file, db_dump_archive) == True:
    os.remove(db_dump_file)

  backup_counter = 0
  dump_counter = 0
  for fn in os.listdir(backup_to):
    if fn.startswith("%s.backup." % db_main_fn) and fn.endswith(db_ext_fn):
      print fn
      backup_counter += 1
    if fn.startswith("%s.dump." % db_main_fn) and (fn.endswith(".zip") or fn.endswith(".sql")):
      print fn
      dump_counter += 1
  print "There are %d backup(s) and %d dump(s) of database file" % (backup_counter, dump_counter)

def util_backup_images(images, backup_type):
  image_root = get_config("image_root")
  backup_to = get_config("backup_to")
  counter = 0
  n_fail = 0
  n_skip = 0
  n_copy = 0
  for img in images:
    counter += 1
    set_name, id_in_set, ext_name = img
    main_fn = "%d%s" % (id_in_set, ext_name)
    src_folder = os.path.join(image_root, set_name, util_get_bucket_name(id_in_set))
    src_file = os.path.join(src_folder, main_fn)
    if os.path.exists(src_file) == False:
      write_log("[error] file not exist: %s" % src_file)
      n_fail += 1
    else:
      dst_folder = os.path.join(backup_to, set_name, util_get_bucket_name(id_in_set))
      util_make_dirs(dst_folder)
      dst_file = os.path.join(dst_folder, main_fn)
      if os.path.exists(dst_file) == True:
        if os.stat(src_file).st_size != os.stat(dst_file).st_size:
          write_log("file not consistent, different size: %s, %s" % (src_file, dst_file))
          raise Exception("file not consistent, different size: %s, %s" % (src_file, dst_file))
        n_skip += 1
      else:
        n_copy += 1
        shutil.copy(src_file, dst_file)
    if counter % 100 == 0:
      print "[backup:%s] %d of %d done (skip:%d, copy:%d, fail:%d)" % (backup_type, counter, len(images), n_skip, n_copy, n_fail)
  if counter % 100 != 0:
    print "[backup:%s] %d of %d done (skip:%d, copy:%d, fail:%d)" % (backup_type, counter, len(images), n_skip, n_copy, n_fail)

def util_cleanup_backup_folder(src_folder, dst_folder):
  src_fmap = {}
  dst_fmap = {}
  for fn in os.listdir(src_folder):
    src_fmap[fn] = 1
  for fn in os.listdir(dst_folder):
    dst_fmap[fn] = 1
  for fn in dst_fmap.keys():
    if src_fmap.has_key(fn) == False:
      backup_fpath = os.path.join(dst_folder, fn)
      write_log("remove backup entry: %s" % backup_fpath)
      if os.path.isdir(backup_fpath):
        shutil.rmtree(backup_fpath)
      else:
        os.remove(backup_fpath)

def util_cleanup_image_set(image_root, backup_to, set_name):
  # check level-1 folders
  src_folder = os.path.join(image_root, set_name)
  dst_folder = os.path.join(backup_to, set_name)
  print "checking level 1 folders of '%s'" % set_name
  util_cleanup_backup_folder(src_folder, dst_folder)
  # ok, now go on to level2 folders
  for fn in os.listdir(src_folder):
    fpath = os.path.join(src_folder, fn)
    dst_fpath = os.path.join(dst_folder, fn)
    if os.path.isdir(fpath) and os.path.isdir(dst_fpath):
      print "checking level 2 folder: %s\\%s" % (set_name, fn)
      util_cleanup_backup_folder(fpath, dst_fpath)

def moe_backup_cleanup():
  image_root = g_image_root
  backup_to = get_config("backup_to")
  image_sets = [
    "danbooru",
    "danbooru_highres",
    "konachan",
    "konachan_highres",
    "moe_imouto",
    "moe_imouto_highres",
    "mypic",
    "nekobooru",
    "nekobooru_highres"
  ]
  for set_name in image_sets:
    util_cleanup_image_set(image_root, backup_to, set_name)

def moe_backup_albums():
  print "backup albums"
  query = "select set_name, id_in_set, ext from albums_has_images, images where albums_has_images.image_id == images.id"
  c = DB_CONN.cursor()
  c.execute(query)
  ret = c.fetchall()
  print "[backup-albums] %d entries to backup" % len(ret)
  util_backup_images(ret, "albums")

def moe_backup_by_rating(rating):
  if rating == None:
    print "backup unrated images"
    query = "select set_name, id_in_set, ext from images where rating is null"
  else:
    print "backup images with rating %d" % rating
    query = "select set_name, id_in_set, ext from images where rating=%d" % rating
  c = DB_CONN.cursor()
  c.execute(query)
  ret = c.fetchall()
  if rating == None:
    print "[backup-unrated] %d entries to backup" % len(ret)
    util_backup_images(ret, "unrated")
  else:
    print "[backup-rate-%d] %d entries to backup" % (rating, len(ret))
    util_backup_images(ret, "rate-%d" % rating)


def moe_backup_all():
  print "Phase 1: backup db"
  moe_backup_db()
  print "Phase 2: backup albums"
  moe_backup_albums()
  print "Phase 3: backup rated images"
  moe_backup_by_rating(3)
  moe_backup_by_rating(2)
  moe_backup_by_rating(1)
  print "Phase 4: backup unrated imags"
  moe_backup_by_rating(None)
  moe_backup_cleanup()

def util_check_image_set_md5(image_root, md5_bin, set_name):
  print "checking md5 of image set: '%s'" % set_name
  n_pass = 0
  n_fail = 0
  set_folder = os.path.join(image_root, set_name)
  for folder_name in os.listdir(set_folder):
    fpath = os.path.join(set_folder, folder_name)
    if os.path.isdir(fpath):
      folder_start, folder_stop = folder_name.split("-")
      print "[check-md5] %s %s-%s" % (set_name, folder_start, folder_stop)
      c = DB_CONN.cursor()
      query = "select md5, id_in_set, ext from images where set_name=\"%s\" and %s <= id_in_set and id_in_set <= %s" % (set_name, folder_start, folder_stop)
      c.execute(query)
      ret = c.fetchall()
      folder_path = os.path.join(image_root, set_name, folder_name)
      md5_fn = os.path.join(folder_path, "md5sum.txt")
      f = open(md5_fn, "w")
      try:
        for e in ret:
          md5, id_in_set, ext = e
          f.write("%s %s%s\n" % (md5, id_in_set, ext))
      finally:
        f.close()
      if os.path.exists(md5_fn):
        try:
          pipe = os.popen("%s %s" % (md5_bin, folder_path))
          for line in pipe.readlines():
            line = line.strip()
            if line.startswith("pass"):
              n_pass += 1
            elif line.startswith("fail"):
              n_fail += 1
              write_log("[error] md5sum failed: '%s'" % line)
          pipe.close()
        finally:
          os.remove(md5_fn)
      print "%d passed, %d failed" % (n_pass, n_fail)

def moe_check_md5():
  print "usage: moe.py check-md5 [set_name]"
  image_root = g_image_root
  image_sets = [
    "danbooru",
    "danbooru_highres",
    "konachan",
    "konachan_highres",
    "moe_imouto",
    "moe_imouto_highres",
    "mypic",
    "nekobooru",
    "nekobooru_highres"
  ]
  md5_bin = os.path.join(os.path.split(__file__)[0], "libexec", "moe-check-md5.exe")
  if os.path.exists(md5_bin) == False:
    print "md5 check helper is not found: %s" % md5_bin
    return
  if len(sys.argv) > 2:
    set_name = sys.argv[2]
    util_check_image_set_md5(image_root, md5_bin, set_name)
  else:
    for set_name in image_sets:
      util_check_image_set_md5(image_root, md5_bin, set_name)

def moe_export():
  image_set = raw_input("image set: ")
  id_in_set_range = raw_input("image id range (eg: 1223 or 1223-1225): ")
  if "-" in id_in_set_range:
    splt = id_in_set_range.split("-")
    id_low = int(splt[0])
    id_high = int(splt[1])
  else:
    id_low = id_high = int(id_in_set_range)
  print "Image rating:"
  print "0: not rated, 1: so-so, 2: good, 3: excellent"
  print "eg: 0123 means all images, 23 means good & excellent images"
  rating_range = raw_input("image rating (press ENTER for all images): ")
  if rating_range == "":
    rating_range = "0123"
  rating_sql = ""
  for c in rating_range:
    if rating_sql != "":
      rating_sql += " or "
    if c == "0":
      rating_sql += "rating is null"
    else:
      rating_sql += "rating = %s" % c
  export_dir = raw_input("export to folder: ")
  images_root = g_image_root
  query_sql = "select * from images where set_name = '%s' and %d <= id_in_set and id_in_set <= %d and (%s)" % (image_set, id_low, id_high, rating_sql)
  c = DB_CONN.cursor()
  c.execute(query_sql)
  ret_all = c.fetchall()
  print "%d images to be exported" % len(ret_all)
  counter = 0
  for ret in ret_all:
    counter += 1
    id_in_set, ext = ret[2], ret[5]
    img_path = images_root + os.path.sep + image_set + os.path.sep + util_get_bucket_name(id_in_set) + os.path.sep + str(id_in_set) + ext
    dest_file = export_dir + os.path.sep + image_set + " " + str(id_in_set) + ext
    shutil.copyfile(img_path, dest_file)
    if counter % 20 == 0:
      print "%d images done" % counter
  print "%d images done" % counter

def moe_export_psp():
  print "WARNING: make sure Imagick 'convert' is in PATH"
  print "WARNING: exported images will be converted to fit in box of 480x480"
  image_set = raw_input("image set: ")
  id_in_set_range = raw_input("image id range (eg: 1223 or 1223-1225): ")
  if "-" in id_in_set_range:
    splt = id_in_set_range.split("-")
    id_low = int(splt[0])
    id_high = int(splt[1])
  else:
    id_low = id_high = int(id_in_set_range)
  print "Image rating:"
  print "0: not rated, 1: so-so, 2: good, 3: excellent"
  print "eg: 0123 means all images, 23 means good & excellent images"
  rating_range = raw_input("image rating (press ENTER for all images): ")
  if rating_range == "":
    rating_range = "0123"
  rating_sql = ""
  for c in rating_range:
    if rating_sql != "":
      rating_sql += " or "
    if c == "0":
      rating_sql += "rating is null"
    else:
      rating_sql += "rating = %s" % c
  export_dir = raw_input("export to folder: ")
  images_root = g_image_root
  query_sql = "select * from images where set_name = '%s' and %d <= id_in_set and id_in_set <= %d and (%s)" % (image_set, id_low, id_high, rating_sql)
  c = DB_CONN.cursor()
  c.execute(query_sql)
  ret_all = c.fetchall()
  print "%d images to be exported" % len(ret_all)
  counter = 0
  for ret in ret_all:
    counter += 1
    id_in_set, ext = ret[2], ret[5]
    img_path = images_root + os.path.sep + image_set + os.path.sep + util_get_bucket_name(id_in_set) + os.path.sep + str(id_in_set) + ext
    dest_dir = export_dir + os.path.sep + image_set + os.path.sep + util_get_bucket_name(id_in_set)
    util_make_dirs(dest_dir)
    dest_file = dest_dir + os.path.sep + str(id_in_set) + ".jpg"
    cmd = 'convert -flatten -resize 480x480 "%s" "%s"' % (img_path, dest_file)
    util_execute(cmd)
    if counter % 20 == 0:
      print "%d images done" % counter
  print "%d images done" % counter

def moe_export_album():
    album_name = raw_input("album name: ")
    print "Image rating:"
    print "0: not rated, 1: so-so, 2: good, 3: excellent"
    print "eg: 0123 means all images, 23 means good & excellent images"
    rating_range = raw_input("image rating (press ENTER for all images): ")
    if rating_range == "":
        rating_range = "0123"
    rating_sql = ""
    for c in rating_range:
        if rating_sql != "":
            rating_sql += " or "
        if c == "0":
            rating_sql += "rating is null"
        else:
            rating_sql += "rating = %s" % c
    export_dir = raw_input("export to folder: ")
    # write description.txt
    c = DB_CONN.cursor()
    query_sql = "select description from albums where albums.name = '%s'" % album_name
    c.execute(query_sql)
    ret_all = c.fetchall()
    album_description = ret_all[0][0]
    if album_description == None:
        print "no description, not creating a description.txt"
    else:
        f = open(os.path.join(export_dir, "description.txt"), "w")
        f.write(album_description)
        f.close()
    # copy images
    images_root = g_image_root
    query_sql = "select set_name, id_in_set, ext, rating from albums, albums_has_images, images where albums.name = '%s' and albums.id = albums_has_images.album_id and images.id = albums_has_images.image_id and (%s)" % (album_name, rating_sql)
    c.execute(query_sql)
    ret_all = c.fetchall()
    print "%d images to be exported" % len(ret_all)
    counter = 0
    for ret in ret_all:
        counter += 1
        image_set, id_in_set, ext = ret[0], ret[1], ret[2]
        img_path = images_root + os.path.sep + image_set + os.path.sep + util_get_bucket_name(id_in_set) + os.path.sep + str(id_in_set) + ext
        dest_file = export_dir + os.path.sep + image_set + " " + str(id_in_set) + ext
        shutil.copyfile(img_path, dest_file)
        if counter % 20 == 0:
            print "%d images done" % counter
    print "%d images done" % counter

def moe_export_big_unrated():
  n_images = raw_input("How many images to be exported? [default 1000] ")
  if n_images == "":
    n_images = 1000
  else:
    n_images = int(n_images)
  c = DB_CONN.cursor()
  query_sql = "select set_name, id_in_set, ext, file_size from images where rating is null order by file_size desc limit %d" % n_images
  c.execute(query_sql)
  ret_all = c.fetchall()
  total_sz = 0
  for ret in ret_all:
    image_set, id_in_set, ext, fsize = ret[0], ret[1], ret[2], ret[3]
    total_sz += fsize
  print "%d images, total size %s" % (len(ret_all), pretty_fsize(total_sz))
  outdir = raw_input("Output dir? ")
  util_make_dirs(os.path.join(outdir, "unrated"))
  util_make_dirs(os.path.join(outdir, "0"))
  util_make_dirs(os.path.join(outdir, "1"))
  util_make_dirs(os.path.join(outdir, "2"))
  util_make_dirs(os.path.join(outdir, "3"))
  done_sz = 0
  counter = 0
  images_root = g_image_root
  for ret in ret_all:
    counter += 1
    image_set, id_in_set, ext, fsize = ret[0], ret[1], ret[2], ret[3]
    img_path = images_root + os.path.sep + image_set + os.path.sep + util_get_bucket_name(id_in_set) + os.path.sep + str(id_in_set) + ext
    dest_file = os.path.join(outdir, "unrated", image_set + " " + str(id_in_set) + ext)
    done_sz += fsize
    print "(%d/%d, %s/%s) %s --> %s" % (counter, len(ret_all), pretty_fsize(done_sz), pretty_fsize(total_sz), img_path, dest_file)
    try:
      shutil.copyfile(img_path, dest_file)
    except:
      traceback.print_exc()
      if os.path.exists(img_path) == False:
        db_del_image(image_set, id_in_set)

def moe_export_sql():
    query_sql = raw_input("your sql query? (no trailing ';') ")
    if ";" in query_sql:
        raise ValueError("no ';' allowed in sql query!")
    query_sql = "select set_name, id_in_set, ext, file_size from (%s)" % query_sql
    c = DB_CONN.cursor()
    c.execute(query_sql)
    ret_all = c.fetchall()
    total_sz = 0
    for ret in ret_all:
        image_set, id_in_set, ext, fsize = ret[0], ret[1], ret[2], ret[3]
        total_sz += fsize
    print "%d images, total size %s" % (len(ret_all), pretty_fsize(total_sz))
    outdir = raw_input("Output dir? ")
    util_make_dirs(os.path.join(outdir, "unrated"))
    util_make_dirs(os.path.join(outdir, "0"))
    util_make_dirs(os.path.join(outdir, "1"))
    util_make_dirs(os.path.join(outdir, "2"))
    util_make_dirs(os.path.join(outdir, "3"))
    done_sz = 0
    counter = 0
    images_root = g_image_root
    for ret in ret_all:
        counter += 1
        image_set, id_in_set, ext, fsize = ret[0], ret[1], ret[2], ret[3]
        img_path = images_root + os.path.sep + image_set + os.path.sep + util_get_bucket_name(id_in_set) + os.path.sep + str(id_in_set) + ext
        dest_file = os.path.join(outdir, "unrated", image_set + " " + str(id_in_set) + ext)
        done_sz += fsize
        print "(%d/%d, %s/%s) %s --> %s" % (counter, len(ret_all), pretty_fsize(done_sz), pretty_fsize(total_sz), img_path, dest_file)
        shutil.copyfile(img_path, dest_file)

def moe_list_albums():
    print "Loading data..."
    c = DB_CONN.cursor()
    c.execute("select id, name from albums order by name")
    albums = c.fetchall()
    for album in albums:
        id, name = album
        query_sql = "select count(*) from albums_has_images where album_id = %d" % id
        count = int(c.execute(query_sql).fetchone()[0])
        try:
            print "%s  (id=%d, count=%d)" % (name, id, count)
        except:
            traceback.print_exc()


def util_pool_get_max_page(pool_api):
    max_page = 1
    query_url = pool_api
    page_src = "\n".join(map(str.strip, urllib2.urlopen(query_url).readlines()))
    idx = page_src.find("<div class=\"pagination\">")
    idx2 = page_src.find("</div>", idx)
    paging_code = page_src[idx:idx2]
    idx = 0
    while True:
        idx = paging_code.find("?page=", idx)
        if idx < 0:
            break
        idx2 = paging_code.find('"', idx)
        page_id = int(paging_code[idx + 6:idx2])
        if page_id > max_page:
            max_page = page_id
        idx = idx2
    return max_page


def util_pool_mirror(pool_index, set_name, pool_name, pool_size):
    print "mirror pool '%s' from '%s' (set=%s), size=%d" % (pool_name, pool_index, set_name, pool_size)
    # first remove the album, then add the album
    album_name = util_html_escape("[pool_%s] %s" % (set_name, pool_name))
    try:
        print "album_name = %s" % album_name
    except:
        pass
    db_del_album(album_name)
    page_id = 1
    desc = None
    while True:
        try:
            query_url = pool_index + (".xml?page=%d" % page_id)
            print "querying xml page: %s" % query_url
            page_src = "\n".join(map(str.strip, urllib2.urlopen(query_url).readlines()))
            xml = ElementTree.XML(page_src)
            if desc == None:
                desc = xml.find("description").text
                print "---- begin description ----"
                try:
                    print desc
                except:
                    pass
                print "---- end description ----"

            db_add_album(album_name, desc)
            posts = xml.findall("posts/post")

            for post in posts:
                id_in_set = int(post.attrib["id"])
                ret1 = db_add_album_image(album_name, set_name, id_in_set)
                # also add highres image
                ret2 = db_add_album_image(album_name, set_name + "_highres", id_in_set)
                if ret1 or ret2:
                    print "post = %s %d, add success" % (set_name, id_in_set)
                else:
                    print "post = %s %d, add failure!" % (set_name, id_in_set)
            db_commit()
            if len(posts) == 0:
                break
            page_id += 1
        except:
            traceback.print_exc()
            time.sleep(1)
            break

    try:
        print "finished mirroring pool %s" % pool_name
    except:
        pass


def util_pool_fetch_page_directory(query_url, set_name):
    print "fetching pool directory %s" % query_url
    page_src = "\n".join(map(str.strip, urllib2.urlopen(query_url).readlines()))
    idx = 0
    urlsplt = urlparse.urlparse(query_url)
    pool_info_list = []
    while True:
        idx = page_src.find("/pool/show/", idx)
        if idx < 0:
            break
        idx2 = page_src.find('"', idx)
        pool_index_url = page_src[idx:idx2]
        pool_index_url = urlsplt.scheme + "://" + urlsplt.netloc + pool_index_url

        idx = page_src.find(">", idx2) + 1
        idx2 = page_src.find("<", idx)
        pool_name = page_src[idx:idx2]

        idx = page_src.find("<td>", idx2) + 1
        idx2 = page_src.find("</td>", idx) + 1
        idx = page_src.find("<td>", idx2) + 4
        idx2 = page_src.find("</td>", idx)

        pool_size = int(page_src[idx:idx2])

        print "found a pool at '%s'" % pool_index_url

        pool_info_list += (pool_index_url, pool_name, pool_size),
        idx = idx2

    for (pool_index_url, pool_name, pool_size) in pool_info_list:
        util_pool_mirror(pool_index_url, set_name, pool_name, pool_size)


def moe_update_pool(pool_api, set_name):
    print "updating pools from image set '%s', query api is '%s'" % (set_name, pool_api)
    max_page = util_pool_get_max_page(pool_api)
    print "there is %d pages of pools" % max_page
    for page_id in range(1, max_page + 1):
        try:
            query_url = pool_api + ("?page=%d" % page_id)
            util_pool_fetch_page_directory(query_url, set_name)
        except:
            traceback.print_exc()
            time.sleep(1)
    print "finished updating pools of set '%s'" % set_name


def util_update_tags_from_page(post_url, set_name, id_in_set):
    try:
        print "update tags of '%s %d' => %s" % (set_name, id_in_set, post_url)
        page_src = "\n".join(map(str.strip, urllib2.urlopen(post_url).readlines()))
        idx = page_src.find('<div id="note-container">')
        if idx < 0:
            print "*** failed to parse page: " + post_url
            return False
        idx = page_src.find('<img alt="', idx)
        if idx < 0:
            print "*** failed to parse page: " + post_url
            return False
        idx += 10

        idx2 = page_src.find('"', idx)
        tags = page_src[idx:idx2].split()
        print "tags:", tags

        db_set_image_tags(set_name, id_in_set, tags)
        db_set_image_tags(set_name + "_highres", id_in_set, tags)

        c = DB_CONN.cursor()
        c.execute("delete from tag_history where set_name = '%s' and id_in_set = %d" % (set_name, id_in_set))
        db_commit()
        return True

    except:
        traceback.print_exc()
        time.sleep(1)
        return False



def moe_update_tag_history(post_api, set_name):
    if post_api.endswith("/") == False:
        post_api += '/'
    print "updating tag history (set_name='%s') from: %s" % (set_name, post_api)
    c = DB_CONN.cursor()
    c.execute("select count(*) from tag_history where set_name = '%s'" % set_name)
    query_ret = c.fetchone()
    n_update = int(query_ret[0])
    print "there are %d posts to be updated in set '%s'" % (n_update, set_name)

    if n_update == 0:
        return

    n_fetch_lim = 10000 # query limit
    while True:
        c.execute("select id_in_set from tag_history where set_name = '%s' limit %d" % (set_name, n_fetch_lim))
        query_ret = c.fetchall()
        update_list = []
        for ret in query_ret:
            update_list += int(ret[0]),
        if len(update_list) == 0:
            break
        random.shuffle(update_list) # shuffle the list, prevent some dead item getting accumulated to head of list
        n_success = 0
        for id_in_set in update_list:
            post_url = post_api + str(id_in_set)
            ret = util_update_tags_from_page(post_url, set_name, id_in_set)
            if ret == True:
                n_success += 1
        if n_success > 0:
            print "successfully updated tags on %d posts"
        else:
            print "*** failed to update some tags! quit now!"
            print "*** note that this might be caused by server side deletion of images"
            print "*** you may routinly cleanup tag_history to prevent this error message"
            break


def util_tag_history_get_max_page_type1(query_url):
    max_page = 1
    page_src = "\n".join(map(str.strip, urllib2.urlopen(query_url).readlines()))
    idx = page_src.find("<div class=\"pagination\">")
    idx2 = page_src.find("</div>", idx)
    paging_code = page_src[idx:idx2]
    idx = 0
    while True:
        idx = paging_code.find("?page=", idx)
        if idx < 0:
            break
        idx2 = paging_code.find('&', idx)
        page_id = int(paging_code[idx + 6:idx2])
        if page_id > max_page:
            max_page = page_id
        idx = idx2
    return max_page

def util_tag_history_parse_page_type1(page_src):
    update_list = [] # a list of tuples (id_in_set, update_time_int)

    idx = 0
    while True:
        idx = page_src.find('<td class="id"><a href="/post/show/', idx)
        if idx < 0:
            break
        idx += 35
        idx2 = page_src.find('"', idx)
        id_in_set = int(page_src[idx:idx2])

        idx = page_src.find("<td>", idx2)
        idx2 = page_src.find("</td>", idx)
        time_str = page_src[idx + 4:idx2]
        time_val_int = util_time_to_int(time_str)

        idx = idx2

        update_list += (id_in_set, time_val_int),

    return update_list

def util_tag_history_get_page_time_range_type1(query_api, page_id):
    query_url = query_api + ("&page=%d" % page_id)
    page_src = "\n".join(map(str.strip, urllib2.urlopen(query_url).readlines()))
    update_list = util_tag_history_parse_page_type1(page_src)

    now_tick = int(time.mktime(time.localtime()))
    max_time = -1
    min_time = now_tick + 86400 + 1 # prevent time zone problems

    for id_in_set, update_time_int in update_list:
        if update_time_int > max_time:
            max_time = update_time_int
        if update_time_int < min_time:
            min_time = update_time_int

    return (min_time, max_time)


def db_tag_history_get_head_version(set_name):
    head_version = 0
    c = DB_CONN.cursor()
    c.execute("select newest_version from tag_history_head where set_name = '%s'" % set_name)
    query_ret = c.fetchone()
    if query_ret != None:
        head_version = int(query_ret[0])
    return head_version


def db_tag_history_set_head_version(set_name, head_version):
    c = DB_CONN.cursor()
    c.execute("select newest_version from tag_history_head where set_name = '%s'" % set_name)
    query_ret = c.fetchone()
    if query_ret == None:
        c.execute("insert into tag_history_head(set_name, newest_version) values('%s', %d)" % (set_name, head_version))
    else:
        c.execute("update tag_history_head set newest_version = %d where set_name = '%s'" % (head_version, set_name))
    db_commit()


def db_update_image_tag_version(set_name, id_in_set, new_version):
    if db_image_in_black_list(set_name, id_in_set):
        print "'%s %d' is in black list" % (set_name, id_in_set)
        return False

    c = DB_CONN.cursor()
    c.execute("select new_version from tag_history where set_name = '%s' and id_in_set = %d" % (set_name, id_in_set))
    query_ret = c.fetchone()
    if query_ret != None:
        old_version = int(query_ret[0])
        if new_version > old_version:
            c.execute("update tag_history set new_version = %d where set_name = '%s' and id_in_set = %d" % (new_version, set_name, id_in_set))
            return True
        else:
            return False
    else:
        c.execute("insert into tag_history(set_name, id_in_set, new_version) values('%s', %d, %d)" % (set_name, id_in_set, new_version))
        return True


def moe_fetch_tag_history_page_type1(query_url, set_name):
    print "fetching tag history from page: %s" % query_url
    page_src = "\n".join(map(str.strip, urllib2.urlopen(query_url).readlines()))
    update_list = util_tag_history_parse_page_type1(page_src)

    has_update = False
    max_ver = 0
    for id_in_set, new_version in update_list:
        if new_version > max_ver:
            max_ver = new_version
        ret = db_update_image_tag_version(set_name, id_in_set, new_version)
        if ret == True:
            print "update image version: %s %d => v%d" % (set_name, id_in_set, new_version)
            has_update = True

    if has_update:
        db_tag_history_set_head_version(set_name, max_ver)
    db_commit()


def moe_fetch_tag_history_type1(query_api, set_name):
    print "fetching tag history from type1 site: %s => %s" % (query_api, set_name)
    max_page = util_tag_history_get_max_page_type1(query_api)
    print "there are %d pages of tag history" % max_page

    head_version = db_tag_history_get_head_version(set_name)
    print "current head version in '%s' is %d" % (set_name, head_version)

    first_page_version_range = util_tag_history_get_page_time_range_type1(query_api, 1)
    last_page_version_range = util_tag_history_get_page_time_range_type1(query_api, max_page)

    print "version on first page (1) is %d ~ %d" % (first_page_version_range[0], first_page_version_range[1])
    print "version on last page (%d) is %d ~ %d" % (max_page, last_page_version_range[0], last_page_version_range[1])

    page_id = max_page # by default, start from last page
    high_page_range = last_page_version_range
    low_page_range = first_page_version_range
    if head_version > first_page_version_range[1] + 86400 + 1:
        page_id = 0 # no need to mirror
    elif head_version >= last_page_version_range[0]:
        # bisect to proper page and restart mirroring
        high_page_id = max_page
        low_page_id = 1
        while low_page_id + 1 < high_page_id:
            mid_page_id = (high_page_id + low_page_id) / 2
            mid_page_range = util_tag_history_get_page_time_range_type1(query_api, mid_page_id)
            print "version on page %d is %d ~ %d" % (mid_page_id, mid_page_range[0], mid_page_range[1])
            if head_version <= mid_page_range[1]:
                low_page_id = mid_page_id
                low_page_range = mid_page_range
            else: # mid_page_range[1] < head_version
                high_page_id = mid_page_id
                high_page_range = mid_page_range
        page_id = high_page_id

    if page_id > 0:
        print "start fetching from page %d, version %d ~ %d" % (page_id, high_page_range[0], high_page_range[1])
        while page_id > 0:
            query_url = query_api + ("&page=%d" % page_id)
            moe_fetch_tag_history_page_type1(query_url, set_name)
            page_id -= 1

    print "fetched all tag history on site '%s'" % query_api




def util_tag_history_get_max_page_type2(query_url):
    max_page = 1
    page_src = "\n".join(map(str.strip, urllib2.urlopen(query_url).readlines()))
    idx = page_src.find("<div class=\"pagination\">")
    idx2 = page_src.find("</div>", idx)
    paging_code = page_src[idx:idx2]
    idx = 0
    while True:
        idx = paging_code.find("?page=", idx)
        if idx < 0:
            break
        idx2 = paging_code.find('"', idx)
        page_id = int(paging_code[idx + 6:idx2])
        if page_id > max_page:
            max_page = page_id
        idx = idx2
    return max_page


def util_tag_history_parse_page_type2(page_src):
    update_list = [] # a list of tuples (id_in_set, update_time_int)

    idx = 0
    while True:
        idx = page_src.find('<td><a href="/post/show/', idx)
        if idx < 0:
            break
        idx += 24
        idx2 = page_src.find('"', idx)
        id_in_set = int(page_src[idx:idx2])

        idx = page_src.find("<td>", idx2)
        idx2 = page_src.find("</td>", idx)
        time_str = page_src[idx + 4:idx2]
        time_val_int = util_time_to_int(time_str)

        idx = idx2

        update_list += (id_in_set, time_val_int),

    return update_list

def util_tag_history_get_page_time_range_type2(query_url):
    page_src = "\n".join(map(str.strip, urllib2.urlopen(query_url).readlines()))
    update_list = util_tag_history_parse_page_type2(page_src)

    now_tick = int(time.mktime(time.localtime()))
    max_time = -1
    min_time = now_tick + 86400 + 1 # prevent time zone problems

    for id_in_set, update_time_int in update_list:
        if update_time_int > max_time:
            max_time = update_time_int
        if update_time_int < min_time:
            min_time = update_time_int

    return (min_time, max_time)


def moe_fetch_tag_history_page_type2(query_url, set_name):
    print "fetching tag history from page: %s" % query_url
    page_src = "\n".join(map(str.strip, urllib2.urlopen(query_url).readlines()))
    update_list = util_tag_history_parse_page_type2(page_src)

    has_update = False
    max_ver = 0
    for id_in_set, new_version in update_list:
        if new_version > max_ver:
            max_ver = new_version
        ret = db_update_image_tag_version(set_name, id_in_set, new_version)
        if ret == True:
            print "update image version: %s %d => v%d" % (set_name, id_in_set, new_version)
            has_update = True

    if has_update:
        db_tag_history_set_head_version(set_name, max_ver)
    db_commit()


def moe_fetch_tag_history_nekobooru():
    query_api = "http://nekobooru.net/post_tag_history"
    set_name = "nekobooru"

    print "fetching tag history from nekobooru site: %s" % query_api
    max_page = util_tag_history_get_max_page_type2(query_api)
    print "there are %d pages of tag history" % max_page

    head_version = db_tag_history_get_head_version(set_name)
    print "current head version in '%s' is %d" % (set_name, head_version)

    first_page_version_range = util_tag_history_get_page_time_range_type2(query_api + ("?page=%d" % 1))
    last_page_version_range = util_tag_history_get_page_time_range_type2(query_api + ("?page=%d" % max_page))

    print "version on first page (1) is %d ~ %d" % (first_page_version_range[0], first_page_version_range[1])
    print "version on last page (%d) is %d ~ %d" % (max_page, last_page_version_range[0], last_page_version_range[1])

    page_id = max_page # by default, start from last page
    high_page_range = last_page_version_range
    low_page_range = first_page_version_range
    if head_version > first_page_version_range[1] + 86400 + 1:
        page_id = 0 # no need to mirror
    elif head_version >= last_page_version_range[0]:
        # bisect to proper page and restart mirroring
        high_page_id = max_page
        low_page_id = 1
        while low_page_id + 1 < high_page_id:
            mid_page_id = (high_page_id + low_page_id) / 2
            mid_page_range = util_tag_history_get_page_time_range_type2(query_api + ("?page=%d" % mid_page_id))
            print "version on page %d is %d ~ %d" % (mid_page_id, mid_page_range[0], mid_page_range[1])
            if head_version <= mid_page_range[1]:
                low_page_id = mid_page_id
                low_page_range = mid_page_range
            else: # mid_page_range[1] < head_version
                high_page_id = mid_page_id
                high_page_range = mid_page_range
        page_id = high_page_id

    if page_id > 0:
        print "start fetching from page %d, version %d ~ %d" % (page_id, high_page_range[0], high_page_range[1])
        while page_id > 0:
            query_url = query_api + ("?page=%d" % page_id)
            moe_fetch_tag_history_page_type2(query_url, set_name)
            page_id -= 1

    print "fetched all tag history on site '%s'" % query_api


def util_count_history_per_page(page_src):
    count_per_page = 0
    idx = 0
    while True:
        idx = page_src.find("PostTagHistory.add_change", idx)
        if idx < 0:
            break
        count_per_page += 1
        idx = idx + 20
    return count_per_page


def util_tag_history_parse_update_id_list_danbooru(query_url):
    id_list = []
    page_src = "\n".join(map(str.strip, urllib2.urlopen(query_url).readlines()))
    idx = 0
    while True:
        idx = page_src.find("PostTagHistory.add_change(", idx)
        if idx < 0:
            break
        idx = idx + 26
        idx2 = page_src.find(",", idx)
        id_list += int(page_src[idx:idx2]),
        idx = idx2
    return id_list


def util_tag_history_find_update_id_range_danbooru(query_api, history_per_page):
    largest = 0
    smallest = 0

    # find largest
    id_list = util_tag_history_parse_update_id_list_danbooru(query_api)
    largest = max(id_list)

    # bisect finding smallest
    low_bound = 0
    high_bound = largest
    while low_bound + 1 < high_bound:
        guess = (low_bound + high_bound) / 2
        print "guessing smallest update_id to be %d" % guess
        id_list = util_tag_history_parse_update_id_list_danbooru(query_api + ("?before_id=%d" % guess))
        if len(id_list) > 0 and len(id_list) < (history_per_page / 2) + 1:
            smallest = min(id_list)
            break
        elif len(id_list) == 0:
            low_bound = guess
        else: # len(id_list) is large, so need to decrease high_bound
            high_bound = guess

    return [smallest, largest]



def moe_fetch_tag_history_danbooru():
    query_api = "http://danbooru.donmai.us/post_tag_history"
    set_name = "danbooru"
    print "fetching tag history from nekobooru site: %s" % query_api

    page_src = "\n".join(map(str.strip, urllib2.urlopen(query_api).readlines()))

    history_per_page = util_count_history_per_page(page_src)
    print "there are %d tag history entries per page" % history_per_page

    head_version = db_tag_history_get_head_version(set_name)
    print "current head version in '%s' is %d" % (set_name, head_version)

    smallest_update_id, largest_update_id = util_tag_history_find_update_id_range_danbooru(query_api, history_per_page)
    print "update_id range %d ~ %d" % (smallest_update_id, largest_update_id)

    before_id = smallest_update_id # by default, start from last page
    last_page_version_range = util_tag_history_get_page_time_range_type2(query_api + ("?before_id=%d" % (smallest_update_id + 10)))

    if head_version >= last_page_version_range[0]:
        high_before_id = largest_update_id
        low_before_id = smallest_update_id
        while low_before_id + history_per_page / 2 < high_before_id:
            mid_before_id = (high_before_id + low_before_id) / 2
            mid_page_range = util_tag_history_get_page_time_range_type2(query_api + ("?before_id=%d" % mid_before_id))
            print "version (before_id=%d) is %d ~ %d" % (mid_before_id, mid_page_range[0], mid_page_range[1])
            if head_version <= mid_page_range[1]:
                high_before_id = mid_before_id
            else:
                low_before_id = mid_before_id
        before_id = low_before_id

    if before_id > 0:
        print "start fetching with before_id=%d" % before_id
        while before_id <= largest_update_id + history_per_page:
            query_url = query_api + ("?before_id=%d" % before_id)
            moe_fetch_tag_history_page_type2(query_url, set_name)
            before_id += history_per_page

    print "fetched all tag history on site '%s'" % query_api



def moe_help():
    print """moe.py: manage all my acg pictures"
usage: moe.py <command>"
available commands:"

    add                             add a new image to library
    add-dir                         add all images in a directory to the library
    add-dir-tree                    add all images in a directory tree to the library
    backup-albums                   backup albums
    backup-all                      backup everything
    backup-cleanup                  cleanup backup repository
    backup-db                       backup database
    backup-rate-1                   backup images with rating 1
    backup-rate-2                   backup images with rating 2
    backup-rate-3                   backup images with rating 3
    backup-unrated                  backup images without rating
    check-md5                       check all images by their md5, need to build binaries under libexec first
    cleanup                         delete images with rating 0, empty albums, and compact the black list
    create-album                    create an album based on a folder of well-formed images
    export                          export images
    export-album                    export images in an album
    export-big-unrated              export big and unrated images for rating, see import-rating-by-find
    export-psp                      (depracated) export images for PSP rating
    export-sql                      export images based on sql query result
    fetch-tag-history-danbooru      fetch tag history from danbooru.donmai.us
    fetch-tag-history-konachan      fetch tag history from konachan.com
    fetch-tag-history-moe-imouto    fetch tag history from moe.imouto.org
    fetch-tag-history-nekobooru     fetch tag history from nekobooru.net
    find-ophan                      find images that are in images root, but not in database
    help                            display this info
    highres-rating                  (depracated) mirror rating of normal res image set to highres image set
    import                          batch import pictures
    import-album                    import existing album
    import-black-list               import existing black list file
    import-rating-dir               import existing rating result from `find` output
    import-rating-psp               (depracated) import existing rating from my PSP lua application
    info                            display info about an image
    info-album                      display info about an album
    list-albums                     list all the albums and their size
    mirror-all                      mirror all known sites
    mirror-danbooru                 mirror danbooru.donmai.us
    mirror-danbooru-1000            mirror danbooru.donmai.us from 1000th page
    mirror-danbooru-before          mirror danbooru.donmai.us before a certain picture id
    mirror-konachan                 mirror konachan.com
    mirror-moe-imouto               mirror moe.imouto.org
    mirror-moe-imouto-html          mirror moe.imouto.org (through html request)
    mirror-nekobooru                mirror nekobooru.net
    mirror-tu178                    mirror tu.178.com
    sync-rating                     sync rating for images
    update-file-size                (depreated) make sure every images's file_size is read into databse
    update-pool-danbooru            update pool info from danbooru.donmai.us
    update-pool-konachan            update pool info from konachan.com
    update-pool-moe-imouto          update pool info from moe.imouto.org
    update-pool-nekobooru           update pool info from nekobooru.net
    update-tag-history-danbooru     update tag history from danbooru.donmai.us
    update-tag-history-konachan     update tag history from konachan.com
    update-tag-history-moe-imouto   update tag history from moe.imouto.org
    update-tag-history-nekobooru    update tag history from nekobooru.net

author: Santa Zhang (santa1987@gmail.com)"""

if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "help":
        moe_help()
    elif sys.argv[1] == "add":
        init_db_connection()
        moe_add()
    elif sys.argv[1] == "add-dir":
        init_db_connection()
        moe_add_dir()
    elif sys.argv[1] == "add-dir-tree":
        init_db_connection()
        moe_add_dir_tree()
    elif sys.argv[1] == "backup-db":
        init_db_connection()
        moe_backup_db()
    elif sys.argv[1] == "backup-all":
        init_db_connection()
        moe_backup_all()
    elif sys.argv[1] == "backup-albums":
        init_db_connection()
        moe_backup_albums()
    elif sys.argv[1] == "backup-rate-1":
        init_db_connection()
        moe_backup_by_rating(1)
    elif sys.argv[1] == "backup-rate-2":
        init_db_connection()
        moe_backup_by_rating(2)
    elif sys.argv[1] == "backup-rate-3":
        init_db_connection()
        moe_backup_by_rating(3)
    elif sys.argv[1] == "backup-unrated":
        init_db_connection()
        moe_backup_by_rating(None)
    elif sys.argv[1] == "backup-cleanup":
        init_db_connection()
        moe_backup_cleanup()
    elif sys.argv[1] == "check-md5":
        init_db_connection()
        moe_check_md5()
    elif sys.argv[1] == "cleanup":
        init_db_connection()
        moe_cleanup()
    elif sys.argv[1] == "create-album":
        init_db_connection()
        moe_create_album()
    elif sys.argv[1] == "export":
        init_db_connection()
        moe_export()
    elif sys.argv[1] == "export-album":
        init_db_connection()
        moe_export_album()
    elif sys.argv[1] == "export-big-unrated":
        init_db_connection()
        moe_export_big_unrated()
    elif sys.argv[1] == "export-psp":
        init_db_connection()
        moe_export_psp()
    elif sys.argv[1] == "export-sql":
        init_db_connection()
        moe_export_sql()
    elif sys.argv[1] == "fetch-tag-history-danbooru":
        init_db_connection()
        moe_fetch_tag_history_danbooru()
    elif sys.argv[1] == "fetch-tag-history-konachan":
        init_db_connection()
        moe_fetch_tag_history_type1("http://konachan.com/history?search=type%3Aposts", "konachan")
    elif sys.argv[1] == "fetch-tag-history-moe-imouto":
        init_db_connection()
        moe_fetch_tag_history_type1("http://oreno.imouto.org/history?search=type%3Aposts", "moe_imouto")
    elif sys.argv[1] == "fetch-tag-history-nekobooru":
        init_db_connection()
        moe_fetch_tag_history_nekobooru()
    elif sys.argv[1] == "find-ophan":
        init_db_connection()
        moe_find_ophan()
    elif sys.argv[1] == "import":
        init_db_connection()
        moe_import()
    elif sys.argv[1] == "import-album":
        init_db_connection()
        moe_import_album()
    elif sys.argv[1] == "import-black-list":
        init_db_connection()
        moe_import_black_list()
    elif sys.argv[1] == "import-rating-dir":
        init_db_connection()
        moe_import_rating_dir()
    elif sys.argv[1] == "import-rating-psp":
        init_db_connection()
        moe_import_rating_psp()
    elif sys.argv[1] == "highres-rating":
        init_db_connection()
        moe_highres_rating()
    elif sys.argv[1] == "info":
        init_db_connection()
        moe_info()
    elif sys.argv[1] == "info-album":
        init_db_connection()
        moe_info_album()
    elif sys.argv[1] == "list-albums":
        init_db_connection()
        moe_list_albums()
    elif sys.argv[1] == "mirror-all":
        moe_mirror_all()
    elif sys.argv[1] == "mirror-danbooru":
        init_db_connection()
        moe_mirror_danbooru()
    elif sys.argv[1] == "mirror-danbooru-1000":
        init_db_connection()
        moe_mirror_danbooru_1000()
    elif sys.argv[1] == "mirror-danbooru-before":
        init_db_connection()
        moe_mirror_danbooru_before(int(sys.argv[2]))
    elif sys.argv[1] == "mirror-konachan":
        init_db_connection()
        moe_mirror_konachan()
    elif sys.argv[1] == "mirror-konachan-html":
        init_db_connection()
        moe_mirror_konachan_html()
    elif sys.argv[1] == "mirror-moe-imouto":
        init_db_connection()
        moe_mirror_moe_imouto()
    elif sys.argv[1] == "mirror-moe-imouto-html":
        init_db_connection()
        moe_mirror_moe_imouto_html()
    elif sys.argv[1] == "mirror-nekobooru":
        init_db_connection()
        moe_mirror_nekobooru()
    elif sys.argv[1] == "mirror-tu178":
        init_db_connection()
        moe_mirror_tu178()
    elif sys.argv[1] == "sync-rating":
        init_db_connection()
        moe_sync_rating()
    elif sys.argv[1] == "update-file-size":
        init_db_connection()
        moe_update_file_size()
    elif sys.argv[1] == "update-pool-danbooru":
        init_db_connection()
        moe_update_pool("http://danbooru.donmai.us/pool/index", "danbooru")
    elif sys.argv[1] == "update-pool-konachan":
        init_db_connection()
        moe_update_pool("http://konachan.com/pool", "konachan")
    elif sys.argv[1] == "update-pool-moe-imouto":
        init_db_connection()
        moe_update_pool("http://oreno.imouto.org/pool", "moe_imouto")
    elif sys.argv[1] == "update-pool-nekobooru":
        init_db_connection()
        moe_update_pool("http://nekobooru.net/pool/index", "nekobooru")
    elif sys.argv[1] == "update-tag-history-danbooru":
        init_db_connection()
        moe_update_tag_history("http://danbooru.donmai.us/post/show", "danbooru")
    elif sys.argv[1] == "update-tag-history-konachan":
        init_db_connection()
        moe_update_tag_history("http://konachan.com/post/show", "konachan")
    elif sys.argv[1] == "update-tag-history-moe-imouto":
        init_db_connection()
        moe_update_tag_history("http://oreno.imouto.org/post/show", "moe_imouto")
    elif sys.argv[1] == "update-tag-history-nekobooru":
        init_db_connection()
        moe_update_tag_history("http://nekobooru.net/post/show", "nekobooru")
    else:
        print "command '%s' not understood, see 'moe.py help' for more info" % sys.argv[1]
