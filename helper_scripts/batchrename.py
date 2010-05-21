#!/usr/bin/python

import os
import re

path = raw_input("Path?\n")
filter = raw_input("Regexp filter (for fullname, excluding path, i.e., 'basename.extname')?\n")
file_list = os.listdir(path)
match_list = []
print "list of matched files:"
for file in file_list:
  if re.search(filter, file):
    match_list += file,
    print file

print
print "choices:"
print "1: rename with increasing id"
print "2: rename according to a function"

def pattern_rename(pattern, start_id, dry_run):
  counter = start_id
  rollback_list = []
  try:
    for file in match_list:
      old_basename = os.path.basename(file)
      old_spltname = os.path.splitext(old_basename)
      new_basename = (pattern % counter) + old_spltname[1]
      print "%s  --->  %s" % (old_basename, new_basename)
      if dry_run == False:
        os.rename(path + os.path.sep + old_basename, path + os.path.sep + new_basename)
      rollback_list += (old_basename, new_basename),
      counter += 1
  except:
    if dry_run:
      raise # re-throw
    else:
      print "error occured, rolling back..."
      for pair in rollback_list:
        old_basename = pair[0]
        new_basename = pair[1]
        print "(rollback) %s  --->  %s" % (new_basename, old_basename)
        os.rename(path + os.path.sep + new_basename, path + os.path.sep + old_basename)


def lambda_rename(fun, dry_run):
  exec "fun = lambda x, i: (%s)" % fun
  counter = 0
  rollback_list = []
  try:
    for file in match_list:
      old_basename = os.path.basename(file)
      old_spltname = os.path.splitext(old_basename)
      new_basename = fun(old_spltname[0], counter) + old_spltname[1]
      print "%s  --->  %s" % (old_basename, new_basename)
      if dry_run == False:
        os.rename(path + os.path.sep + old_basename, path + os.path.sep + new_basename)
      rollback_list += (old_basename, new_basename),
      counter += 1
  except:
    if dry_run:
      raise # re-throw
    else:
      print "error occured, rolling back..."
      for pair in rollback_list:
        old_basename = pair[0]
        new_basename = pair[1]
        print "(rollback) %s  --->  %s" % (new_basename, old_basename)
        os.rename(path + os.path.sep + new_basename, path + os.path.sep + old_basename)

choice = raw_input()
if choice == "1":
  print "some hints on renaming pattern:"
  print "%d -> increasing id"
  print "%03d -> increasing id, prepadding by 0"
  print "%% -> % itself"
  print "provide renaming pattern (for basename only):"
  pattern = raw_input()
  print "privide start id[1]:"
  start_id = raw_input()
  if start_id == "":
    start_id = 1
  else:
    start_id = int(start_id)
  print "dry run result (not actually executed):"
  pattern_rename(pattern, start_id, True)
  raw_input("press ENTER to confirm and execute the action...")
  pattern_rename(pattern, start_id, False)
elif choice == "2":
  print "please provide a lambda function f(x, i):"
  print "x: original basename (without ext)"
  print "i: counter (starts from 0)"
  print """eg:\n        "%s_%d" % (x, i)"""
  fun = raw_input("lambda function?\n")
  print "dry run result (not actually executed):"
  lambda_rename(fun, True)
  raw_input("press ENTER to confirm and execute the action...")
  lambda_rename(fun, False)
  
else:
  print "no such choice: '%s'" % choice
