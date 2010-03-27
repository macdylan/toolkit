import os
import shutil

print 'Copy the images from psp to the "for_psp" folder, then run this script.'


def prepare_folder(path):
  if os.path.exists(path) == False:
    os.makedirs(path)
    print "[mkdir] " + path

black_list_f = open("black_list.txt", "a")

def rank_walker(arg, dirname, files):
  global black_list_f
  folder_name = os.path.split(dirname)[1]
  print "[dir] %s" % dirname
  if folder_name.isdigit() == False:
    return
  folder_start = int(folder_name)
  folder_end = folder_start + 99
  bucket_name = "%d-%d" % (folder_start, folder_end)
  image_set_name = os.path.split(os.path.split(dirname)[0])[1]
  prepare_folder("..\\%s\\rank\\%s" % (image_set_name, bucket_name))
  for f in files:
    f = f.lower()
    if f.endswith(".rank.txt") == False:
      continue
    file_id = int(f.split("_")[-1].split(".")[0])
    
    src = dirname + "\\" + f
    src_f = open(src, "r")
    rank_txt = src_f.read()
    src_f.close()
    rank_txt = rank_txt.strip()
    if rank_txt == "delete":
      print "[black_list] %s %d" % (image_set_name, file_id)
      black_list_f.write("%s %d\n" % (image_set_name, file_id))
    
    dst = "..\\%s\\rank\\%s\\%d.txt" % (image_set_name, bucket_name, file_id)
    if os.path.exists(dst) == False:
      print "[cp] %s ---> %s" % (src, dst)
      shutil.copyfile(src, dst)
    
    
    src_image = dirname + ("\\%s_%d.jpg" % (image_set_name, file_id))
    if os.path.exists(src):
      os.remove(src)
    if os.path.exists(src_image):
      os.remove(src_image)
    

os.path.walk("../for_psp", rank_walker, None)



black_list_f.close()