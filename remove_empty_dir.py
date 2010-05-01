import os

def ReallyEmpty(fnames):
  for f in fnames:
    if (f.startswith("AlbumArt") and f.endswith(".jpg")):
      continue
    elif (f == "Folder.jpg"):
      continue
    elif (f.lower() == "thumb.db"):
      continue
    else:
      return False
  return True

def Walker(arg, dir, fnames):
  if (ReallyEmpty(fnames)):
    print dir
    for f in fnames:
      os.remove(dir + os.path.sep + f)
    os.rmdir(dir)

def RemoveEmptyFolder(root):
  os.path.walk(root, Walker, None)

if __name__ == "__main__":
  root = raw_input("Root path?[" + os.getcwd() + "]\n")
  if (root == ""):
    root = os.getcwd()
  RemoveEmptyFolder(root)
