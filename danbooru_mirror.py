#!/usr/bin/python

# author: Santa Zhang (santa1987@gmail.com)
# mirroring danbooru sites
#
# currently support:
# http://moe.imouto.org
# http://konachan.com
# http://danbooru.donmai.us
# http://nekobooru.net

import json
import urllib2
from urllib2 import HTTPError
import re
import sys
import os
import traceback
import socket
import time
import hashlib
import shutil
from select import *

black_list = set()

def load_black_list(img_set_name):
  blk = set()
  f = open("black_list.txt")
  for l in f.readlines():
    l = l.strip()
    if len(l) == 0:
      continue
    sp1 = l.split()
    if sp1[0] != img_set_name:
      continue
    if "-" in sp1[1]:
      sp2 = sp1[1].split("-")
      begin = int(sp2[0])
      end = int(sp2[1])
      for i in range(begin, end + 1):
        blk.add(i)
    else:
      v = int(sp1[1])
      blk.add(v)
  f.close()
  return blk

def download_danbooru_image(basefolder, bucket_name, id, url, type, size = 0, md5 = None):
  
  # check if in black list
  int_id = int(id)
  if int_id in black_list:
    print "[black list] %d skipped" % id
    return
    
  try:
    url = "http://" + urllib2.quote(url[7:])
    pic_ext = url[url.rfind("."):]
    final_bucket = basefolder + os.path.sep + type + os.path.sep + bucket_name
    final_path = final_bucket + os.path.sep + str(id) + pic_ext
    
    if os.path.exists(final_path):
      print "[%s] %d skipped" % (type, id)
      return
    
    print "[%s] %d started on %s" % (type, id, time.asctime())
    start_time = time.time()
    src = urllib2.urlopen(url)
    pic_data = src.read()
    
    prepare_folder(basefolder + os.path.sep + "tmp")
    pic_fn = basefolder + os.path.sep + "tmp" + os.path.sep + type + "-" + str(id) + pic_ext
    pic_f = open(pic_fn, "wb")
    pic_f.write(pic_data)
    pic_f.close()
    
    if size != 0:
      if os.stat(pic_fn).st_size != size:
        print "[%s] %d broken: wrong size" % (type, id)
        return
    
    if md5 != None:
      m = hashlib.md5()
      m.update(pic_data)
      if m.hexdigest() != md5:
        print "[%s] %d broken: wrong md5 sum" % (type, id)
        return
    
    prepare_folder(final_bucket)
    shutil.move(pic_fn, final_path)
    end_time = time.time()
    speed = len(pic_data) / (end_time - start_time) / 1024.0
    print "[%s] %d finished on %s, speed = %.2f K/s" % (type, id, time.asctime(), speed)
    
  except:
    traceback.print_exc()
    time.sleep(1)
  

def mirror_danbooru(basefolder, site, start_page):
  current_page = start_page
  while True:
    try:
      url = site + ("/post/index.json?page=%d" % current_page)
      print "[page] %s" % url
      current_page += 1
      
      try:
        page = urllib2.urlopen(url)
        page_all_lines = page.readlines()
        page_all_text = "\n".join(page_all_lines)
      except HTTPError, e:
        print "server response code: " + str(e.code)
        
      info_list = []
      try:
        info_list.extend(json.loads(page_all_text))
      except:
        # json decode failure, the site is probably down for maintenance... (danbooru.donmai.us, usually)
        # on this condition, we wait for a very long time
        print "site down for maintenance, wait for 2 minutes, on %s" % time.asctime()
        print "when resumed, will restart from page 1"
        time.sleep(120) # wait 2 minutes
        current_page = 1
        continue
      
      if len(info_list) == 0:
        print "no more images"
        print "restart downloading from page 1"
        current_page = 1
        continue
      
      for info in info_list:
        try:
          if int(info[u"id"]) in black_list:
            print "[black list] %d skipped" % int(info[u"id"])
            continue
          bucket_size = 100
          bucket_id = info[u"id"] / bucket_size
          bucket_name = "%d-%d" % (bucket_id * bucket_size, bucket_id * bucket_size + bucket_size - 1)
          bucket_path = basefolder + os.path.sep + "info" + os.path.sep + bucket_name
          prepare_folder(bucket_path)
          info_fn = bucket_path + os.path.sep + str(info[u"id"]) + ".txt"
          info_f = open(info_fn, "w")
          info_f.write(json.dumps(info))
          info_f.close()
          
          bucket_path = basefolder + os.path.sep + "tags" + os.path.sep + bucket_name
          prepare_folder(bucket_path)
          tag_fn = bucket_path + os.path.sep + str(info[u"id"]) + ".txt"
          tag_f = open(tag_fn, "w")
          for tag in info[u"tags"].split():
            try:
              tag_f.write(tag + "\n")
            except:
              pass
          tag_f.close()
          
          download_danbooru_image(basefolder, bucket_name, info[u"id"], info[u"preview_url"], "preview")
          if info.has_key(u"sample_file_size"):
            download_danbooru_image(basefolder, bucket_name, info[u"id"], info[u"sample_url"], "sample", info[u"sample_file_size"])
          else:
            download_danbooru_image(basefolder, bucket_name, info[u"id"], info[u"sample_url"], "sample")
          if info.has_key(u"jpeg_url"):
            download_danbooru_image(basefolder, bucket_name, info[u"id"], info[u"jpeg_url"], "jpeg", info[u"jpeg_file_size"])
          if info.has_key(u"file_size"):
            download_danbooru_image(basefolder, bucket_name, info[u"id"], info[u"file_url"], "original", info[u"file_size"], info[u"md5"])
          else:
            download_danbooru_image(basefolder, bucket_name, info[u"id"], info[u"file_url"], "original", 0, info[u"md5"])
          
        except:
          traceback.print_exc()
          time.sleep(1)
      
    except:
      traceback.print_exc()
      time.sleep(1)


def prepare_folder(path):
  if os.path.exists(path) == False:
    os.makedirs(path)
    print "[mkdir] " + path


def do_mirror(basedir, site, start_page):
  global black_list
  
  timeout = 30  # 30 secs
  socket.setdefaulttimeout(timeout)
  if site.find("danbooru") != -1:
    site = "http://danbooru.donmai.us"
    black_list = load_black_list("danbooru")
  elif site.find("konachan") != -1:
    site = "http://konachan.com"
    black_list = load_black_list("konachan")
  elif site.find("imouto") != -1:
    site = "http://moe.imouto.org"
    black_list = load_black_list("moe_imouto")
  elif site.find("nekobooru") != -1:
    site = "http://nekobooru.net"
    black_list = load_black_list("nekobooru")
  else:
    print "site not supported: " + site
    return
  mirror_danbooru(basedir, site, start_page)
  

if __name__ == "__main__":
  print "this is danbooru_mirror!"
  print "usage: danbooru_mirror <folder> <site> [start_page=1]"
  if len(sys.argv) > 3:
    do_mirror(sys.argv[1], sys.argv[2], int(sys.argv[3]))
  elif len(sys.argv) == 3:
    do_mirror(sys.argv[1], sys.argv[2], 1)
