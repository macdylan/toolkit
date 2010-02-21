
import pickle

print "loading database"
f = open("md5_db", "rb")
md5_table = pickle.load(f)
f.close()
print "database loaded"

print "input empty line to quit"

while True:
  input = raw_input("md5 value: ")
  input = input.strip()
  if input == "":
    break
  if md5_table.has_key(input):
    print md5_table[input]
  else:
    print "not found"
