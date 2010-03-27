# basic items: (img_set_name, start_id, end_id)
# end_id is inclusive

b_list = []
black_f = open("black_list.txt", "r")
for l in black_f.readlines():
  l = l.strip()
  if len(l) == 0:
    continue
  sp1 = l.split()
  img_set_name = sp1[0]
  if "-" in sp1[1]:
    sp2 = sp1[1].split("-")
    begin = int(sp2[0])
    end = int(sp2[1])
    b_item = (img_set_name, begin, end)
    b_list += b_item,
  else:
    v = int(sp1[1])
    b_item = (img_set_name, v, v)
    b_list += b_item,
black_f.close()

def b_item_sort(a, b):
  if a[0] < b[0]:
    return -1
  elif a[0] > b[0]:
    return 1
  else:
    if a[1] < b[1]:
      return -1
    elif a[1] > b[1]:
      return 1
    else:
      if a[2] < b[2]:
        return -1
      elif a[2] > b[2]:
        return 1
      else:
        return 0

b_list.sort(b_item_sort)

print "before shrink, size = %d" % len(b_list)


s_list = []

s_item = None
for item in b_list:
  if s_item == None:
    s_item = item
    continue
  if s_item[0] != item[0]:
    s_list += s_item,
    s_item = item
    continue
  else:
    if s_item[2] + 1 >= item[1]:
      s_item = (s_item[0], s_item[1], item[2])
    else:
      s_list += s_item,
      s_item = item
      continue

s_list += s_item,

print "after shrink, size = %d" % len(s_list)
s_file = open("black_list.shrinked.txt", "w")
for item in s_list:
  if item[1] == item[2]:
    s_file.write("%s %d\n" % (item[0], item[1]))
  else:
    s_file.write("%s %d-%d\n" % (item[0], item[1], item[2]))

print "written to black_list.shrinked.txt"

s_file.close()
