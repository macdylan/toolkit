# download manga from http://acg.178.com

import urllib2
import os
import shutil
import sys
from urllib2 import HTTPError

def prepare_folder(path):
  if os.path.exists(path) == False:
    os.makedirs(path)
    try:
      print "[mkdir] " + path
    except:
      pass

print "This script is used to download manga from http://acg.178.com"

#root_page = "http://acg.178.com/mh/k/kanonair.shtml"
if len(sys.argv) > 1:
  root_page = sys.argv[1]
else:
  root_page = raw_input("give me the url of the table of contents page:\n")
print "[downloading]", root_page

page_src = urllib2.urlopen(root_page).read()

idx = page_src.index("var g_comic_name = '") + 20
idx2 = page_src.index("\r\n", idx) - 2
comic_name = page_src[idx:idx2].replace(" ", "").decode("utf-8")

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


# now download chapter
for chap in toc_arr:
  chap_title = chap[0].decode("utf-8")
  chap_href = chap[1]
  prepare_folder("acg178down/" + comic_name + "/" + chap_title)
  idx = root_page.rfind("/")
  idx = root_page[0:idx].rfind("/")
  base_url = root_page[0:idx]
  chap_url = base_url + chap_href[2:]
  
  chap_src = urllib2.urlopen(chap_url).read()
  idx = chap_src.find("var pages") + 13
  idx2 = chap_src.find("\r\n", idx) - 2
  comic_pages_src = chap_src[idx:idx2].replace("\\/", "/")
  comic_pages_url = eval(comic_pages_src)
  
  for pg in comic_pages_url:    
    full_pg = (base_url + "/imgs/" + pg)
    idx = full_pg.rfind("/") + 1
    leaf_nm = full_pg[idx:]
    print leaf_nm
    fn = u"acg178down/" + comic_name + u"/" + chap_title + u"/" + leaf_nm.decode("unicode_escape")
    try:
      print fn
    except:
      pass
    down_filename = fn
    if os.path.exists(down_filename):
      try:
        print "[pass]", down_filename
      except:
        pass
      continue
    down_f = open(fn + u".tmp", "wb")
    full_pg_unescaped = full_pg.decode("unicode_escape").encode("utf-8")
    full_pg_unescaped = full_pg_unescaped.replace(" ", "%20")
    try:
      down_data = urllib2.urlopen(full_pg_unescaped).read()
      down_f.write(down_data)
      down_f.close()
      shutil.move(fn + u".tmp", fn)
    except HTTPError, e:
      down_f.close()
      os.remove(fn + u".tmp")
      error_sign_f = open(fn + u".failed", "w")
      error_sign_f.close()
  
