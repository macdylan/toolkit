
source_name = None

f = open("black_list.txt", "a")

print "input base folder name: (danbooru|konachan|moe_imouto|nekobooru)"
print "after that, input image id like '103002' or '104848-104866'"
print "input nothing if you wanna quit"

while True:
  input = raw_input()
  input = input.lower()
  if input == "danbooru":
    source_name = input
  elif input == "konachan":
    source_name = input
  elif input == "moe_imouto":
    source_name = input
  elif input == "nekobooru":
    source_name = input
  elif input == "mypic":
    source_name = input
  elif input == "" or input == "exit" or input == "quit":
    break
  else:
    if "-" in input:
      splt = input.split('-')
      start_id = int(splt[0])
      end_id = int(splt[1])
      f.write("%s %d-%d\n" % (source_name, start_id, end_id))
    else:
      f.write("%s %d\n" % (source_name, int(input)))

f.close()
