import sys
import os
import time

def get_config(key):
  conf_fn = os.path.splitext(sys.argv[0])[0] + ".conf"
  value = None
  
  f = None
  try:
    f = open(conf_fn)
    for line in f.readlines():
      line = line.strip()
      if line.startswith(";") or line.startswith("#") or line == "":
        continue
      idx = line.find("=")
      if idx < 0:
        continue
      if key == line[:idx]:
        value = line[(idx + 1):]
        break
  finally:
    if f != None:
      f.close()
      
  if value == None:
    raise Exception("Config '%s' not found!" % key)
  else:
    return value

def is_hex(text):
  text = text.lower()
  for c in text:
    if ('0' <= c and c <= '9') or ('a' <= c and c <= 'f'):
      continue
    else:
      return False
  return True

def write_log(text):
  print text
  log_fn = os.path.splitext(sys.argv[0])[0] + ".log"
  f = open(log_fn, "a")
  tm = time.strftime("%Y.%m.%d %H:%M:%S", time.localtime())
  f.write("[%s] %s\n" % (tm, text))
  f.close()

