# convert video to mp4 format

import sys
import os
import re

def detect_audio_info(line, info):
  splt = map(str.strip, line[6:].split(","))
  for item in splt:
    if item.lower().endswith("hz"):
      splt2 = item.split()
      info["ar"] = int(splt2[0])  # audio sample rate
    if item.lower().endswith("kb/s"):
      splt2 = item.split()
      info["ab"] = int(splt2[0])  # audio bit rate

def detect_video_info(line, info):
  splt = map(str.strip, line[6:].split(","))
  for item in splt:
    if re.match("[0-9]*x[0-9]*", item):
      info["s"] = item
    if item.lower().endswith("kb/s"):
      splt2 = item.split()
      info["b"] = int(splt2[0])  # audio bit rate

def detect_media_info(fname):
  # popen4 could get stderr
  p = os.popen4('ffmpeg -i "%s"' % fname)
  info = {}
  for l in p[1].readlines():
    
    # search Audio info
    m = re.search("Audio.*Hz.*$", l)
    if m != None:
      detect_audio_info(m.group(0), info)
      
    # search Video info
    m = re.search("Video.*x.*$", l)
    if m != None:
      detect_video_info(m.group(0), info)
  p[1].close()
  return info

def find_arg(val, candidate):
  ret = candidate[0]
  for candi in candidate:
    if candi >= val:
      ret = candi
      break
  return ret

def do_convert(src, dst):
  print "convert job:"
  print "source:   %s" % src
  print "dest:     %s" % dst
  
  video_bit_rate_candidate = [256, 384, 512, 758, 1000, 1200]
  video_bit_rate_candidate.sort()
  
  audio_bit_rate_candidate = [64, 80, 96, 112, 128, 160, 192]
  audio_bit_rate_candidate.sort()
  
  info = detect_media_info(src)
  
  ffmpeg_args = []
  
  ffmpeg_args += '-i "%s"' % src,
  ffmpeg_args += "-y",   # yes to all prompts
  
  ffmpeg_args += "-r 29.97",
  ffmpeg_args += "-ac 2",
  ffmpeg_args += "-aspect 16:9",
  ffmpeg_args += "-vcodec libx264",
  ffmpeg_args += "-s 480x272",  # fixed output video size = 480x272
  
  ffmpeg_args += "-b 1200k",
  
  ffmpeg_args += "-acodec libfaac",
  # set audio sample rate
  ffmpeg_args += "-ar 44100",
  
  ffmpeg_args += "-ab 160k",
  
  ffmpeg_args += "-f psp", # video container format
  
  ffmpeg_args += '"%s"' % dst,
  
  ffmpeg_cmd = "d:\\tools\\ffmpeg\\ffmpeg"
  for arg in ffmpeg_args:
    ffmpeg_cmd += " "
    ffmpeg_cmd += arg
  
  print
  print "============="
  print ffmpeg_cmd
  os.system(ffmpeg_cmd)

if __name__ == "__main__":
  if len(sys.argv) != 3:
    print "Usage: convert_to_psp_mp4.py <src> <dst>"
  else:
    do_convert(sys.argv[1], sys.argv[2])