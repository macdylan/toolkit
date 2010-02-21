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

def download_danbooru_image(basefolder, bucket_name, id, url, type, size = 0, md5 = None):
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
    time.sleep(10)
  

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
        print "Server response code: " + str(e.code)
        
      try:
        info_list = json.loads(page_all_text)
      except:
        # json decode failure, the site is probably down for maintenance... (danbooru.donmai.us, usually)
        # on this condition, we wait for a very long time
        print "Site down for maintenance, wait for half hour, on %s" % time.asctime()
        time.sleep(60 * 30) # wait half an hour
        continue
      
      
      for info in info_list:
        try:
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
          time.sleep(10)
      
    except:
      traceback.print_exc()
      time.sleep(10)


def prepare_folder(path):
  if os.path.exists(path) == False:
    os.makedirs(path)
    print "[mkdir] " + path


def do_mirror(basedir, site, start_page):
  timeout = 30  # 30 secs
  socket.setdefaulttimeout(timeout)
  if site.find("danbooru") != -1:
    site = "http://danbooru.donmai.us"
  elif site.find("konachan") != -1:
    site = "http://konachan.com"
  elif site.find("imouto") != -1:
    site = "http://moe.imouto.org"
  elif site.find("nekobooru") != -1:
    site = "http://nekobooru.net"
  else:
    print "site not supported: " + site
    return
  mirror_danbooru(basedir, site, start_page)
  

if __name__ == "__main__":
  print "this is danbooru_mirror!"
  print "usage: danbooru_mirror <folder> <site> [start_page=1]"
  if (len(sys.argv) > 3):
    do_mirror(sys.argv[1], sys.argv[2], int(sys.argv[3]))
  else:
    do_mirror(sys.argv[1], sys.argv[2], 1)
