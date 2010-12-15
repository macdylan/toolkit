#!/usr/bin/env python

# Convertion tools for video, picture, text.
#
# Author: Santa Zhang (santa1987@gmail.com)
#

import sys
import os
import time
import shutil
import shlex
from subprocess import Popen, PIPE, STDOUT
from utils import *
from threading import Thread

class FfmpegThread(Thread):
  
  def __init__(self, manager):
    Thread.__init__(self)
    self.manager = manager
    self.job = None
  
  def get_current_job(self):
    return self.job
  
  def run(self):
    while True:
      self.job = self.manager.request_job(self)
      if self.job == None:
        break

      full_cmd = self.manager.get_ffmpeg_bin() + " " + self.job.get_commandline()
      #print "[new] %s" % full_cmd
      
      # do real job here
      job_folder = os.path.split(self.job.get_output_file())[0]
      cmd_split = shlex.split(full_cmd)
      pipe = Popen(cmd_split, shell=False, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True, cwd=job_folder)
      stdout_output = pipe.stdout.read()
      #print "[done] %s" % full_cmd
      # notify done!
      fin_cb = self.job.get_finish_callback()
      if fin_cb != None:
        fin_cb(self.job)
    self.manager.notify_thread_death(self)

class FfmpegJobManager(Thread):
  
  def __init__(self, ffmpeg_bin):
    Thread.__init__(self)
    self.ffmpeg_bin = ffmpeg_bin
    self.jobs = []
    self.n_threads = int(get_config("n_threads"))
    self.jobs_pending = []
    self.running_threads = []
  
  def get_running_threads(self):
    return self.running_threads
  
  def get_ffmpeg_bin(self):
    return self.ffmpeg_bin
  
  def add_job(self, job):
    self.jobs += job,
    self.jobs_pending += job,
  
  def get_jobs(self):
    return self.jobs
  
  def get_n_threads(self):
    return self.n_threads
  
  def set_n_threads(self, n_threads):
    self.n_threads = n_threads
  
  def start(self):
    self.ensure_running_threads()
  
  def ensure_running_threads(self):
    while len(self.running_threads) < self.n_threads and len(self.jobs_pending) > 0:
      new_thread = FfmpegThread(self)
      self.running_threads += new_thread,
      #print "[info] new thread '%s' created" % str(new_thread)
      new_thread.start()

  def request_job(self, job_thread):
    if self.running_threads.index(job_thread) >= self.n_threads:
      # too many threads runing, kill some
      return None
    elif len(self.jobs_pending) > 0:
      self.ensure_running_threads()
      new_job = self.jobs_pending[0]
      self.jobs_pending = self.jobs_pending[1:]
      return new_job
    else:
      return None
  
  def notify_thread_death(self, job_thread):
    #print "[info] thread '%s' finished" % str(job_thread)
    self.running_threads.remove(job_thread)
  
  def is_done(self):
    if len(self.jobs_pending) == 0 and len(self.running_threads) == 0:
      return True
    else:
      return False


class FfmpegJob:
  
  def __init__(self):
    self.param = {}
    self.input_files = []
    self.output_file = None
    self.status = "new"
    self.finish_callback = None
  
  def set_params(self, params):
    for key in params.keys():
      self.param[key] = params[key]
  
  def set_param(self, key, value=None):
    self.param[key] = str(value)
  
  def get_param(self, key):
    return self.param[key]
  
  def get_params(self):
    return self.param
    
  def set_finish_callback(self, cb):
    self.finish_callback = cb
  
  def get_finish_callback(self):
    return self.finish_callback
  
  def clear_finish_callback(self):
    self.finish_callback = None
  
  def set_status(self, status):
    self.status = status
  
  def get_status(self):
    return self.status
  
  def set_input_files(self, *input_files):
    self.input_files = input_files
  
  def get_input_files(self):
    return self.input_files
  
  def set_output_file(self, output_file):
    self.output_file = output_file
  
  def get_output_file(self):
    return self.output_file
  
  def get_commandline(self):
    cmd_line = "-y " # say yes to all questions
    for input in self.input_files:
      cmd_line += "-i \"%s\" " % input
    for key in self.param.keys():
      cmd_line += "-%s %s " % (key, str(self.param[key]))
    cmd_line += " \"%s\"" % self.output_file
    return cmd_line


def jc_makedirs(path):
  if os.path.exists(path) == False:
    print "[mkdir] %s" % path
    os.makedirs(path)

def jc_get_ffmpeg_info():
  ffmpeg_bin = get_config("ffmpeg_bin")
  info = ''
  pipe = Popen(ffmpeg_bin, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
  lines = pipe.stderr.read()
  for line in lines.splitlines():
    if line.find("version") >= 0 or line.startswith("  "):
      info += line + "\n"
  return info

def jc_ffmpeg_info():
  print jc_get_ffmpeg_info()

def jc_dos2unix_print_help():
  print "convert dos text file to unix text file"
  print "usage: justconvert.py dos2unix <textfile>"

def jc_dos2unix():
  if len(sys.argv) <= 2:
    jc_dos2unix_print_help()
  else:
    fname = sys.argv[2]
    if os.path.exists(fname) == False:
      print "[error] cannot find file '%s'!" % fname
      exit()
    bak_fname = fname + ".bak"
    if os.path.exists(bak_fname):
      i = 1
      while os.path.exists(bak_fname):
        bak_fname =  fname + (".bak.%d" % i)
        i += 1
    print "backup file is '%s'" % bak_fname
    shutil.move(fname, bak_fname)
    if os.path.exists(bak_fname) == False:
      print "[error] failed to create backup file '%s'!" % bak_fname
      exit()
    fin = open(bak_fname)
    fout = open(fname, "w")
    for line in fin.readlines():
      line = line.splitlines()[0]
      fout.write(line + "\n")
    fin.close()
    fout.close()
    print "done converting '%s'" % fname

def jc_make_iphone_ringtone_change_ext_callback(job):
  tmp_fn = job.get_output_file()
  ringtone_fn = os.path.splitext(job.get_input_files()[0])[0] + ".m4r"
  if os.path.exists(tmp_fn):
    print "[done] %s" % ringtone_fn
    os.rename(tmp_fn, ringtone_fn)

def jc_split_ffmpeg_preset(text):
  preset = {}
  splt = text.split(";")
  for sp in splt:
    idx = sp.index(":")
    key = sp[:idx]
    value = sp[(idx + 1):]
    preset[key] = value
  return preset

def jc_make_iphone_ringtone():
  root_dir = raw_input("The folder containing music files? ")
  manager = FfmpegJobManager(get_config("ffmpeg_bin"))
  conv_params = jc_split_ffmpeg_preset(get_config("iphone_ringtone.preset"))
  for fn in os.listdir(root_dir):
    fpath = os.path.join(root_dir, fn)
    if is_music(fn):
      out_fpath = os.path.splitext(fpath)[0] + ".ringtone-tmp.m4a"
      job = FfmpegJob()
      job.set_params(conv_params)
      job.set_finish_callback(jc_make_iphone_ringtone_change_ext_callback)
      job.set_input_files(fpath)
      job.set_output_file(out_fpath)
      manager.add_job(job)
  manager.start()
  while manager.is_done() == False:
    time.sleep(2)
    running = manager.get_running_threads()
    print "[info] %d jobs running now" % len(running)
    all_jobs = manager.get_jobs()
    for th in running:
      print "[info] %d of %d: %s" % (all_jobs.index(th.get_current_job()) + 1, len(all_jobs), th.get_current_job().get_output_file())

def jc_ipod_movie(src_fn, dst_fn):
  jc_makedirs(os.path.split(dst_fn)[0])
  conv_params = jc_split_ffmpeg_preset(get_config("ipod_movie.preset"))
  job = FfmpegJob()
  job.set_params(conv_params)
  job.set_input_files(src_fn)
  job.set_output_file(dst_fn)
  ffmpeg_bin = get_config("ffmpeg_bin")
  full_cmd = "%s %s" % (ffmpeg_bin, job.get_commandline())
  print "[cmd] %s" % full_cmd
  os.system(full_cmd)
  

def jc_psp_movie(src_fn, dst_fn):
  jc_makedirs(os.path.split(dst_fn)[0])
  conv_params = jc_split_ffmpeg_preset(get_config("psp_movie.preset"))
  job = FfmpegJob()
  job.set_params(conv_params)
  job.set_input_files(src_fn)
  job.set_output_file(dst_fn)
  ffmpeg_bin = get_config("ffmpeg_bin")
  full_cmd = "%s %s" % (ffmpeg_bin, job.get_commandline())
  print "[cmd] %s" % full_cmd
  os.system(full_cmd)


def jc_psp_movie_dir(src_dir, dst_dir):
  jc_makedirs(dst_dir)
  print "This shall be done!"

def jc_print_help():
  print "justconvert.py: convertion tools for video, picture & text files"
  print "usage: justconvert.py <command>"
  print
  print "  dos2unix                convert dos text file to unix text file"
  print "  ffmpeg-info             display info about ffmpeg"
  print "  iphone-ringtone         convert m4a and mp3 files into m4r (iphone ringtone)"
  print "  ipod-movie              convert a video to ipod movie (2nd generation)"
  print "  psp-movie               convert a video to psp format"
  print "  psp-movie-dir           convert video in a folder to psp format"
  print "  help                    display this info"
  print
  print "author: Santa Zhang (santa1987@gmail.com)"


if __name__ == "__main__":
  if len(sys.argv) == 1 or sys.argv[1] == "help":
    jc_print_help()
  elif sys.argv[1] == "dos2unix":
    jc_dos2unix()
  elif sys.argv[1] == "ffmpeg-info":
    jc_ffmpeg_info()
  elif sys.argv[1] == "iphone-ringtone":
    jc_make_iphone_ringtone()
  elif sys.argv[1] == "ipod-movie":
    if len(sys.argv) < 4:
      print "usage: justconvert ipod-movie <src_file> <dst_file>"
      print "<dst_file> should have .mp4 as extension"
      exit(0)
    jc_ipod_movie(sys.argv[2], sys.argv[3])
  elif sys.argv[1] == "psp-movie":
    if len(sys.argv) < 4:
      print "usage: justconvert psp-movie <src_file> <dst_file>"
      print "<dst_file> should have .mp4 as extension"
      exit(0)
    jc_psp_movie(sys.argv[2], sys.argv[3])
  elif sys.argv[1] == "psp-movie-dir":
    if len(sys.argv) < 4:
      print "usage: justconvert psp-movie-dir <src_dir> <dst_dir>"
      print "all converted result in <dst_dir> will have .mp4 as extension"
      exit(0)
    jc_psp_movie_dir(sys.argv[2], sys.argv[3])
  else:
    print "command '%s' not understood, see 'justconvert.py help' for more info" % sys.argv[1]

