#!/usr/bin/env python

# script to mirror a whole phpgraphy site

from utils import *
from urlparse import urlparse
import urllib2
import traceback
import time
import shutil

# fetch global const values
ZIP_FILES = get_config("zip_f", "true")
if ZIP_FILES.lower().startswith("y") or ZIP_FILES.lower().startswith("t"):
  ZIP_FILES = True
else:
  ZIP_FILES = False

def grab_is_image(fname):
  return is_image(fname)

# helper function directly copied from grabber.py
def grab_ensure_manga_packed_walker(arg, dirname, fnames):
  has_image = False
  has_subdir = False
  archive_name = os.path.abspath(dirname) + ".zip"
  for fn in fnames:
    fpath = dirname + os.path.sep + fn
    if os.path.isdir(fpath):
      has_subdir = True
      continue
    if grab_is_image(fn):
      has_image = True
    if fn == "NOT_FINISHED" or fn == "ERROR":
      # a bad folder
      print "found a bad folder, not zipping it"
      if os.path.exists(archive_name):
        print "zip archive already exists, removing folder"
        shutil.rmtree(dirname)
      return
  if has_subdir == True:
    print "has subdir, not zipping it"
    return
  if has_image == False:
    print "found an empty folder, skipping it"
    return

  # do zipping
  print "zipping"
  # remove FINISHED file from zip package
  finished_fn = os.path.join(dirname, "FINISHED")
  if os.path.exists(finished_fn):
    os.remove(finished_fn)
  if zipdir(dirname, archive_name) == True:
    shutil.rmtree(dirname)
    print "zip done, removing original folder"
  else:
    print "[error] failed to create zip archive!"

def grab_ensure_manga_packed(root_dir=None):
  if root_dir == None:
    return
  print "[zip] %s" % root_dir
  if ZIP_FILES == True:
    print "packing manga books"
    os.path.walk(root_dir, grab_ensure_manga_packed_walker, None)

def prepare_folder(path):
  if os.path.exists(path) == False:
    os.makedirs(path)
    print("[mkdir] %s" % path)

def parse_subdir_list(page_src, dir_url):
  url = urlparse(dir_url)
  subdir_list = []
  idx = 0
  while True:
    idx = page_src.find('<div class="ffcontentwrap', idx)
    if idx < 0:
      break
    idx2 = page_src.find('<a href="?dir=', idx)
    idx = page_src.find('"', idx2 + 10)
    subdir_url = "http://" + url[1] + url[2] + page_src[idx2 + 9:idx]
    subdir_list += subdir_url,
    idx = idx2
  return subdir_list

def parse_image_list_slideshows(page_src, dir_url, pic_list):
  url = urlparse(dir_url)
  pic_url_prefix = "http://" + url[1] + os.path.split(url[2])[0] + "/"
  if (page_src.find("slideshow_start_count") >= 0):
    idx = 0
    while True:
      idx = page_src.find('<span class="slideshow_path">', idx)
      if idx < 0:
        break
      idx = page_src.find('>', idx + 2)
      idx2 = page_src.find('</span>', idx)
      pic_url = pic_url_prefix + urllib2.quote(page_src[idx + 1:idx2])
      pic_list += pic_url,
      idx = idx2

def parse_image_page_by_page(first_page_src, dir_url, pic_list):
  
  pass

def parse_image_list(page_src, dir_url):
  pic_list = []
  parse_image_list_slideshows(page_src, dir_url, pic_list)
  parse_image_page_by_page(page_src, dir_url, pic_list)
  return pic_list

def pgm_mirror(dir_url):
  if dir_url.startswith("http://") == False:
    dir_url = "http://" + dir_url
  print "[mirror dir] %s" % dir_url
  url = urlparse(dir_url)
  params = dict([part.split('=') for part in url[4].split('&')])
  for p in params.keys():
    params[p] = urllib2.unquote(params[p])
  local_dir = os.path.join(get_config("local_root"), url[1], params["dir"])
  print "[local dir] %s" % local_dir
  prepare_folder(local_dir)
  
  dir_finished_fn = os.path.join(local_dir, "FINISHED")
  if os.path.exists(dir_finished_fn):
    print "[pass] %s" % local_dir
    return
  
  # create dir not finished flag file
  dir_finished = True
  dir_not_finished_fn = os.path.join(local_dir, "NOT_FINISHED")
  open(dir_not_finished_fn, "w").close()
  
  # check for sub folders
  page_src = urllib2.urlopen(dir_url).read()
  subdir_list = parse_subdir_list(page_src, dir_url)
  for subdir_url in subdir_list:
    try:
      pgm_mirror(subdir_url)
    except:
      dir_finished = False
      traceback.print_exc()
      time.sleep(1)
  
  # check for pictures
  pic_list = parse_image_list(page_src, dir_url)
  for pic_url in pic_list:
    print "[remote image] %s" % pic_url
    try:
      fn = os.path.join(local_dir, os.path.split(urlparse(pic_url)[2])[1])
      if !is_image(fn):
        print "TODO: deal with non-image files (possibly zip)"
      print "[local image] %s" % fn
      if os.path.exists(fn):
        print "[skip] %s" % fn
      else:
        down_data = urllib2.urlopen(pic_url).read()
        down_f = open(fn + u".tmp", "wb")
        down_f.write(down_data)
        down_f.close()
        shutil.move(fn + u".tmp", fn)
    except:
      dir_finished = False
      traceback.print_exc()
      time.sleep(1)
  
  # remove dir not finished flag file, if successful
  if dir_finished == True:
    os.remove(dir_not_finished_fn)
    open(dir_finished_fn, "w").close()
    print "[finish dir] %s" % local_dir

  # pack book
  grab_ensure_manga_packed(local_dir)


def pgm_pack_all():
  grab_ensure_manga_packed(get_config("local_root"))

def grab_print_help():
  print "phpgraphymirror.py: mirror phpgraphy sites"
  print "usage: phpgraphymirror.py <command>"
  print "available commands:"
  print
  print "  mirror-doujin-moe    mirror www.doujin-moe.us"
  print "  mirror <url>         mirror a specific site folder"
  print "  pack-all             pack all books"
  print
  print "author: Santa Zhang (santa1987@gmail.com)"

if __name__ == "__main__":
  if len(sys.argv) == 1 or sys.argv[1] == "help":
    grab_print_help()
  elif sys.argv[1] == "mirror":
    pgm_mirror(sys.argv[2])
  elif sys.argv[1] == "mirror-doujin-moe":
#    pgm_mirror("www.doujin-moe.us/phpgraphy/index.php?dir=")
    pgm_mirror("http://www.doujin-moe.us/phpgraphy/index.php?dir=Baka%20to%20Test%20to%20Shoukanju%2FDoujins%2F")
  elif sys.argv[1] == "pack-all":
    pgm_pack_all()
  else:
    print "command '%s' not understood, see 'phpgraphymirror.py help' for more info" % sys.argv[1]
