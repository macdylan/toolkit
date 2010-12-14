# batch convert video to psp mp4 format

import sys
import os
import shutil
import time
from threading import Thread
from threading import Lock


max_thread_count = 4

def do_single_file(src, dst):
  dst_folder = os.path.split(dst)[0]
  try:
    os.makedirs(dst_folder)
  except:
    pass
    
  print "%s -> %s" % (src, dst)
  cmd = 'convert_to_psp_mp4.py "%s" "%s"' % (src, dst)
  print cmd
  os.system(cmd)
  if src.lower().endswith(".mkv") and not os.path.exists(os.path.splitext(dst)[0] + ".srt"):
    cmd = 'extract_mkv_srt_psp.py "%s"' % src
    print cmd
    os.system(cmd)
    os.remove(os.path.splitext(src)[0] + ".ssa")
    shutil.move(os.path.splitext(src)[0] + ".srt", os.path.splitext(dst)[0] + ".srt")

class JobThread(Thread):

  def __init__(self, src, dst):
    self.video_src = src
    self.video_dst = dst
    Thread.__init__(self)
  
  def run(self):
    global job_queue
    do_single_file(self.video_src, self.video_dst)
    job_queue.remove_wait_list(self)

def do_single_file_wrapper(src, dst):
  jt = JobThread(src, dst)
  jt.start()
  return jt

class JobQueue(Thread):
  
  def __init__(self):
    self.got_job = False
    self.job_list = []
    self.job_lock = Lock()
    self.wait_list = []
    self.running_job_counter = 0
    Thread.__init__(self)
  
  def add_job(self, src, dst):
    self.got_job = True
    self.job_lock.acquire()
    self.job_list += (src, dst),
    self.job_lock.release()
  
  def pop_job(self):
    self.job_lock.acquire()
    job = None
    if len(self.job_list) > 0:
      job = self.job_list.pop()
    self.job_lock.release()
    return job
  
  def decr_running_job_counter(self):
    self.running_job_counter -= 1
  
  def add_wait_list(self, job_thread):
    self.wait_list += job_thread,
    pass
  
  def remove_wait_list(self, job_thread):
    self.running_job_counter -= 1
    self.wait_list.remove(job_thread)
    pass
  
  def run(self):
    global max_thread_count
    while self.got_job == False:
      time.sleep(1)
    
    while len(self.job_list) > 0:
      if (self.running_job_counter >= max_thread_count):
        time.sleep(1)
      else:
        job = self.pop_job()
        if job != None:
          src, dst = job
          self.running_job_counter += 1
          jt = do_single_file_wrapper(src, dst)
          self.add_wait_list(jt)
    pass
  
  pass

job_queue = JobQueue()

def start_job_queue():
  global job_queue
  job_queue.start()
  
  pass

def add_job_queue(src, dst):
  global job_queue
  job_queue.add_job(src, dst)
  pass

def wait_job_queue():
  global job_queue
  job_queue.join()
  pass
  
def is_video(fname):
  ext_list = [".rmvb", ".mkv", ".avi", ".mp4", ".mpg", ".wmv"]
  for ext in ext_list:
    if fname.lower().endswith(ext):
      return True
  return False

skipped_ext_list = []

def path_walker(arg, dirname, fnames):
  global skipped_ext_list
  src_dir, dst_dir = arg
  
  for f in fnames:
    src = dirname + os.path.sep + f
    if os.path.isdir(src):
      continue
    if is_video(f):
      dst = dst_dir + dirname[len(src_dir):] + os.path.sep + os.path.splitext(f)[0] + ".mp4"
      print "Found video: %s" % dst
      if os.path.exists(dst) == False:
        add_job_queue(src, dst)
      print dst.lower().endswith(".mkv")
      if src.lower().endswith(".mkv") and not os.path.exists(os.path.splitext(dst)[0] + ".srt"):
        cmd = 'extract_mkv_srt_psp.py "%s"' % src
        print cmd
        os.system(cmd)
        os.remove(os.path.splitext(src)[0] + ".ssa")
        shutil.move(os.path.splitext(src)[0] + ".srt", os.path.splitext(dst)[0] + ".srt")
    else:
      ext = os.path.splitext(f)[1]
      if ext not in skipped_ext_list:
        skipped_ext_list += ext,

def do_batch(src_dir, dst_dir):
  global skipped_ext_list
  os.path.walk(src_dir, path_walker, (src_dir, dst_dir))
  print "Skipped non-video extensions:", skipped_ext_list
  pass

if __name__ == "__main__":
  if len(sys.argv) != 3:
    print "Usage: batch_convert_to_psp_mp4 <src_dir> <dst_dir>"
  else:
    start_job_queue()
    do_batch(sys.argv[1], sys.argv[2])
    wait_job_queue()
