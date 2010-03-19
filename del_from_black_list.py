# delete images from black list

import shutil
import os

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

def prepare_folder(path):
  if os.path.exists(path) == False:
    os.makedirs(path)
    print "[mkdir] " + path

def del_walker(arg, dir, files):
  global black_list
  branch_name, dust_bin = arg
  print "[dir] %s" % dir
  for f in files:
    fpath = dir + "/" + f
    if os.path.isdir(fpath):
      continue
    sp = os.path.splitext(f)
    main_fn = sp[0]
    if main_fn.isdigit() == False:
      continue
    id = int(main_fn)
    if id in black_list:
      print "[del] %s %d" % (branch_name, id)
      src = fpath
      dest = dust_bin + "/" + branch_name + " " + f
      print "[cmd] mv %s ====> %s" % (src, dest)
      shutil.move(src, dest)
    

def do_del_branch(branch_name, img_set_folder):
  if os.path.exists(img_set_folder + "/" + branch_name):
    os.path.walk(img_set_folder + "/" + branch_name, del_walker, (branch_name, img_set_folder + "/deleted"))

def do_del(img_set_name, img_set_folder):
  global black_list
  black_list = load_black_list(img_set_name)
  prepare_folder(img_set_folder + "/deleted")
  do_del_branch("info", img_set_folder)
  do_del_branch("jpeg", img_set_folder)
  do_del_branch("original", img_set_folder)
  do_del_branch("preview", img_set_folder)
  do_del_branch("sample", img_set_folder)
  do_del_branch("tags", img_set_folder)

do_del("nekobooru", "../nekobooru")
do_del("moe_imouto", "../moe_imouto")
do_del("konachan", "../konachan")
do_del("danbooru", "../danbooru")
