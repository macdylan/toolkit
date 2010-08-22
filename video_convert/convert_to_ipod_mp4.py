# convert video to ipod mp4 format

import sys
import os

def do_convert(src, dst):
  print "convert job:"
  print "source:   %s" % src
  print "dest:     %s" % dst
  
  ffmpeg_args = []
  
  ffmpeg_args += '-i "%s"' % src,
  ffmpeg_args += '-y',  # yes to all prompts
  ffmpeg_args += "-r 29.97",
  ffmpeg_args += "-ac 2", # audio 2 channels?
  ffmpeg_args += "-vcodec libx264",
  ffmpeg_args += "-s 640x480",
  ffmpeg_args += "-b 2500k", # video bit rate 2500k
  ffmpeg_args += "-acodec libfaac",
  ffmpeg_args += "-ar 44100",
  ffmpeg_args += "-ab 160k", # audio bit rate 160k
  ffmpeg_args += '"%s"' % dst,
  
  ffmpeg_cmd = "d:\\tools\\ffmpeg\\ffmpeg"
  for arg in ffmpeg_args:
    ffmpeg_cmd += " " + arg
  
  print ffmpeg_cmd
  os.system(ffmpeg_cmd)

if __name__ == "__main__":
  if len(sys.argv) != 3:
    print "Usage: convert_to_ipod_mp4.py <src> <dst>"
  else:
    do_convert(sys.argv[1], sys.argv[2])
