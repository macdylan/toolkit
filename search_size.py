import pickle

print "loading database"
f = open("size_db", "rb")
jpeg_size_db, original_size_db, sample_size_db = pickle.load(f)
f.close()
print "database loaded"

print "input empty line to quit"

def print_result(result_set, type):
  for result in result_set:
    print "%s (%s)" % (result, type)

while True:
  input = raw_input("image file size: ")
  size = int(input.strip())
  ever_found = False
  if jpeg_size_db.has_key(size):
    ever_found = True
    print_result(jpeg_size_db[size], "jpeg")
  if original_size_db.has_key(size):
    ever_found = True
    print_result(original_size_db[size], "original")
  if sample_size_db.has_key(size):
    ever_found = True
    print_result(sample_size_db[size], "sample")
  if ever_found == False:
    print "not found"
