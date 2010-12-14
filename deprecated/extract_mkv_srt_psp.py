# extract subtitle for psp
 
import sys
import os
 
def drop_effect(line):
  plain = ""
  level = 0
  for c in line:
    if level == 0:
      if c == "{":
        level += 1
      else:
        plain += c
    else:
      if c == "}":
        level -= 1
  plain.replace("\\N", " ")
  return plain
 
def split_ssa_line(line):
  
  comma_to_split = 9
  lst = []
  while (comma_to_split > 0):
    index = line.find(',')
    seg = line[:index]
    line = line[index + 1:]
    lst += seg,
    comma_to_split -= 1
  lst += drop_effect(line),
  return lst
 
def ssa_to_srt(ssa):
  seg = split_ssa_line(ssa)
  srt = ""
  srt += seg[4] + "\n"
  srt += seg[1] + " --> " + seg[2] + "\n"
  srt += seg[9]
  return srt
  
def make_psp_srt_from_ssa(fname):
  ssa = open(fname)
  srt = open(fname[:-4] + ".srt", "w")
  for l in ssa.readlines():
    srt.write(ssa_to_srt(l) + "\n")
  srt.close()
  ssa.close()
 
def extract_ssa_from_mkv(fname):
  os.system('ffmpeg -y -i "' + fname + '" -an -vn -scodec copy -f rawvideo "' + fname[:-4] + '.ssa');
  return fname[:-4] + ".ssa"
  
 
if __name__ == "__main__":
  make_psp_srt_from_ssa(extract_ssa_from_mkv(sys.argv[1]));