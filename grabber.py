#!/usr/bin/env python

# One script to manage my manga books.
# Only for MacOS!
#
# Author: Santa Zhang (santa1987@gmail.com)
#


import sys
import os
import re
import time
import traceback
import shutil
import socket
import urllib2
from urllib2 import HTTPError
from utils import *

SOCKET_TIMEOUT = 30
socket.setdefaulttimeout(SOCKET_TIMEOUT)

# fetch global const values
ZIP_FILES = get_config("zip_f", "true")
if ZIP_FILES.lower().startswith("y") or ZIP_FILES.lower().startswith("t"):
  ZIP_FILES = True
else:
  ZIP_FILES = False

MANGA_FOLDER = get_config("manga_folder")


def grab_message(message):
  try:
    print message
  except:
    pass

def prepare_folder(path):
  if os.path.exists(path) == False:
    os.makedirs(path)
    grab_message("[mkdir] %s" % path)

def grab_print_help():
  print "grabber.py: manage my manga books"
  print "usage: grabber.py <command>"
  print "available commands:"
  print
  print "  clear-cruft-files    clear cruft files in zip packages"
  print "  download             download a manga book"
  print "  download-reverse     download a manga book, in reverse order"
  print "  help                 display this help message"
  print "  list-library         list contents in library"
  print "  update               update specified managed manga books"
  print "  update-all           update all managed manga books"
  print
  print "author: Santa Zhang (santa1987@gmail.com)"
  
def grab_is_image(fname):
  return is_image(fname)


def folder_contains_images(dirpath):
  for fn in os.listdir(dirpath):
    if grab_is_image(fn):
      return True
  return False

def grab_ensure_manga_packed_walker(arg, dirname, fnames):
  has_image = False
  has_subdir = False
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
      return
  if has_image == False:
    print "found an empty folder, not zipping it"
    return
  if has_subdir == True:
    print "has subdir, not zipping it"
    return
    
  # do zipping
  print "zipping"
  archive_name = os.path.abspath(dirname) + ".zip"
  if zipdir(dirname, archive_name) == True:
    shutil.rmtree(dirname)
    print "zip done, removing original folder"
  else:
    print "[error] failed to create zip archive!"
  
def grab_ensure_manga_packed(root_dir=None):
  if root_dir == None:
    return
  grab_message("[zip] %s" % root_dir)
  if ZIP_FILES == True:
    grab_message("packing manga books")
    os.path.walk(root_dir, grab_ensure_manga_packed_walker, None)

def grab_download_manhua178(manga_url, **opt):
  print "[toc] %s" % manga_url
  root_page = manga_url
  page_src = urllib2.urlopen(root_page).read()
  idx = page_src.index("var g_comic_name = \"") + 20
  idx2 = page_src.index("\r\n", idx) - 2
  comic_name = page_src[idx:idx2].replace(" ", "").decode("utf-8")
  comic_name = comic_name.strip()

  idx = page_src.index("cartoon_online_border")
  idx = page_src.index("<ul>", idx)
  idx2 = page_src.index("</ul>", idx)
  toc_src = page_src[idx:idx2]
  toc_src_split = toc_src.split("\r\n")
  toc_arr = []
  for sp in toc_src_split:
    idx = sp.find('<li><a title="') + 14
    if idx == -1:
      continue
    idx2 = sp.find('" href="', idx)
    title = sp[idx:idx2]
    idx = idx2 + 8
    idx2 = sp.find('"', idx)
    href = sp[idx:idx2]
    if title.strip() == "":
      continue
    toc_arr += (title, href),
  
  # download new chapters if necessary
  if opt.has_key("reverse") and opt["reverse"] == True:
    toc_arr.reverse()
  
  comic_name = comic_name.replace('/', "~")
  comic_folder_path = MANGA_FOLDER + os.path.sep + comic_name + "(acg178)"
  prepare_folder(comic_folder_path)
  link_f = open(comic_folder_path + os.path.sep + "downloaded_from.txt", "w")
  print "writing download url file"
  link_f.write(manga_url + "\n")
  link_f.close()
  
  # now download chapter
  for chap in toc_arr:
    try:
      chap_title = chap[0].decode("utf-8")
      chap_title = chap_title.replace('/', "~")
      chap_title = chap_title.strip()
      chap_href = chap[1]
      chapter_folder_path = comic_folder_path + u"/" + chap_title

      # pass chapter if zip exists or the folder does not have NOT_FINISHED & ERROR file
      chapter_zip_fn = comic_folder_path + u"/" + chap_title + ".zip"
      if os.path.exists(chapter_zip_fn):
        print "zip exists, pass chapter"
        continue
      else:
        print "zip not exists!"

      prepare_folder(chapter_folder_path)
      
      error_log_fn = chapter_folder_path + u"/ERROR"
      not_finished_fn = chapter_folder_path + u"/NOT_FINISHED"
      if os.path.exists(error_log_fn) == False and os.path.exists(not_finished_fn) == False and folder_contains_images(chapter_folder_path):
        print "chapter already downloaded, skip"
        grab_ensure_manga_packed(comic_folder_path)
        continue
      else:
        print "still have to download chapter"
      
      idx = root_page.rfind("/")
      idx = root_page[0:idx].rfind("/")
      base_url = root_page[0:idx]
      chap_url = base_url + chap_href[2:]
      chap_url = chap_url.replace(" ", "%20")

      chap_src = urllib2.urlopen(chap_url).read()
      idx = chap_src.find("var pages") + 13
      idx2 = chap_src.find("\r\n", idx) - 2
      comic_pages_src = chap_src[idx:idx2].replace("\\/", "/")
      comic_pages_url = eval(comic_pages_src)
      
      # remove possibly existing error log file
      if os.path.exists(error_log_fn):
        os.remove(error_log_fn)
      
      # create a place holder
      open(not_finished_fn, "w").close()
      
      chapter_download_ok = True # whether the chapter is successfully downloaded
      for pg in comic_pages_url:
        full_pg = (base_url + "/imgs/" + pg)
        idx = full_pg.rfind("/") + 1
        leaf_nm = full_pg[idx:]
        print leaf_nm
        fn = comic_folder_path + u"/" + chap_title + u"/" + leaf_nm.decode("unicode_escape")
        grab_message(fn)
        down_filename = fn
        if os.path.exists(down_filename):
          grab_message("[pass] %s" % down_filename)
          continue
        down_f = None
        full_pg_unescaped = full_pg.decode("unicode_escape").encode("utf-8")
        full_pg_unescaped = full_pg_unescaped.replace(" ", "%20")
        try:
          down_data = urllib2.urlopen(full_pg_unescaped).read()
          down_f = open(fn + u".tmp", "wb")
          down_f.write(down_data)
          down_f.close()
          shutil.move(fn + u".tmp", fn)
        except HTTPError, e:
          print "download failure!"
          if down_f != None:
            down_f.close()
          if os.path.exists(fn + u".tmp"):
            os.remove(fn + u".tmp")
          err_log_f = open(error_log_fn, "a")
          try:
            err_log_f.write("failed to download: %s\n" % fn)
          except:
            err_log_f.write("failed to download from: %s\n" % full_pg_unescaped)
          finally:
            err_log_f.close()
          chapter_download_ok = False
      
      # remove the place holder
      if os.path.exists(not_finished_fn):
        os.remove(not_finished_fn)
      
      # pack the folder if necessary
      grab_ensure_manga_packed(comic_folder_path)
      
    except:
      traceback.print_exc()
      time.sleep(1)


def bengou_down_page(page_url, down_dir, page_id):
  ok = True
  print "[down] id=%d, url=%s" % (page_id, page_url)
  page_src = urllib2.urlopen(page_url).read()

  # get pic url:
  idx = page_src.index('"disp"')
  idx = page_src.index('http://', idx)
  idx2 = page_src.index('"', idx)
  img_url = page_src[idx:idx2]
  print "[img] %s" % img_url
  
  error_log_fn = os.path.join(down_dir, "ERROR")

  # download pic:
  img_ext = img_url[img_url.rfind("."):]
  pic_fn = down_dir + os.path.sep + ("%03d" % page_id) + img_ext
  if os.path.exists(pic_fn):
    try:
      print "[skip] %s" % pic_fn
    except:
      pass
  else:
    pic_f = None
    try:
      pic_data = urllib2.urlopen(img_url).read()
      pic_f = open(pic_fn + u".tmp", "wb")
      pic_f.write(pic_data)
      pic_f.close()
      shutil.move(pic_fn + u".tmp", pic_fn)
    except HTTPError, e:
      if pic_f != None:
        pic_f.close()
      if os.path.exists(pic_fn + u".tmp"):
        os.remove(pic_fn + u".tmp")
      print "[failure] %s" % page_url
      
      err_log_f = open(error_log_fn, "a")
      try:
        err_log_f.write("failed to download: %s\n" % pic_fn)
      except:
        err_log_f.write("failed to download from: %s\n" % img_url)
      finally:
        err_log_f.close()
      
      ok = False
  return ok

def bengou_down_vol(vol_url, down_dir):
  all_ok = True
  print "[vol-url] %s" % vol_url
  page_src = urllib2.urlopen(vol_url).read()
  root_url = vol_url[:vol_url.rfind("/")]

  # get pic tree
  idx = page_src.index("var pictree")
  idx2 = page_src.index(";", idx)
  pictree_src = page_src[(idx + 14):idx2]
  exec "pictree=%s" % pictree_src
  counter = 1
  for pic in pictree:
    try:
      ok = bengou_down_page(root_url + "/" + pic, down_dir, counter)
      all_ok = all_ok and ok
      counter += 1
    except HTTPError, e:
      all_ok = False
      traceback.print_exc()
      time.sleep(1)
  return all_ok

def grab_download_bengou(index_url, **opt):
  page_src = urllib2.urlopen(index_url).read()
  index_root = index_url[:index_url.rfind("/")]
  # find manga name
  idx = page_src.index("sectioninfo ")
  idx = page_src.index("title=", idx)
  idx2 = page_src.index('"', idx + 7)
  comic_name = page_src[(idx + 7):idx2].decode("utf-8")
  grab_message(comic_name)
  grab_message("[index-url] %s" % index_url)
  
  comic_folder_path = MANGA_FOLDER + os.path.sep + comic_name + "(bengou)"

  # find the volumes
  idx = page_src.index("mhlist")
  idx2 = page_src.index("</div>", idx)
  mhlist_src = page_src[idx:idx2]

  
  manga_list = []
  idx = 0
  idx2 = 0
  while True:
    idx = mhlist_src.find("href", idx2)
    if idx < 0:
      break
    idx2 = mhlist_src.index("target", idx)
    vol_url = index_root + "/" + mhlist_src[(idx + 6):(idx2 - 2)]
    idx = mhlist_src.find("span", idx2)
    idx2 = mhlist_src.index("</span>", idx)
    vol_name = mhlist_src[(idx + 17):(idx2)].decode("utf-8")
    manga_list += (vol_name, vol_url),

  # download new chapters if necessary
  if opt.has_key("reverse") and opt["reverse"] == True:
    manga_list.reverse()

  for vol_name, vol_url in manga_list:
    grab_message(vol_name)
    grab_message("[vol-page] %s" % vol_url)
    chapter_folder_path = os.path.join(comic_folder_path, vol_name)
    chapter_zip_fn = chapter_folder_path + ".zip"
    
    if os.path.exists(chapter_zip_fn):
      print "zip exists, pass chapter"
      continue
    else:
      print "zip not exists!"
    
    prepare_folder(chapter_folder_path)
    
    error_log_fn = chapter_folder_path + u"/ERROR"
    not_finished_fn = chapter_folder_path + u"/NOT_FINISHED"
    if os.path.exists(error_log_fn) == False and os.path.exists(not_finished_fn) == False and folder_contains_images(chapter_folder_path):
      print "chapter already downloaded, skip"
      grab_ensure_manga_packed(comic_folder_path)
      continue
    else:
      print "still have to download chapter"
  
    # remove possibly existing error log file
    if os.path.exists(error_log_fn):
      os.remove(error_log_fn)
    
    # create a place holder
    open(not_finished_fn, "w").close()
  
    all_ok = bengou_down_vol(vol_url, chapter_folder_path)
    
    # remove the place holder
    if os.path.exists(not_finished_fn):
      os.remove(not_finished_fn)
    
    # pack the folder if necessary
    grab_ensure_manga_packed(comic_folder_path)

  
def grab_download_print_help():
  print "download a manga book"
  print "usage: grabber.py download <url>"
  print "<url> is the table of contents page"

def grab_download_real(url, **opt):
  if url.startswith("http://") == False:
    url = "http://" + url
  if url.find("manhua.178.com") >= 0:
    grab_download_manhua178(url, **opt)
  elif url.find("bengou.com") >= 0:
    grab_download_bengou(url, **opt)    
  else:
    print "sorry, the manga book site is not supported!"
  

def grab_download(**opt):
  if len(sys.argv) <= 2:
    grab_download_print_help()
    exit()
  url = sys.argv[2]
  grab_download_real(url, **opt)
  

def grab_load_library():
  library_fn = os.path.join(os.path.split(__file__)[0], "grabber.library")
  print library_fn
  lib_f = open(library_fn)
  name = None
  url = None
  library = {}
  for line in lib_f.readlines():
    line = line.strip()
    if line.startswith("#"):
      continue
    if line == "":
      if name != None and url != None:
        if library.has_key(name):
          print "[warning] duplicate name '%s' in grabber.library" % name
        library[name] = url
        name = None
        url = None
    if line.startswith("name="):
      name = line[5:]
    elif line.startswith("url="):
      url = line[4:]
  if name != None and url != None:
    if library.has_key(name):
      print "[warning] duplicate name '%s' in grabber.library" % name
    library[name] = url
    name = None
    url = None
  lib_f.close()
  return library

def grab_update_all():
  library = grab_load_library()
  for manga_name in library:
    try:
      url = library[manga_name]
      print "downloading '%s' from '%s'" % (manga_name, url)
      grab_download_real(url)
    except:
      traceback.print_exc()
      time.sleep(1)

def grab_update_show_help():
  print "update specific manga books"
  print "usage: grabber.py update <manga1> [manga2] [manga3]"

def grab_update():
  if len(sys.argv) <= 2:
    grab_update_show_help()
    return()
  library = grab_load_library()
  for i in range(2, len(sys.argv)):
    manga_name = sys.argv[i]
    if library.has_key(manga_name) == False:
      print "[warning] no such manga: '%s', skipping it" % manga_name
      continue
    else:
      url = library[manga_name]
      print "downloading '%s' from '%s'" % (manga_name, url)
      grab_download_real(url)
    

def grab_list_library():
  library = grab_load_library()
  print "library content:"
  print
  for item in library:
    print "%s => %s" % (item, library[item])
  print
  print "%d items in library" % len(library)

def grab_is_cruft_file(fn):
  if fn.lower() == ".ds_store" or fn.lower() == "thumbs.db":
    return True
  return False

def grab_clear_cruft_files():
  for root, dirs, files in os.walk(MANGA_FOLDER):
    for fn in files:
      if not fn.lower().endswith(".zip"):
        continue
      fpath = os.path.join(root, fn)
      should_rm_zf = False
      zf = ZipFile(fpath)
      for entry in zf.namelist():
        if grab_is_cruft_file(entry):
          print fpath
          main_fn = os.path.splitext(fn)[0]
          extract_path = os.path.join(root, main_fn)
          prepare_folder(extract_path)
          zf.extractall(extract_path)
          should_rm_zf = True
          break
      zf.close()
      if should_rm_zf:
        print "remove original zip"
        os.remove(fpath)


if __name__ == "__main__":
  if len(sys.argv) == 1 or sys.argv[1] == "help":
    grab_print_help()
  elif sys.argv[1] == "clear-cruft-files":
    grab_clear_cruft_files()
  elif sys.argv[1] == "download":
    grab_download()
  elif sys.argv[1] == "download-reverse":
    grab_download(reverse=True)
  elif sys.argv[1] == "list-library":
    grab_list_library()
  elif sys.argv[1] == "update":
    grab_update()
  elif sys.argv[1] == "update-all":
    grab_update_all()
  else:
    print "command '%s' not understood, see 'grabber.py help' for more info" % sys.argv[1]

