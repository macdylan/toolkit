
# usage: load_black_list("moe_imouto")
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
