#!/usr/bin/python

# downloads image sets from g.e-hentai.org

import os
import sys
import urllib2
import traceback
import time
import zlib
from urllib2 import HTTPError

class GzipConsumer:

    def __init__(self, consumer):
        self.__consumer = consumer
        self.__decoder = None
        self.__data = ""

    def __getattr__(self, key):
        # delegate unknown methods/attributes
        return getattr(self.__consumer, key)

    def feed(self, data):
        if self.__decoder is None:
            # check if we have a full gzip header
            data = self.__data + data
            try:
                i = 10
                flag = ord(data[3])
                if flag & 4: # extra
                    x = ord(data[i]) + 256*ord(data[i+1])
                    i = i + 2 + x
                if flag & 8: # filename
                    while ord(data[i]):
                        i = i + 1
                    i = i + 1
                if flag & 16: # comment
                    while ord(data[i]):
                        i = i + 1
                    i = i + 1
                if flag & 2: # crc
                    i = i + 2
                if len(data) < i:
                    raise IndexError("not enough data")
                if data[:3] != "\x1f\x8b\x08":
                    raise IOError("invalid gzip data")
                data = data[i:]
            except IndexError:
                self.__data = data
                return # need more data
            import zlib
            self.__data = ""
            self.__decoder = zlib.decompressobj(-zlib.MAX_WBITS)
        data = self.__decoder.decompress(data)
        if data:
            self.__consumer.feed(data)

    def close(self):
        if self.__decoder:
            data = self.__decoder.flush()
            if data:
                self.__consumer.feed(data)
        self.__consumer.close()
        

class stupid_gzip_consumer:
  def __init__(self): self.data = []
  def feed(self, data): self.data.append(data)
  def close(self): pass

def gunzip(data):
  c = stupid_gzip_consumer()
  gzc = GzipConsumer(c)
  gzc.feed(data)
  gzc.close()
  return "".join(c.data)

def util_make_dirs(path):
  if os.path.exists(path) == False:
    print "[mkdir] %s" % path
    os.makedirs(path)

def is_finished(folder):
  mark_fn = folder + os.path.sep + "FINISHED"
  return os.path.exists(mark_fn)

def mark_unfinished(folder):
  lock_fn = folder + os.path.sep + "UNFINISHED"
  f = open(lock_fn, "w")
  f.close()

def mark_finished(folder):
  lock_fn = folder + os.path.sep + "UNFINISHED"
  unlock_fn = folder + os.path.sep + "FINISHED"
  os.rename(lock_fn, unlock_fn)

def do_real_mirror_chapter(chapter_link, folder):
  util_make_dirs(folder)
  if (is_finished(folder)):
    print "[skip] already mirrored or black listed"
    # TODO blacklist
  mark_unfinished(folder)
  
  chap_src = gunzip(urllib2.urlopen(chapter_link).read())
  
  idx = chap_src.find("<div class=\"gdtm")
  idx = chap_src.find("<a href=", idx) + 9
  idx2 = chap_src.find("\">", idx)
  pic_page_url =  chap_src[idx:idx2]
  could_mark_finish = True
  while True:
    try:
      pic_src = gunzip(urllib2.urlopen(pic_page_url).read())
    
      # determine id
      idx = pic_src.find("<span>") + 6
      idx2 = pic_src.find("</span>", idx)
      cur_pic_id = int(pic_src[idx:idx2])
      idx = pic_src.find("<span>", idx2) + 6
      idx2 = pic_src.find("</span>", idx)
      total_pic_count = int(pic_src[idx:idx2])
      print "%03d-of-%d" % (cur_pic_id, total_pic_count)
    
      # find image url
      idx = pic_src.find("</iframe>")
      idx = pic_src.find("<img src=\"", idx) + 10
      idx2 = pic_src.find("\" style", idx)
      img_url = pic_src[idx:idx2]
      img_fn = img_url.split("/")[-1]
      short_local_fn = "%03d-of-%d_%s" % (cur_pic_id, total_pic_count, img_fn)
      local_fn = folder + os.path.sep + short_local_fn
      print img_url, local_fn
      tmp_fn = local_fn + ".tmp"
      if not os.path.exists(local_fn):
        tmp_f = open(tmp_fn, "wb")
        tmp_f.write(urllib2.urlopen(img_url).read())
        tmp_f.close()
        os.rename(tmp_fn, local_fn)
      else:
        print "[skip] %s already downloaded" % short_local_fn
    
    
      # find next page
    
      idx = pic_src.find("/img/p.png")
      idx = pic_src.find("a href=", idx) + 8
      idx2 = pic_src.find("\"", idx)
    
      if pic_page_url == pic_src[idx:idx2]:
        break
      else:
        pic_page_url = pic_src[idx:idx2]
        
    except:
      traceback.print_exc()
      time.sleep(1)
      could_mark_finish = False

  if could_mark_finish:
    mark_finished(folder)

def do_mirror_chapter(genre, chapter_id, chapter_name, chapter_ranking, chapter_link):
  folder = "eh_down" + os.path.sep + genre + os.path.sep + chapter_id + "-" + chapter_name
  do_real_mirror_chapter(chapter_link, folder)

def start_download_from_index_page(page_id):
  while True:
    try:
      page_url = "http://g.e-hentai.org/?page=%d" % page_id
      print "\n[index page] %s" % page_url
      page_data = gunzip(urllib2.urlopen(page_url).read())
    
      # analyze index table
      idx = page_data.find("<table class=\"itg")
      while True:
        idx = page_data.find("<tr class=\"gtr", idx)
  #      print page_data[idx:idx+100]
      
        if idx < 0:
          break
        
        # find genre
        idx = page_data.find("e-hentai.org", idx) + 13
        idx2 = page_data.find("\"><img", idx)
      
        genre = page_data[idx:idx2]
      
        # find name
        idx = page_data.find("preload_pane_image_delayed", idx)
        idx = page_data.find("<div class=\"it3\"", idx)
        idx = page_data.find("<a href=\"http://g.e-hen", idx)
        idx2 = page_data.find("</a>", idx)
        sublink = page_data[idx:idx2]
      
        idx3 = sublink.find("\"") + 1
        idx4 = sublink.find("\"", idx3 + 3)
      
        chapter_link = sublink[idx3:idx4]
        chapter_name = sublink[idx4 + 2:]
        chapter_id = chapter_link.split("/")[4]
      
        # for ranking
        idx5 = page_data.find("<div class=\"it4\"", idx)
        idx5 = page_data.find("img/r/", idx5) + 6
        idx6 = page_data.find(".gif", idx5)
        chapter_ranking = page_data[idx5:idx6]
      
        print "\n[%s] #%s - %s\nranking:%s, link:%s" % (genre, chapter_id, chapter_name, chapter_ranking, chapter_link)
        do_mirror_chapter(genre, chapter_id, chapter_name, chapter_ranking, chapter_link)
      
        idx = idx + 10
    
      # find next page
      idx = page_data.find("<table class=\"ptt")
      idx2 = page_data.find("</table>", idx)
      nav_data = page_data[idx:idx2]
      next_page_id = -1
    
      idx = 0
      while True:
        idx = nav_data.find("document.location='http://g.e-hentai.org/?", idx)
        idx2 = nav_data.find("\">", idx) - 1
        stxt = nav_data[idx:idx2]
        next_pgid = stxt[47:]
        if "'" not in next_pgid and next_pgid != "":
          next_page_id = int(next_pgid)
        if idx < 0:
          break
      
        idx = idx2
      
      if page_id >= next_page_id:
        print "Everything done!"
        break
      
      page_id = next_page_id
    except:
      traceback.print_exc()
      time.sleep(1)

if len(sys.argv) > 0:
  if sys.argv[1] == "album":
    print "usage: eh_down.py album <album_url> down_folder"
    do_real_mirror_chapter(sys.argv[2], sys.argv[3])
else:
  # TODO config start page
  start_index_page = 0
  start_download_from_index_page(start_index_page)
