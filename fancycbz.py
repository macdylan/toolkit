#!/usr/bin/env python

# Fancy CBZ file format (1.0):
# based upon .cbz file (zip package of comic pictures)
#
# decorated .cbz package format:
# /content.json -- where the metadata is saved
# /*.{jpg,png} -- images
#
# content.json object:
#
# comic_book:
#   utf8: ver -- fancy cbz format version, "1.0"
#   utf8: min_ver -- minimum version required to open the file, default "1.0"
#   utf8: app_name -- (optional) the application that created the cbz file
#   utf8: series -- (optional) the series name
#   utf8: title -- the book title
#   utf8: author -- (optional) author name
#   utf8: kind -- (optional) "manga", "comic"
#   utf8: comment -- (optional) comment for the book
#   utf8: country -- (optional)
#   utf8: language -- (optional)
#   utf8: front_cover -- (optional) front cover file name
#   utf8: padding -- (optional) fill up the file with " "
#   [utf8]: images
#
# falling back on bad-formatted .cbz files:
#   if content.json not found, or version not matched, then fall back to normal cbz files.
#   fallback values:
#   is_fancy_format -> false,
#   ver -> "", min_ver -> "", series -> "",
#   title -> zip file name, author -> "",
#   comment -> "",
#   front_cover -> "",
#   images -> ascending list of the picture files in zip package,
#   "" means "Unknown"

import os
import json
import zipfile
import time
import shutil
import binascii
import struct
import datetime

class CbzFile:

  UNKNOWN = ""
  VERSION = "1.0"
  MIN_CONTENT_SIZE = 4096
  CONTENT_FNAME = "content.json"

  def __init__(self, fpath = None):
    self.meta = {}
    self.meta["ver"] = CbzFile.VERSION
    self.meta["min_ver"] = CbzFile.VERSION
    self.f_meta_sz = -1
    self.f = None
    self.fpath = None
    # list of current files
    self.cur_f_list = []
    # list of file to be added
    self.add_f_list = []  # pair: (local_fpath, cbz_fname)
    self.dirty = False

    if fpath != None:
      self.open(fpath)

  def __str__(self):
    json_txt = json.dumps(self.meta, sort_keys=True, indent=2)
    return json_txt

  def open(self, fpath):
    if self.f != None:
      self.close()
    self.fpath = fpath

    if os.path.exists(fpath) == False:
      # create an empty zip file
      zipf = zipfile.ZipFile(fpath, "w")
      tempfn = self.fpath + "~" + CbzFile.CONTENT_FNAME + "~"
      tempf = open(tempfn, "wb")
      tempf.write(" " * CbzFile.MIN_CONTENT_SIZE)
      zipf.write(tempfn, CbzFile.CONTENT_FNAME, zipfile.ZIP_STORED)
      tempf.close()
      os.remove(tempfn)
      zipf.close()

    # open by zipfile, load file info
    zipf = zipfile.ZipFile(fpath, "r")
    namelst = zipf.namelist()
    if len(namelst) == 0 or namelst[0] != CbzFile.CONTENT_FNAME:
      raise Exception("%s not found at head of cbz package!" % CbzFile.CONTENT_FNAME)
    infolst = zipf.infolist()
    self.f_meta_sz = infolst[0].compress_size

    # load json info!
    json_txt = zipf.read(CbzFile.CONTENT_FNAME)
    try:
      self.meta = json.loads(json_txt.strip())
    except:
      pass

    zipf.close()
    self.cur_f_list = namelst

    self.fpath = fpath
    self.f = open(fpath, "r+")


  def save(self):
    if self.dirty == False:
      pass
    # determine the size of content_json
    content_json = str(self) + "\n"
    content_sz = CbzFile.MIN_CONTENT_SIZE
    while True:
      if content_sz >= len(content_json):
        break
      else:
        content_sz *= 2
    padding_sz = content_sz - len(content_json)
    padding_row = " " * 80 + "\n"
    padding_row_n = padding_sz / len(padding_row) + 1
    content_json += padding_row * padding_row_n
    content_json = content_json[:content_sz]

    size_diff = len(content_json) - self.f_meta_sz

    zip_header_sz = 30 # first 30 bytes not modified
    if len(content_json) != self.f_meta_sz:
      # need to re-pack the zip file
      #print "repack"
      repack_fn = self.fpath + "~repack~"
      repack_f = open(repack_fn, "wb")
      self.f.seek(0, os.SEEK_SET)
      repack_f.write(self.f.read(zip_header_sz + len(CbzFile.CONTENT_FNAME)))
      repack_f.write(content_json)
      #print "old meta size = %d, new meta size = %d" % (self.f_meta_sz, len(content_json))
      self.f.seek(zip_header_sz + len(CbzFile.CONTENT_FNAME) + self.f_meta_sz, os.SEEK_SET)
      copy_bytes = 0
      while True:
        buf = self.f.read(1024 * 1024 * 4)
        copy_bytes += len(buf)
        if buf == "":
          break
        repack_f.write(buf)
      #print "copied bytes: %d" % copy_bytes
      repack_f.close()
      self.f.close()
      shutil.move(repack_fn, self.fpath)
      self.f = open(self.fpath, "r+")
      self.f_meta_sz = len(content_json)
    else:
      # in place edit
      self.f.seek(zip_header_sz + len(CbzFile.CONTENT_FNAME), os.SEEK_SET)
      self.f.write(content_json)

    # modify time & date
    mtime = time.localtime()
    dt = mtime[0:6]
    dosdate = (dt[0] - 1980) << 9 | dt[1] << 5 | dt[2]
    dostime = dt[3] << 11 | dt[4] << 5 | (dt[5] // 2)


    # edit content.json's crc32 value, file size
    content_crc = binascii.crc32(content_json, 0)
    content_crc_binary = struct.pack("i", content_crc)
    self.f.seek(10, os.SEEK_SET)
    self.f.write(struct.pack("H", dostime))
    self.f.write(struct.pack("H", dosdate))
    self.f.write(content_crc_binary)
    fsize_binary = struct.pack("i", self.f_meta_sz)
    self.f.write(fsize_binary)
    self.f.write(fsize_binary)

    #print "-" * 80
    # jump to central directory's first item, that is, "content.json"
    self.f.seek(0, os.SEEK_SET)
    start_of_central_dir = -1
    while True:
      rec_start = self.f.tell()
      buf = None
      buf = self.f.read(4)
      if buf == "PK\03\04":
        self.f.seek(rec_start + 18, os.SEEK_SET)
        compress_size = struct.unpack("i", self.f.read(4))[0]
        self.f.seek(rec_start + 26, os.SEEK_SET) # skip one value
        fname_len = struct.unpack("h", self.f.read(2))[0]
        extra_filed_len = struct.unpack("h", self.f.read(2))[0]
        self.f.seek(rec_start + 30 + compress_size + fname_len + extra_filed_len, os.SEEK_SET)
      elif buf == "PK\01\02":

        self.f.seek(rec_start + 28, os.SEEK_SET)
        fname_len = struct.unpack("i", self.f.read(4))[0]
        self.f.seek(rec_start + 46, os.SEEK_SET)

        #print "fentry=%s" % self.f.read(fname_len)

        if start_of_central_dir < 0:
          # first central dir -> content.json
          # now we could edit the other crc32
          self.f.seek(rec_start + 12, os.SEEK_SET)
          self.f.write(struct.pack("H", dostime))
          self.f.write(struct.pack("H", dosdate))
          self.f.write(content_crc_binary)
          self.f.write(fsize_binary)
          self.f.write(fsize_binary)
          self.f.seek(rec_start + 28, os.SEEK_SET)
          fname_len = struct.unpack("i", self.f.read(4))[0]
          self.f.seek(rec_start + 46, os.SEEK_SET)

          if self.f.read(fname_len) != CbzFile.CONTENT_FNAME:
            raise Exception("%s not in correct position!" % CbzFile.CONTENT_FNAME)

          start_of_central_dir = rec_start
          #print "start of central dir = %d" % start_of_central_dir

        else:
          # no first central dir
          # update local offset header
          self.f.seek(rec_start + 42, os.SEEK_SET)
          orig_offset = struct.unpack("i", self.f.read(4))[0]
          new_offset = orig_offset + size_diff
          self.f.seek(rec_start + 42, os.SEEK_SET)
          self.f.write(struct.pack("i", new_offset))

        self.f.seek(rec_start + 28, os.SEEK_SET)
        skip = 0
        skip += struct.unpack("h", self.f.read(2))[0]
        skip += struct.unpack("h", self.f.read(2))[0]
        skip += struct.unpack("h", self.f.read(2))[0]
        self.f.seek(rec_start + 46 + skip, os.SEEK_SET)
      elif buf == "PK\05\6":
        # end of central directory

        self.f.seek(rec_start + 16, os.SEEK_SET)
        old_start_pos = struct.unpack("i", self.f.read(4))[0]
        if old_start_pos != start_of_central_dir:
          pass
          #print "old pos = %d, new pos = %d, diff = %d" % (old_start_pos, start_of_central_dir, start_of_central_dir - old_start_pos)
        self.f.seek(rec_start + 16, os.SEEK_SET)
        if start_of_central_dir < 0:
          raise Exception("invalid start of central directory position!")
        self.f.write(struct.pack("i", start_of_central_dir))
        break
      else:
        raise Exception("invalid zip format!")
    self.f.flush()

    # now add images
    zipf = zipfile.ZipFile(self.fpath, "a")
    for fname_pair in self.add_f_list:
      local_fpath, cbz_fpath = fname_pair
      if os.path.exists(local_fpath) == False:
        raise Exception("file '%s' not found!" % local_fpath)
      zipf.write(local_fpath, cbz_fpath, zipfile.ZIP_STORED)
    zipf.close()

    self.dirty = False

  def close(self):
    if self.f != None:
      self.save()
      self.f.close()

    # finalize values
    self.f = None
    self.fpath = None
    self.f_meta_sz = -1
    self.cur_f_list = []
    self.add_f_list = []

  def set_title(self, title):
    self.dirty = True
    self.meta["title"] = title

  def set_author(self, author):
    self.dirty = True
    self.meta["author"] = author

  def set_comment(self, comment):
    self.dirty = True
    self.meta["comment"] = comment

  def set_series(self, series):
    self.dirty = True
    self.meta["series"] = series

  def set_cover(self, cover):
    self.dirty = True
    self.meta["cover"] = cover

  def set_info(self, key, value):
    if key != "ver" and key != "min_ver" and key != "images":
      self.meta[key] = value
    else:
      raise Exception("key '%s' is reserved!" % key)
    self.dirty = True

  def get_info(self, key):
    if self.meta.has_key(key):
      return self.meta[key]
    else:
      return None

  def add_image(self, local_fpath, cbz_fname = None):
    if cbz_fname == None:
      cbz_fname = os.path.split(local_fpath)[1]
    if self.meta.has_key("images") == False:
      self.meta["images"] = []
    if cbz_fname in self.cur_f_list:
      raise Exception("archive filename '%s' already exists" % cbz_fname)
    for add_entry in self.add_f_list:
      if cbz_fname == add_entry[1]:
        raise Exception("archive filename '%s' already exists" % cbz_fname)

    self.meta["images"] += cbz_fname,
    self.add_f_list += (local_fpath, cbz_fname),
    self.dirty = True


if __name__ == "__main__":
  cbz = CbzFile()
  cbz.open("/Users/santa/Downloads/dummy.cbz")
  print cbz.get_info("author")
  cbz.set_title("title")
  cbz.set_author("Auqaplus")
  cbz.set_comment("# NO COMMENT")
  cbz.set_series("To Heart 2")
  cbz.close()
  for root, folders, files in os.walk("/Users/santa/Downloads/t"):
    for fn in files:
      if fn.endswith(".jpg") == False:
        continue
      fpath = os.path.join(root, fn)
      cbz.open("/Users/santa/Downloads/dummy.cbz")
      cbz.add_image(fpath)
      print cbz.get_info("author")
      cbz.set_cover("images/a.jpg")
      print cbz.get_info("cover")
      cbz.close()


