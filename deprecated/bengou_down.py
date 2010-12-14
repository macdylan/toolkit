# download manga from http://www.bengou.com

import urllib2
import os
import shutil
import sys
from urllib2 import HTTPError

def util_make_dirs(path):
  if os.path.exists(path) == False:
    print "[mkdir] %s" % path
    os.makedirs(path)

def down_page(page_url, down_dir, page_id):
  print page_url, down_dir, page_id
  page_src = urllib2.urlopen(page_url).read()
  
  # get pic url:
  idx = page_src.index('"disp"')
  idx = page_src.index('http://', idx)
  idx2 = page_src.index('"', idx)
  img_url = page_src[idx:idx2]
  print "[img] %s" % img_url
  
  # download pic:
  img_ext = img_url[img_url.rfind("."):]
  pic_fn = down_dir + os.path.sep + ("%03d" % page_id) + img_ext
  if os.path.exists(pic_fn):
    print "[skip] %s" % pic_fn
  else:
    try:
      pic_data = urllib2.urlopen(img_url).read()
      pic_f = open(pic_fn, "wb")
      pic_f.write(pic_data)
      pic_f.close()
    except HTTPError, e:
      print "[failure] %s" % pic_fn
      f = open(pic_fn + ".failed", "w")
      f.close()

def down_vol(vol_url, down_dir):
  print "[vol] %s" % vol_url
  page_src = urllib2.urlopen(vol_url).read()
  root_url = vol_url[:vol_url.rfind("/")]
  
  # get pic tree
  idx = page_src.index("var pictree")
  idx2 = page_src.index(";", idx)
  pictree_src = page_src[(idx + 14):idx2]
  exec "pictree=%s" % pictree_src
  counter = 1
  for pic in pictree:
    down_page(root_url + "/" + pic, down_dir, counter)
    counter += 1
  

def down_manga(index_url):
  page_src = urllib2.urlopen(index_url).read()
  
  index_root = index_url[:index_url.rfind("/")]
  
  # find manga name
  idx = page_src.index("sectioninfo ")
  idx = page_src.index("title=", idx)
  idx2 = page_src.index('"', idx + 7)
  comic_name = page_src[(idx + 7):idx2].decode("utf-8")
  print "ComicName=%s" % comic_name

  # find the volumes
  idx = page_src.index("mhlist")
  idx2 = page_src.index("</div>", idx)
  mhlist_src = page_src[idx:idx2]
  
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
    print "Vol: %s=%s" % (vol_name, vol_url)
    down_dir = "bengou" + os.path.sep + comic_name + os.path.sep + vol_name
    util_make_dirs(down_dir)
    down_vol(vol_url, down_dir)
    
if __name__ == "__main__":
  print "please input the manga's directory url:"
  comic_index = raw_input()
  down_manga(comic_index)
