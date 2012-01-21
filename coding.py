#!/usr/bin/env python

# Utility to aid coding.
#
# Author: Santa Zhang (santa1987@gmail.com)
#

import sys
import os
import time

# matched by "lowercase(), then endswith()"
g_code_files = [".c", ".cc", ".rb", ".py", "Rakefile", ".mm", ".html", ".htm", ".tex"]

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
        print "usage: ./coding.py clear-ws <file_or_folder>"
        exit(0)
    start_path = sys.argv[2]
    do_on_each_file(start_path, action_clear_ws, g_code_files)
    print "--------"
    print "finished"

# replace leading tabs in a line
def line_replace_tab(line):
    if line.startswith("\t"):
        line = "    " + line_replace_tab(line[1:])
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
        print "usage: ./coding.py clear-ws <file_or_folder>"
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
        print "usage: ./coding.py check-style <file_or_folder>"
        exit(0)
    start_path = sys.argv[2]
    do_on_each_file(start_path, action_check_style, g_code_files)
    print "--------"
    print "finished"


def kd_py4tab():
    print "This shall be done!"
    if len(sys.argv) < 3:
        print "usage: ./coding.py py-4tab-fy <py-file>"
        exit(0)
    pyfpath = sys.argv[2]
    print "analyzing %s" % pyfpath

    def leading_ws_count(l):
        indent = 0
        while indent < len(l) and l[indent] == ' ':
            indent += 1
        return indent

    # 1st pass, find out indents in target file
    indent_set = set()
    f = open(pyfpath)
    for l in f.readlines():
        l = l.strip("\n")
        if l.endswith(" ") or l.endswith("\t"):
            print "*** trailing whitespace found! please clear them first!"
            exit(1)
        if l.startswith("\t"):
            print "*** leading tab found! please clear them first!"
            exit(1)
        indent = leading_ws_count(l)
        indent_set.add(indent)
    f.close()
    print "indents:", list(indent_set)

    if 2 not in indent_set:
        print "no 2-space indent found, quitting"
        exit(0)

    print "2-space indent found, will fix"

    # fix for per-lv1-function
    f = open(pyfpath)

    g = open(pyfpath + ".4tab-fix", "w")
    line_buf = []

    def fix_line_buf():
        fix_needed = False
        for l in line_buf:
            indent = leading_ws_count(l)
            if indent == 2:
                fix_needed = True
                break
        if not fix_needed:
            for l in line_buf:
                g.write(l + "\n")
            return

        print "----"
        for l in line_buf:
            indent = leading_ws_count(l)
            print "%-6s|%s" % (("%d>%d " % (indent, indent * 2)), l)
            fixed_line = (" " * (indent * 2)) + l[indent:]
            g.write(fixed_line + "\n")
        print "----"

    for line in f.readlines():
        line = line.strip("\n")
        if len(line) == 0:
            line_buf += line,
            continue
        if line.startswith("#"):
            line_buf += line,
            continue
        if line.startswith(" "):
            line_buf += line,
            continue
        if line.startswith("def"):
            fix_line_buf()
            line_buf = []
        line_buf += line,

    fix_line_buf()
    g.close()
    f.close()


def kd_help():
    print """coding.py: utility to aid coding
usage: coding.py <command>
available commands:

    check-style        Check coding style
    clear-ws           Clear trailing whitespace
    py-4tab-fy         Change tab size for python to 4 spaces
    replace-tab        Replace leading tab to space

author: Santa Zhang <santa1987@gmail.com>"""

if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "help":
        kd_help()
    elif sys.argv[1] == "check-style":
        kd_check_style()
    elif sys.argv[1] == "clear-ws":
        kd_clear_ws()
    elif sys.argv[1] == "py-4tab-fy":
        kd_py4tab()
    elif sys.argv[1] == "replace-tab":
        kd_replace_tab()
    else:
        print "command '%s' not understood, see 'coding.py help' for more info" % sys.argv[1]
