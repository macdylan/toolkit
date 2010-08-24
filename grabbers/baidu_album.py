#!/usr/bin/python
# download manga from baidu album

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

def image_id_in_url(url):
	idx = url.rfind("/") + 1
	idx2 = url.rfind(".")
	return url[idx:idx2]

print "This script is used to download manga from baidu albums"

downloaded_images = []

first_page = raw_input("Give me the URL of first page inside album\n")

cur_page = first_page
while True:
	print "[page] %s" % cur_page
	page_src = urllib2.urlopen(cur_page).read()
	
	idx = page_src.find("albumName: ")
	idx2 = page_src.find("\n", idx)
	find_sec = page_src[idx:idx2]
	idx = find_sec.find("'") + 1
	idx2 = find_sec.rfind("'")
	album_name = find_sec[idx:idx2]
	print "[album] %s" % album_name
	
	idx = cur_page.find("/", 10) + 1
	idx2 = cur_page.find("/", idx + 1)
	album_owner = cur_page[idx:idx2]
	print "[owner] %s" % album_owner
	
	match_list = []
	idx2 = 0
	while True:
		idx = page_src.find("photoLists.push", idx2)
		if idx == -1:
			break
		idx2 = page_src.find("});", idx)
		info_sec = page_src[idx:idx2]
		image_id = info_sec[24:48]
		idx3 = info_sec.find(",", 54)
		pic_sn = int(info_sec[58:idx3])
		match_list += (image_id, pic_sn),
		
		if image_id == image_id_in_url(cur_page):
			downloaded_images += image_id, 
			prepare_folder("baidu_album" + os.path.sep + album_name)
			idx = cur_page.rfind(".")
			img_url = "http://hiphotos.baidu.com/" + album_owner + "/pic/item/" + image_id + ".jpg"
			print "[img] %d.jpg: %s" % (pic_sn, img_url)
			fn = "baidu_album" + os.path.sep + album_name + os.path.sep + ("%d.jpg" % pic_sn)
			try:
				if os.path.exists(fn):
					print "already downloaded, skip"
				else:
					down_f = open(fn + ".tmp", "wb")
					down_data = urllib2.urlopen(img_url).read()
					down_f.write(down_data)
					down_f.close()
					shutil.move(fn + u".tmp", fn)
			except HTTPError, e:
				down_f.close()
				os.remove(fn + u".tmp")
				error_sign_f = open(fn + u".failed", "w")
				error_sign_f.close()
	
	redirected = False
	for m in match_list:
		if m[0] not in downloaded_images:
			idx = cur_page.rfind("/") + 1
			cur_page = cur_page[:idx] + m[0] + ".html"
			redirected = True
			break
	if redirected == False:
		break
		