#!/usr/bin/env python

# Utility to aid coding.
#
# Author: Santa Zhang (santa1987@gmail.com)
#

import sys
import os
import time

# matched by "lowercase(), then endswith()"
g_code_files = [".c", ".cc", ".rb", ".py", "Rakefile"]

# if filter == [], then all files are matched
def check_filter_match(fname, filter = []):
  if len(filter) == 0:
    return True
  for flt in filter:
    if fname.lower().endswith(flt):
      return True

# iterate an action on all matched files
def do_on_each_file(start_path, func_action, filter = []):
  if os.path.isdir(start_path):
    for fn in os.listdir(start_path):
      if fn == "." or fn == "..":
        continue
      do_on_each_file(os.path.join(start_path, fn), func_action, filter)
  else:
    # single file
    if check_filter_match(start_path, filter):
      func_action(start_path)

def action_clear_ws(fpath):
  f = open(fpath, "r")
  lines = f.readlines()
  f.close()
  f = open(fpath, "w")
  for line in lines:
    line = line.rstrip()
    f.write(line)
    f.write("\n")
    print line
  f.close()

# clear trailing whitespace
def kd_clear_ws():
  global g_code_files
  if len(sys.argv) < 3:
    print "Usage: ./coding clear-ws <file_or_folder>"
    exit(0)
  start_path = sys.argv[2]
  do_on_each_file(start_path, action_clear_ws, g_code_files)
  print "--------"
  print "finished"

# replace leading tabs in a line
def line_replace_tab(line):
  if line.startswith("\t"):
    line = "  " + line_replace_tab(line[1:])
  return line

# replace leading tabs in a file
def action_replace_tab(fpath):
  f = open(fpath, "r")
  lines = f.readlines()
  f.close()
  f = open(fpath, "w")
  for line in lines:
    line = line.rstrip()
    line = line_replace_tab(line)
    f.write(line)
    f.write("\n")
    print line
  f.close()


# replace leading tab to 2 spaces
def kd_replace_tab():
  global g_code_files
  if len(sys.argv) < 3:
    print "Usage: ./coding clear-ws <file_or_folder>"
    exit(0)
  start_path = sys.argv[2]
  do_on_each_file(start_path, action_replace_tab, g_code_files)
  print "--------"
  print "finished"

def action_check_style(fpath):
  b_leading_tab = False
  b_trailing_ws = False
  f = open(fpath, "r")
  for line in f.readlines():
    line = line.strip("\n")
    if line.startswith("\t"):
      b_leading_tab = True
    if line.endswith(" ") or line.endswith("\t"):
      b_trailing_ws = True
    if b_trailing_ws and b_leading_tab:
      break
  f.close()
  if b_trailing_ws:
    print "[trailing ws]",
  if b_leading_tab:
    print "[leading tab]",
  if b_leading_tab or b_trailing_ws:
    print fpath

# check coding style
def kd_check_style():
  global g_code_files
  if len(sys.argv) < 3:
    print "Usage: ./coding check-style <file_or_folder>"
    exit(0)
  start_path = sys.argv[2]
  do_on_each_file(start_path, action_check_style, g_code_files)
  print "--------"
  print "finished"

def kd_help():
  print "coding.py: utility to aid coding"
  print "usage: coding.py <command>"
  print "available commands:"
  print
  print "  check-style        Check coding style"
  print "  clear-ws           Clear trailing whitespace"
  print "  replace-tab        Replace leading tab to space"
  print
  print "author: Santa Zhang <santa1987@gmail.com>"

if __name__ == "__main__":
  if len(sys.argv) == 1 or sys.argv[1] == "help":
    kd_help()
  elif sys.argv[1] == "check-style":
    kd_check_style()
  elif sys.argv[1] == "clear-ws":
    kd_clear_ws()
  elif sys.argv[1] == "replace-tab":
    kd_replace_tab()
  else:
    print "command '%s' not understood, see 'coding.py help' for more info" % sys.argv[1]

