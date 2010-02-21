print "input empty line to quit"

while True:
  input = raw_input("image name: ")
  if input == "":
    break
  splt = input.split()
  img_set = splt[0]
  id = int(splt[1])
  
  bucket_size = 100
  bucket_id = id / bucket_size
  bucket_name = "%d-%d" % (bucket_id * bucket_size, bucket_id * bucket_size + bucket_size - 1)
  fpath = "../" + img_set + "/tags/" + bucket_name + "/" + str(id) + ".txt"
  f = open(fpath)
  print "tags:"
  print
  for l in f.readlines():
    print l.strip()
  print
  f.close()
  