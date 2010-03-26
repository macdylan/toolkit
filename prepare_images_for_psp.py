# picks images to "..\for_psp" folder

import os

def prepare_folder(path):
  if os.path.exists(path) == False:
    os.makedirs(path)
    print "[mkdir] " + path

def my_exec(cmd):
  print "[cmd] %s" % cmd
  os.system(cmd)

def conv_image(src, dst):
  dst_folder = os.path.split(dst)[0]
  prepare_folder(dst_folder)
  print src, "==>", dst
  if os.path.exists(dst) == False:
    my_exec("convert -resize 480x480 \"%s\" \"%s\"" % (src, dst))

prepare_folder("..\\for_psp")
img_set = raw_input("image set name: ")
range_txt = raw_input("pic_id range (like 1333-3232): ")
splt = range_txt.split("-")
start_id = int(splt[0])
end_id = int(splt[1])

print "Preparing images %s %d-%d..." % (img_set, start_id, end_id)

sample_dir = "..\\" + img_set + "\\sample"

dirs = os.listdir(sample_dir)
for dir in dirs:
  dir_body = os.path.split(dir)[1].split("-")[0]
  dir_first_id = int(dir_body)
  dir_last_id = dir_first_id + 99
  if not (end_id < dir_first_id or dir_last_id < start_id):
    files = os.listdir(sample_dir + "\\" + dir)
    for file in files:
      file = file.lower()
      if not (file.endswith(".png") or file.endswith(".jpg")):
        continue
      fn_splt = os.path.splitext(file)
      main_fn = fn_splt[0]
      main_id = int(main_fn)
      if not (start_id <= main_id and main_id <= end_id):
        continue
      src_path = sample_dir + "\\" + dir + "\\" + file
      dst_path = "..\\for_psp\\" + img_set + "\\" + dir_body + "\\" + img_set + "_" + str(main_id) + fn_splt[1]
      conv_image(src_path, dst_path)
