#!/usr/bin/env python

# Fancy CBZ file format (1.0):
# based upon .cbz file (zip package of comic pictures)
# 
# decorated .cbz package format:
# /content.json -- where the metadata is saved
# /*.{jpg,png} -- images
# 
# content.json object:
# pic_note:
#   int:x,y,width,height -- location of the note
#   utf8:text -- the note info
# 
# pic_meta:
#   [utf8]:z_path -- zipped name, including path, relative to the root directory, do not start with '/'
#   int:crop_x,crop_y,crop_width,crop_hegiht -- (optional) cropped image size
#   [utf8]:comment -- (optional) picture comment
#   [utf8]:additional_info -- (optional) additional information on the image
#   [pic_note]:notes -- (optional) notes on the picture
# 
# comic_meta:
#   bool:is_fancy_format -- flag to indicate if the cbz is in good format, not written into zip package
#   utf8:ver -- fancy cbz version, currently 'fancy cbz 1.0'
#   utf8:min_ver -- (optional) minimum version required to open the file, currently 'fancy cbz 1.0'
#   utf8:app_name -- (optional) the application that created the cbz file
#   utf8:series -- (optional) the series name
#   utf8:title -- title in the series
#   utf8:author -- (optional) author name
#   utf8:kind -- (optional) "manga" or "comic"?
#   utf8:comment -- (optional) comment on the comic book
#   utf8:country -- (optional)
#   utf8:language -- (optional)
#   pic_meta:front_cover -- (optional)
#   [pic_meta]:images -- list of images, including front & back cover
# 
# falling back on bad-formatted .cbz files:
#   if content.json not found, or version not matched, then fall back to normal cbz files.
#   fallback values:
#   is_fancy_format -> false,
#   ver -> "", min_ver -> "", app_name -> "", series -> "",
#   title -> zip file name, author -> "",
#   comment -> "", country -> "", language -> "",
#   front_cover -> "",
#   images -> ascending list of the picture files in zip package,
#   "" means "Unknown"

import json

UNKNOWN = ""
VERSION_TEXT = "fancy cbz 1.0"

class FancyCBZImage(dict):
  pass

class FancyCBZ(dict):
  
  def __init__(self):
    self["is_fancy_format"] = False
    self["ver"] = VERSION_TEXT
    self["min_ver"] = VERSION_TEXT
    self["app_name"] = "fancycbz.py"
    self["series"] = UNKNOWN
    self["title"] = UNKNOWN
    self["author"] = UNKNOWN
    self["kind"] = UNKNOWN
    self["comment"] = UNKNOWN
    self["country"] = UNKNOWN
    self["language"] = UNKNOWN
    self["front_cover"] = None
    self["images"] = []
  
  def loads(self, txt):
    self.__init__()
    print "TODO!"
  
  def dumps(self):
    txt = "TODO"
    return txt

if __name__ == "__main__":
  cbz = FancyCBZ()
  print json.dumps(cbz)
  f = open("blah.json", "w")
  json.dump(cbz, f)
  f.close()

