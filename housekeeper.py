#!/usr/bin/env python
# coding=utf-8

# One script to manage my important collections.
#
# Author: Santa Zhang (santa1987@gmail.com)
#

from __future__ import with_statement
from contextlib import closing
import urllib
import sys
import os
import re
import time
import random
import shutil
import traceback
import sqlite3
import csv
from subprocess import Popen, PIPE, STDOUT
from urllib2 import *
from utils import *

def hk_make_dirs(path):
    if os.path.exists(path) == False:
        print "[mkdir] %s" % path
        os.makedirs(path)

def hk_exec(cmd):
    print "[cmd] %s" % cmd
    os.system(cmd)

def hk_read_crc32_dict(crc32_dict_fn):
    crc32_dict = {}
    if os.path.exists(crc32_dict_fn):
        f = open(crc32_dict_fn)
        for line in f.readlines():
            line = line.strip()
            if line.startswith(";") or line.startswith("#") or line == "":
                continue
            idx = line.find(" ")
            if idx < 0:
                continue
            crc32_dict[line[(idx + 1):]] = line[:idx]
        f.close()
    return crc32_dict

# if return None, then no info
# first try to get data from dict
# if not found, then get data from fname
def hk_try_get_crc32_info(fname, crc32_dict):
    if crc32_dict.has_key(fname):
        return crc32_dict[fname]
    splt = re.split("\[|\]|\(|\)|_", fname)
    for sp in splt:
        if len(sp) == 8 and is_hex(sp):
            return sp
    return None

def hk_calc_crc32_from_file(crc32_bin, fpath):
    crc = None
    cmd = "%s \"%s\"" % (crc32_bin, fpath)
    pipe = os.popen(cmd)
    crc = pipe.readlines()[0].split()[0]
    pipe.close()
    if crc == None:
        raise Exception("Failed to calc crc32 for '%s'! Binary is '%s'." % (fpath, crc32_bin))
    return crc

def hk_check_crc32_walker(crc32_bin, folder, files):
    write_log("[dir] %s" % folder)
    crc32_dict_fn = folder + os.path.sep + "housekeeper.crc32"
    crc32_dict = hk_read_crc32_dict(crc32_dict_fn)
    if os.path.exists(crc32_dict_fn):
        write_log("[dict] %s" % crc32_dict_fn)

    for fn in files:
        if fn.startswith("housekeeper."):
            # ignore housekeeper's data
            continue
        fpath = folder + os.path.sep + fn
        if os.path.isdir(fpath):
            continue
        crc32_info = hk_try_get_crc32_info(fn, crc32_dict)
        if crc32_info == None:
            write_log("[ignore] %s" % fpath)
        else:
            calc_crc32 = hk_calc_crc32_from_file(crc32_bin, fpath)
            if calc_crc32 == crc32_info:
                write_log("[pass] %s" % fpath)
            else:
                write_log("[failure] %s" % fpath)


def hk_check_crc32():
    crc32_bin = get_config("crc32_bin")
    if os.path.exists(crc32_bin) == False:
        crc32_bin = os.path.join(os.path.split(__file__)[0], crc32_bin)
    print "using crc32 binary at %s" % crc32_bin
    root_dir = raw_input("The root directory to start with? ")
    os.path.walk(root_dir, hk_check_crc32_walker, crc32_bin)


def hk_check_ascii_fnames_walker(arg, folder, files):
    write_log("[dir] %s" % folder)
    for fn in files:
        fpath = folder + os.path.sep + fn
        if is_ascii(fpath):
            write_log("[pass] %s" % fpath)
        else:
            write_log("[failure] %s" % fpath)


def hk_check_ascii_fnames():
    root_dir = raw_input("The root directory to start with? ")
    os.path.walk(root_dir, hk_check_ascii_fnames_walker, None)

def hk_should_ignore_file(fname, ignore_pattern):
    matched = re.search(ignore_pattern, fname)
    if matched != None:
        return True
    else:
        return False

def hk_should_ignore_crc32(fname, ignore_pattern):
    return hk_should_ignore_file(fname, ignore_pattern)


def hk_write_crc32_walker(args, folder, files):
    crc32_bin, ignore_pattern, new_only = args
    write_log("[dir] %s" % folder)
    crc_f = None
    crc32_dict = {}

    if new_only == True:
        crc32_dict_fn = folder + os.path.sep + "housekeeper.crc32"
        crc32_dict = hk_read_crc32_dict(crc32_dict_fn)
        if os.path.exists(crc32_dict_fn):
            write_log("[dict] %s" % crc32_dict_fn)

    for fn in files:
        if fn.startswith("housekeeper."):
            # ignore housekeeper's data
            continue
        fpath = folder + os.path.sep + fn
        if os.path.isdir(fpath):
            continue
        if hk_should_ignore_crc32(fn, ignore_pattern):
            write_log("[ignore] %s" % fpath)
            continue

        if new_only == True:
            if crc32_dict.has_key(fn):
                write_log("[exists] %s %s" % (crc32_dict[fn], fpath))
                continue

        calc_crc32 = hk_calc_crc32_from_file(crc32_bin, fpath)
        write_log("[crc32] %s %s" % (calc_crc32, fpath))

        if crc_f == None:
            if new_only == True:
                is_new_file = not os.path.exists(folder + os.path.sep + "housekeeper.crc32")
                crc_f = open(folder + os.path.sep + "housekeeper.crc32", "a")
                if is_new_file:
                    crc_f.write("# generated by housekeeper.py, on %s\n" % time.asctime())
                    crc_f.write("#\n\n")
                else:
                    crc_f.write("\n")
                    crc_f.write("# new data updated on %s\n" % time.asctime())
                    crc_f.write("#\n\n")
            else:
                crc_f = open(folder + os.path.sep + "housekeeper.crc32", "w")
                crc_f.write("# generated by housekeeper.py, on %s\n" % time.asctime())
                crc_f.write("#\n\n")

        crc_f.write("%s %s\n" % (calc_crc32, fn))
        crc_f.flush()

    if crc_f != None:
        crc_f.close()

def hk_write_crc32():
    crc32_bin = get_config("crc32_bin")
    if os.path.exists(crc32_bin) == False:
        crc32_bin = os.path.join(os.path.split(__file__)[0], crc32_bin)
    print "using crc32 binary at %s" % crc32_bin
    ignore_pattern = get_config("crc32_ignore_pattern")
    root_dir = raw_input("The root directory to start with? ")
    new_only = False
    os.path.walk(root_dir, hk_write_crc32_walker, (crc32_bin, ignore_pattern, new_only))

def hk_write_crc32_new_only():
    crc32_bin = get_config("crc32_bin")
    if os.path.exists(crc32_bin) == False:
        crc32_bin = os.path.join(os.path.split(__file__)[0], crc32_bin)
    print "using crc32 binary at %s" % crc32_bin
    ignore_pattern = get_config("crc32_ignore_pattern")
    root_dir = raw_input("The root directory to start with? ")
    new_only = True
    os.path.walk(root_dir, hk_write_crc32_walker, (crc32_bin, ignore_pattern, new_only))

def hk_util_append_tmp_ext(fpath):
    while True:
        tmp_fpath = "%s.tmp.%d" % (fpath, random.randint(0, 100000000))
        if os.path.exists(tmp_fpath) == False:
            break
    return tmp_fpath

def hk_jpeg2jpg():
    root_dir = raw_input("The root directory to start with? ")
    for root, folders, files in os.walk(root_dir):
        for fn in files:
            fpath = os.path.join(root, fn)
            splt = os.path.splitext(fpath)
            if splt[1].lower() == ".jpeg":
                # rename to a tmp file and rename back
                new_name = splt[0] + ".jpg"
                print "[rename] %s ==> %s" % (fpath, new_name)
                os.rename(fpath, new_name)

def hk_lowercase_ext():
    root_dir = raw_input("The root directory to start with? ")
    for root, folders, files in os.walk(root_dir):
        for fn in files:
            fpath = os.path.join(root, fn)
            splt = os.path.splitext(fpath)
            if splt[1] != splt[1].lower():
                # rename to a tmp file and rename back
                new_name = splt[0] + splt[1].lower()
                tmp_name = hk_util_append_tmp_ext(fpath)
                print "[rename] %s ==> %s" % (fpath, new_name)
                os.rename(fpath, tmp_name)
                os.rename(tmp_name, new_name)

def hk_rm_all_gems():
    root_required()
    mac_required()
    p = os.popen("gem env gempath")
    gempath = p.read().strip().split(":")
    p.close()
    p = os.popen("gem list --no-version")
    all_gems = p.read().split()
    p.close()
    f = open("reinstall-all-gems.sh", "w")
    f.write("gem install " + (" ").join(all_gems) + "\n")
    f.close()
    for gpath in gempath:
        for gem in all_gems:
            hk_exec("sudo sh -c 'GEM_HOME=%s gem uninstall -aIx %s'" % (gpath, gem))
    print "A file 'reinstall-all-gems.sh' is generate in current woring dir."

def hk_rm_empty_dir():
    root_dir = raw_input("The root directory to start with? ")
    ignore_pattern = get_config("rm_empty_dir_ignore_pattern")
    for root, folders, files in os.walk(root_dir):
        if len(folders) > 0:
            continue
        is_empty = True
        for fn in files:
            if hk_should_ignore_file(fn, ignore_pattern) == False:
                is_empty = False
                break
            else:
                print "[ignore] %s" % os.path.join(root, fn)
        if is_empty:
            print "[empty-dir] %s" % root
            shutil.rmtree(root)

def hk_psp_sync_pic():
    psp_root = get_config("psp_root")
    pic_root = get_config("psp_sync_pic.pic_root")
    pic_folders = get_config("psp_sync_pic.folders").split("|")
    convert_bin = get_config("convert_bin")

    # check if really a psp dir
    if os.path.isdir(psp_root) == False:
        write_log("[error] psp_root is not a valid dir: '%s'" % psp_root)
        exit(1)
    psp_root_listing = []
    for item in os.listdir(psp_root):
        psp_root_listing += item.lower(),
    for psp_item in ["picture", "music", "psp", "video"]:
        if psp_item not in psp_root_listing:
            write_log("[error] not a valid psp root: '%s'" % psp_root)
            exit(1)

    # start syncing
    for folder in pic_folders:
        write_log("[psp-sync-pic] folder: '%s'" % folder)
        from_dir = os.path.join(pic_root, folder)
        to_dir = os.path.join(psp_root, "Picture", folder)
        hk_make_dirs(to_dir)
        from_dir_ls = os.listdir(from_dir)
        to_dir_ls = os.listdir(to_dir)
        for to_f in to_dir_ls:
            to_f_path = os.path.join(to_dir, to_f)
            if not is_image(to_f):
                continue
            if to_f not in from_dir_ls:
                write_log("[del] %s" % to_f_path)
                os.remove(to_f_path)
        for from_f in from_dir_ls:
            if not is_image(from_f):
                continue
            if from_f not in to_dir_ls:
                from_f_path = os.path.join(from_dir, from_f)
                to_f_path = os.path.join(to_dir, from_f)
                write_log("[add] %s" % from_f)
                if os.stat(from_f_path).st_size > 1024 * 1024:
                    hk_exec("%s \"%s\" -resize 1280x800 \"%s\"" % (convert_bin, from_f_path, to_f_path))
                else:
                    hk_exec("cp \"%s\" \"%s\"" % (from_f_path, to_f_path))

def hk_batch_rename():
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

        dry_run = True
        for dummy_i in range(2):
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

            if dry_run == True:
                raw_input("press ENTER to confirm and execute the action...")
                dry_run = False
            else:
                break

    elif choice == "2":
        print "please provide a lambda function f(x, i):"
        print "x: original basename (without ext)"
        print "i: counter (starts from 0)"
        print """eg:\n        "%s_%d" % (x, i)"""
        fun_body = raw_input("lambda function?\n")
        print "dry run result (not actually executed):"

        dry_run = True
        for dummy_i in range(2):
            exec "housekeeper_lambda_rename_helper_function = lambda x, i: (%s)" % fun_body
            counter = 0
            rollback_list = []
            try:
                for file in match_list:
                    old_basename = os.path.basename(file)
                    old_spltname = os.path.splitext(old_basename)
                    new_basename = housekeeper_lambda_rename_helper_function(old_spltname[0], counter) + old_spltname[1]
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

            if dry_run == True:
                raw_input("press ENTER to confirm and execute the action...")
                dry_run = False
            else:
                break

    else:
        print "no such choice: '%s'" % choice

def hk_clean_eject_usb(usb_name):
    mount_folder = "/Volumes/" + usb_name
    if os.path.isdir(mount_folder) == False:
        print "USB drive not found: '%s'" % (mount_folder)
        exit(1)
    print "Possible cruft files:"
    print "---"
    os.system("find \"%s\" -iname \".*\"" % mount_folder)
    os.system("find \"%s\" -iname \".DS_Store\"" % mount_folder)
    print "---"
    print "input 'clean' to remove those cruft files, or just press ENTER to pass along"
    choice = raw_input().strip()
    if choice == "clean":
        hk_exec("find \"%s\" -iname \".*\" -delete" % mount_folder)
        hk_exec("find \"%s\" -iname \".DS_Store\" -delete" % mount_folder)
    for cruft in [".DS_Store", ".fseventsd", ".Spotlight-V100", ".Trashes"]:
        cruft_path = os.path.join(mount_folder, cruft)
        if os.path.exists(cruft_path):
            if os.path.isdir(cruft_path):
                print "[rm-dir] %s" % cruft_path
                try:
                    shutil.rmtree(cruft_path)
                except:
                    traceback.print_exc()
            else:
                print "[rm-file] %s" % cruft_path
                os.remove(cruft_path)

    hk_exec("diskutil eject \"%s\"" % usb_name)


def has_highres_image_set(set_name):
    if set_name in ["moe_imouto", "nekobooru", "konachan", "danbooru"]:
        return True
    else:
        return False

def get_bucket_name(id_in_set):
    BUCKET_SIZE = 100
    bucket_id = id_in_set / BUCKET_SIZE
    bucket_name = "%d-%d" % (bucket_id * BUCKET_SIZE, bucket_id * BUCKET_SIZE + BUCKET_SIZE - 1)
    return bucket_name

def get_highres_image(image_root, set_name, image_id, ext_name):
    if has_highres_image_set(set_name):
        bucket_name = get_bucket_name(int(image_id))
        image_fn = os.path.join(image_root, set_name + "_highres", bucket_name, image_id + "." + ext_name)
        if os.path.exists(image_fn):
            return image_fn
    return None

def split_image_fname(fname):
    image_set = None
    image_id = None
    splt = fname.split()
    image_set = splt[0]
    image_id = splt[1].split(".")[0]
    ext_name = splt[1].split(".")[1]
    return (image_set, image_id, ext_name)

def hk_upgrade_dropbox_pic():
    pic_root = get_config("upgrade_res.pic_root")
    dest_root = get_config("upgrade_res.dest_root")
    pic_folders = get_config("upgrade_res.folders").split("|")
    threshold = int(get_config("upgrade_res.size_threshold_mb")) * 1024 * 1024
    for folder in pic_folders:
        folder_path = os.path.join(dest_root, folder)
        for fn in os.listdir(folder_path):
            fpath = os.path.join(folder_path, fn)
            if os.path.isfile(fpath) == False or is_image(fn) == False:
                continue
            image_set, image_id, ext_name = split_image_fname(fn)
            highres_image = get_highres_image(pic_root, image_set, image_id, ext_name)
            if highres_image == None:
                continue
            else:
                if os.stat(highres_image).st_size > threshold:
                    print "[skip] image too big (%.2fMB): '%s'" % (os.stat(highres_image).st_size / 1024.0 /1024.0, highres_image)
                else:
                    dest_fn = "%s %s.%s" % (image_set + "_highres", image_id, ext_name)
                    write_log("[replace] %s -> %s" % (fn, dest_fn))
                    shutil.copy(highres_image, os.path.join(folder_path, dest_fn))
                    os.remove(fpath)

def util_aucdtect(aucdtect_bin, ffmpeg_bin, tmp_folder, strip_fn, fpath):
    print "[aucdtect] %s" % strip_fn
    audio_type = ""
    probability = ""
    tmp_fn = os.path.join(tmp_folder, "itunes-genunie-check-%s.wav" % random_token())
    try:
        ffmpeg_cmd = "%s -y -i \"%s\" \"%s\"" % (ffmpeg_bin, fpath, tmp_fn)
        # on Windows, close fds is not supported when stdin/stdout/stderr is directed
        pipe = Popen(ffmpeg_cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        stdout_output = pipe.stdout.read()
        #print stdout_output

        aucdtect_cmd = "%s \"%s\"" % (aucdtect_bin, tmp_fn)
        pipe = Popen(aucdtect_cmd, shell=False, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        stdout_output = pipe.stdout.read()
        for line in stdout_output.splitlines():
            line = line.strip()
            if line.startswith("This track looks like"):
                splt = line.split()
                audio_type = splt[4]
                probability = splt[7]
                print "[result] %s %s" % (audio_type, probability)
                break
    finally:
        if os.path.exists(tmp_fn):
            os.remove(tmp_fn)
    return audio_type, probability

def hk_itunes_backup():
    hk_exec("cp -v /Users/santa/Music/iTunes/iTunes* /Users/santa/Dropbox/Backups/mac_backup/iTunes")

def hk_itunes_genuine_check():
    aucdtect_bin = get_config("aucdtect_bin")
    ffmpeg_bin = get_config("ffmpeg_bin")
    itunes_folder = get_config("itunes_folder")
    tmp_folder = get_config("tmp_folder")
    report_fn = os.path.abspath(os.path.join(itunes_folder, "..", "itunes_genuine_report.csv"))
    print "[report-file] %s" % report_fn
    old_db = {}
    new_db = {}
    if os.path.exists(report_fn):
        old_db_f = open(report_fn, "rb")
        old_db_reader = csv.reader(old_db_f)
        for row in old_db_reader:
            old_db[row[0]] = [row[1], row[2], row[3]]
        old_db_f.close()
    itunes_music_folder = os.path.join(itunes_folder, "Music")
    new_db_f = open(report_fn + ".tmp", "wb")
    new_db_writer = csv.writer(new_db_f)
    # the genunie info: (relative_fpath, filename, type, probability)
    new_db_writer.writerow(["path", "filename", "type", "probability"])
    for root, dirname, fnames in os.walk(itunes_music_folder):
        strip_root = root[(len(itunes_music_folder) + 1):]
        for fn in fnames:
            if is_music(fn):
                fpath = os.path.join(root, fn)
                strip_fn = os.path.join(strip_root, fn)
                if old_db.has_key(strip_fn) == False:
                    print "[new] %s" % strip_fn
                    new_db[strip_fn] = [fn, "", ""]
                else:
                    print "[skip] %s" % strip_fn
                    new_db[strip_fn] = old_db[strip_fn]
                if new_db[strip_fn][1] == "" or new_db[strip_fn][2] == "":
                    new_db[strip_fn][1], new_db[strip_fn][2] = util_aucdtect(aucdtect_bin, ffmpeg_bin, tmp_folder, strip_fn, fpath)
                new_db_writer.writerow([strip_fn, new_db[strip_fn][0], new_db[strip_fn][1], new_db[strip_fn][2]])
                new_db_f.flush()
    new_db_f.close()
    shutil.move(report_fn + ".tmp", report_fn)

def hk_itunes_play_count():
    itunes_lib_xml_fn = os.path.join(get_config("itunes_folder"), "iTunes Music Library.xml")
    total_count = 0
    fp = open(itunes_lib_xml_fn)
    fcontent = fp.read()
    fp.close()
    match = re.findall("Play Count<\/key><integer>[^<]*", fcontent)
    for m in match:
        total_count += int(m[25:])
    print "Total play count is %d" % total_count

def hk_itunes_check_exists():
    itunes_folder = get_config("itunes_folder")
    itunes_lib_xml_fn = os.path.join(itunes_folder, "iTunes Music Library.xml")
    fp = open(itunes_lib_xml_fn)
    fcontent = fp.read()
    fp.close()
    match = re.findall("file\:\/\/[^<]+", fcontent)
    missing_count = 0
    fpath_dict = {}
    for root, dirname, fnames in os.walk(os.path.join(itunes_folder, "Music")):
        for fn in fnames:
            fpath = os.path.join(root, fn)
            fpath = convert_jpn_path(fpath)
            fpath_dict[fpath] = True

    for m in match:
        #music_fn = m.replace("\u30fb", ".")
        music_fn = urllib.unquote(m)[16:]
        music_fn = music_fn.replace("&#38;", "&")
        if os.path.exists(music_fn) == False:
            print music_fn
            missing_count += 1
    if missing_count == 0:
        print "Nothing is missing"
    else:
        print "%d items missing" % missing_count

def convert_jpn_path(fpath):
    # eg: ??
    # E3 81 B5 E3 82 99 -> E3 81 B6
    # E3 81 AF B3 82 9A -> E3 82 BD
    fpath = fpath.replace("ダ", "ダ")
    fpath = fpath.replace("ポ", "ポ")
    fpath = fpath.replace("グ", "グ")
    fpath = fpath.replace("ド", "ド")
    fpath = fpath.replace("ジ", "ジ")
    fpath = fpath.replace("だ", "だ")
    fpath = fpath.replace("ば", "ば")
    fpath = fpath.replace("が", "が")
    fpath = fpath.replace("で", "で")
    fpath = fpath.replace("パ", "パ")
    fpath = fpath.replace("プ", "プ")
    fpath = fpath.replace("デ", "デ")
    fpath = fpath.replace("び", "び")
    fpath = fpath.replace("ず", "ず")
    fpath = fpath.replace("ベ", "ベ")
    fpath = fpath.replace("ゼ", "ゼ")
    fpath = fpath.replace("グ", "グ")
    fpath = fpath.replace("ピ", "ピ")
    fpath = fpath.replace("じ", "じ")
    fpath = fpath.replace("ゲ", "ゲ")
    fpath = fpath.replace("ブ", "ブ")
    fpath = fpath.replace("ご", "ご")
    fpath = fpath.replace("ビ", "ビ")
    fpath = fpath.replace("ズ", "ズ")
    fpath = fpath.replace("ボ", "ボ")
    fpath = fpath.replace("ぼ", "ぼ")
    fpath = fpath.replace("ガ", "ガ")
    fpath = fpath.replace("ど", "ど")
    fpath = fpath.replace("ぶ", "ぶ")
    fpath = fpath.replace("バ", "バ")
    fpath = fpath.replace("ぞ", "ぞ")
    fpath = fpath.replace("ヴ", "ヴ")
    fpath = fpath.replace("ぱ", "ぽ")
    fpath = fpath.replace("ゴ", "ゴ")
    fpath = fpath.replace("ぎ", "ぎ")
    fpath = fpath.replace("ペ", "ぺ")
    fpath = fpath.replace("ざ", "ざ")
    fpath = fpath.replace("ぴ", "ぴ")
    fpath = fpath.replace("ゾ", "ゾ")
    return fpath

def dbg_print(msg):
    if "゙" in msg or "゚" in msg or "ハチミツとクローバー" in msg:
        print msg

def hk_itunes_find_ophan():
    library_map = {}
    itunes_folder = get_config("itunes_folder")
    itunes_lib_xml_fn = os.path.join(itunes_folder, "iTunes Music Library.xml")
    fp = open(itunes_lib_xml_fn)
    fcontent = fp.read()
    fp.close()
    match = re.findall("file\:\/\/[^<]+", fcontent)
    ophan_count = 0
    for m in match:
        #music_fn = m.replace("\u30fb", ".")
        music_fn = urllib.unquote(m)[16:]
        music_fn = music_fn.replace("&#38;", "&")
        music_fn = convert_jpn_path(music_fn)
        library_map[music_fn] = True
        dbg_print(music_fn)
    for root, dirname, fnames in os.walk(os.path.join(itunes_folder, "Music")):
        for fn in fnames:
            fpath = os.path.join(root, fn)
            fpath = convert_jpn_path(fpath)
            #dbg_print(fpath)
            if is_music(fpath):
                if library_map.has_key(fpath) == False:
                    ophan_count += 1
                    dbg_print(fpath)
    if ophan_count == 0:
        print "No ophan found"
    else:
        print "Found %d ophan files" % ophan_count
    print "NOTE: THIS UTILITY IS STILL IN DEVEOPMENT, THE RESULTS MIGHT NOT BE CORRECT!"

def hk_itunes_export_cover():
    output_dir = raw_input("Output dir? ")
    hk_make_dirs(output_dir)
    itc2png_bin = get_config("itc2png_bin")
    itunes_folder = get_config("itunes_folder")
    for root, dirname, fnames in os.walk(os.path.join(itunes_folder, "Album Artwork")):
        for fn in fnames:
            if fn.endswith(".itc2"):
                fpath = os.path.join(root, fn)
                print "[itc2] %s" % fpath
                shutil.copy(fpath, output_dir)
                os.system("%s %s" % (itc2png_bin, os.path.join(output_dir, fn)))
    return output_dir

def hk_itunes_bad_cover():
    bad_uuid = set()
    output_dir = hk_itunes_export_cover()
    for fn in os.listdir(output_dir):
        if fn.startswith("."):
            continue
        if fn.lower().endswith(".itc2"):
            fpath = os.path.join(output_dir, fn)
            os.remove(fpath)
        if fn.lower().endswith(".png"):
            fpath = os.path.join(output_dir, fn)
            pipe = os.popen("file \"%s\"" % fpath)
            output = pipe.read()
            splt = output.split()
            #print splt
            pic_uuid = os.path.split(splt[0][:-1])[1][17:33]
            pic_w = int(splt[4])
            pic_h = int(splt[6][:-1])
            ratio = 1 - pic_w * 1.0 / pic_h
            if ratio < 0.0:
                ratio = -ratio
            ratio_threshold = 0.1 # the ratio we can bare
            if ratio > ratio_threshold and pic_uuid not in bad_uuid:
                print pic_uuid, pic_w, pic_h, ratio
                bad_uuid.add(pic_uuid)
            else:
                fpath = os.path.join(output_dir, fn)
                os.remove(fpath)
            pipe.close()


def hk_itunes_rm_useless_cover():
    library_map = {}
    itunes_folder = get_config("itunes_folder")
    itunes_lib_xml_fn = os.path.join(itunes_folder, "iTunes Music Library.xml")
    fp = open(itunes_lib_xml_fn)
    fcontent = fp.read()
    fp.close()
    match = re.findall("Persistent ID<\/key><string>[^<]*", fcontent)
    uuid_lib = {}
    for m in match:
        uuid = m.split(">")[-1]
        uuid_lib[uuid] = True
    for root, dirname, fnames in os.walk(os.path.join(itunes_folder, "Album Artwork")):
        for fn in fnames:
            if fn.endswith(".itc2"):
                uuid = fn[17:33]
                if uuid_lib.has_key(uuid) == False:
                    fpath = os.path.join(root, fn)
                    os.remove(fpath)
                    print "[rm] %s" % fpath
    print "Done!"

def hk_itunes_stats():
    itunes_lib_xml_fn = os.path.join(get_config("itunes_folder"), "iTunes Music Library.xml")
    total_count = 0
    total_tracks = 0
    fp = open(itunes_lib_xml_fn)
    fcontent = fp.read()
    fp.close()
    idx = idx2 = idx3 = idx4 = 0
    album_name_to_play_count = {}
    while True:
        idx = fcontent.find("<key>Name</key><string>", idx)
        if idx < 0:
            break
        else:
            total_tracks += 1
        idx2 = fcontent.find("</string>", idx)
        title = fcontent[(idx + 23) : idx2]
        idx += 1

        idx3 = fcontent.find("<key>Album</key><string>", idx)
        if fcontent[idx2:idx3].find("<dict>") >= 0:
            continue
        if idx3 < 0:
            continue
        idx4 = fcontent.find("</string>", idx3)
        album_name = fcontent[(idx3 + 24) : idx4]
        idx = idx3 + 1

        idx3 = fcontent.find("<key>Play Count</key><integer>", idx)
        if fcontent[idx2:idx3].find("<dict>") >= 0:
            play_count = 0
        else:
            idx4 = fcontent.find("</integer>", idx3)
            play_count_str = fcontent[(idx3 + 30) : idx4]
            play_count = int(play_count_str)
            idx = idx3 + 1

        #print "%s, %s, played %d times" % (album_name, title, play_count)
        if album_name_to_play_count.has_key(album_name):
            album_name_to_play_count[album_name] += play_count,
        else:
            album_name_to_play_count[album_name] = [play_count]
        #print album_name_to_play_count[album_name]

    print "Total tracks: %d" % total_tracks

    avg_album_playcount = []
    for k in album_name_to_play_count.keys():
        v = album_name_to_play_count[k]
        album_play_count = sum(v)
        avg = sum(v) * 1.0 / len(v)
        #print avg, k
        avg_album_playcount += (avg, k),
    avg_album_playcount.sort()

    n_least = 100;
    print "%d most less played albums:" % n_least
    counter = 0
    for avg, album in avg_album_playcount:
        print avg, album
        counter += 1
        if counter > n_least:
            break



def get_du_of_folder(folder):
    du = 0
    for root, dirnames, fnames in os.walk(folder):
        for fn in fnames:
            fpath = os.path.join(root, fn)
            if os.path.isfile(fpath):
                du += os.stat(fpath).st_size
    return du

def hk_backup_psp():
    tmp_folder = get_config("tmp_folder")
    psp_root = get_config("psp_root")
    bkup_folder = os.path.join(get_config("dropbox_folder"), "Backups")
    bkup_job_name = "psp_backup.%s" % (time.strftime("%y%m%d-%H%M%S", time.localtime()))
    tmp_cp_folder = os.path.join(tmp_folder, bkup_job_name)
    hk_make_dirs(tmp_cp_folder)
    tmp_savedata_dir = os.path.join(tmp_cp_folder, "PSP", "SAVEDATA")
    hk_make_dirs(tmp_savedata_dir)
    psp_save_root = os.path.join(psp_root, "PSP", "SAVEDATA")
    bkup_threshold = int(get_config("psp_savedata_backup_threshold_mb")) * 1024 * 1024
    for fn in os.listdir(psp_save_root):
        fpath = os.path.join(psp_save_root, fn)
        if os.path.isdir(fpath) == False:
            continue
        folder_du = get_du_of_folder(fpath)
        if folder_du <= bkup_threshold:
            print "[backup] %d bytes, '%s'" % (folder_du, fpath)
            shutil.copytree(fpath, os.path.join(tmp_savedata_dir, fn))
        else:
            print "[skip] too big: %d bytes, '%s'" % (folder_du, fpath)
    for fn in os.listdir(psp_root):
        fpath = os.path.join(psp_root, fn)
        if os.path.isdir(fpath) == False:
            if fpath.lower().endswith(".bin") or fpath.lower().endswith(".txt") or fpath.lower().endswith(".ind") or fpath.lower().endswith(".prx"):
                f_size = os.stat(fpath).st_size
                if f_size <= bkup_threshold:
                    print "[backup] %d bytes, '%s'" % (f_size, fpath)
                    shutil.copy(fpath, os.path.join(tmp_cp_folder, fn))
                else:
                    print "[skip] too big: %d bytes, '%s'" % (f_size, fpath)
        else:
            if fn.lower() == "registry" or fn.lower() == "seplugins" or fn.lower() == "freecheat":
                folder_du = get_du_of_folder(fpath)
                if folder_du <= bkup_threshold:
                    print "[backup] %d bytes, '%s'" % (folder_du, fpath)
                    shutil.copytree(fpath, os.path.join(tmp_cp_folder, fn))
                else:
                    print "[skip] too big: %d bytes, '%s'" % (folder_du, fpath)
    print "zipping...."
    zipdir(tmp_cp_folder, tmp_cp_folder + ".zip")
    print "[rmdir] %s" % tmp_cp_folder
    shutil.rmtree(tmp_cp_folder)
    shutil.move(tmp_cp_folder + ".zip", bkup_folder)
    print "done!"

def hk_backup_addr_book():
    mac_required()
    print "Doing AddressBook backup..."
    addr_src_dir = "/Users/santa/Library/Application Support/AddressBook"
    addr_dest_file = "/Users/santa/Dropbox/Backups/mac_backup/AddressBook.zip"
    if os.path.exists(addr_dest_file):
        os.remove(addr_dest_file)
    zipdir(addr_src_dir, addr_dest_file)
    print "AddressBook backup done!"

def hk_backup_conf():
    conf_backup_folder = get_config("config_backup_folder")
    config_files = []
    for conf in get_config("config_files").split(";"):
        if conf != "":
            config_files += conf,
    # do backup work
    hk_make_dirs(conf_backup_folder)
    for conf in config_files:
        if os.path.isfile(conf):
            folder, fname = os.path.split(conf)
            dest_folder = os.path.join(conf_backup_folder, folder[1:]) # folder[1:] -> strip the leading '/'
            dest_file = os.path.join(dest_folder, fname)
            hk_make_dirs(dest_folder)
            print "[file] %s -> %s" % (conf, dest_file)
            shutil.copy(conf, dest_file)
        elif os.path.isdir(conf):
            parent_folder, main_name = os.path.split(conf)
            dest_folder = os.path.join(conf_backup_folder, parent_folder[1:])
            hk_make_dirs(dest_folder)
            dest_entry = os.path.join(dest_folder, main_name)
            if os.path.exists(dest_entry):
                print "[replace] %s" % dest_entry
                shutil.rmtree(dest_entry)
            print "[dir] %s -> %s" % (conf, dest_entry)
            shutil.copytree(conf, dest_entry)

def util_update_chrome_progress(len, percent, timeused, bytesread):
    try:
        bar = "\b["
        for i in range(len):
            if (i < percent * len):
                bar += '='
            else:
                bar += ' '
        bar += '] %d%% %db/s ' % (int(percent * 100), int(bytesread / timeused))
        bar += str(int(timeused / percent * (1 - percent))) + "s # "
        bar += str(int(timeused)) + "s   "
        print bar + '\b' * (len + 100),
    except:
        pass  # might have division error

def hk_update_chrome():
    if os.name != "nt":
        print "Sorry, this function only works in Windows!"
        exit(0)
    dlfolder = get_config("tmp_folder")
    chromefolder = "C:\\Users\\Santa\\AppData\\Local\\Chromium\\Application"
    last_revision = 0
    # get last revision from log file
    try:
        f = open(chromefolder + os.path.sep + "updatechrome_revision.txt", "r")
        last_revision = int(f.readline())
        f.close()
    except: # file not found
        print "*** updatechrome_revision.txt not found!"

    while True:
        try:

            downloaded = False

            # delete temp download files
            for fname in os.listdir(dlfolder):
                try:
                    if fname.startswith("chrome.") and fname.endswith(".zip"):
                        fname_split = fname.split(".")
                        if len(fname_split) != 3:
                            continue
                        elif fname_split[1].isdigit():
                            os.remove(dlfolder + os.path.sep + fname)
                            print "Deleted temp download file: " + fname
                except:
                    print "*** Error deleting tmp download files"


            while downloaded == False:

                u = urlopen("http://build.chromium.org/buildbot/snapshots/chromium-rel-xp/LATEST")
                rev = int(u.readline())
                print "Revision is %d" % rev

                if (rev != last_revision):

                    u = urlopen("http://build.chromium.org/buildbot/snapshots/chromium-rel-xp/%d/chrome-win32.zip" % rev)
                    dlsize = int(u.headers["Content-Length"])
                    dlpath = os.path.join(dlfolder, "chrome.%d.zip" % rev)
                    print "Downloading %d bytes" % dlsize
                    dlfile = open(dlpath, "wb")
                    dlcnt = 0
                    start = time.time()
                    last_time = start
                    last_count = 0

                    while (dlcnt < dlsize):
                        binary = u.read(8192)
                        dlfile.write(binary)
                        dlcnt += len(binary)
                        timeused = time.time() - start
                        if last_count == 100:
                            timespan = time.time() - last_time
                            if timespan < 1:  # download failure
                                break
                            last_count = 0
                            last_time = time.time()
                        last_count += 1
                        util_update_chrome_progress(40, 1.0 * dlcnt / dlsize, timeused, dlcnt)

                    dlfile.close()

                    if dlcnt == dlsize:
                        downloaded = True
                        if os.path.exists(chromefolder + os.path.sep + "chrome.exe"):
                            os.remove(chromefolder + os.path.sep + "chrome.exe")
                        # will raise exception when chrome is running, thus the log file will not be written

                        os.system("unzip -o %s -d %s" % (dlpath, dlfolder))
                        os.system("cp %s %s -rf" % (dlfolder + "//chrome-win32//*", chromefolder))
                        shutil.rmtree(os.path.join(dlfolder, "chrome-win32"))
                        os.remove(dlpath)
                        last_revision = rev

                        try:
                            f = open(chromefolder + os.path.sep + "updatechrome_revision.txt", "w")
                            f.write(str(last_revision) + "\n")
                            f.close()
                        except: # file not opened
                            print "*** Failed to write updatechrome_revision.txt"
                            (exc_type, exc_val, exc_tb) = sys.exc_info()
                            print exc_type
                            print exc_val
                            traceback.print_tb(exc_tb)

                    else:
                        print ""
                        print "Oops, download failed. Retry..."

                else:
                    downloaded = True
                    print "Up to date"

        except:
            print "*** Exception during downloading"
            (exc_type, exc_val, exc_tb) = sys.exc_info()
            print exc_type
            print exc_val
            traceback.print_tb(exc_tb)

        finally:
            print "Wait 10 minutes for next update"
            time.sleep(600)

def hk_papers_find_ophan():
    papers_folder = get_config("papers_folder")
    lib_fn = os.path.join(papers_folder, "Library.papers")
    db_conn = sqlite3.connect(lib_fn, 10)
    c = db_conn.cursor()
    c.execute("select ZPATH from ZPAPER")
    ret = c.fetchall()
    print "%d papers in library" % len(ret)
    lib_dict = {}
    for e in ret:
        pdfpath = os.path.join(papers_folder, e[0].encode("utf-8"))
        if os.path.exists(pdfpath) == False:
            print "[not-exists] %s" % pdfpath
        else:
            lib_dict[pdfpath] = True
    for root, dirnames, fnames in os.walk(papers_folder):
        for fn in fnames:
            fpath = os.path.join(root, fn)
            if fpath.lower().endswith(".pdf"):
                if lib_dict.has_key(fpath) == False:
                    print "[ophan] %s" % fpath


def hk_zip_sub_dir():
    root_dir = raw_input("root dir? ")
    for fn in os.listdir(root_dir):
        fpath = os.path.join(root_dir, fn)
        if os.path.isdir(fpath):
            zip_fn = fpath + ".zip"
            if os.path.exists(zip_fn):
                print "[skip] zip exists: '%s'" % zip_fn
                continue
            print "[zip-dir] %s" % fpath
            zipdir(fpath, fpath + ".zip")


def parse_ics_uid_map(ics_content):
    uidmap = {}
    splt = re.split("\n|\r", ics_content)
    for i in range(len(splt)):
        line = splt[i]
        if line.startswith("UID:"):
            uid = line[4:]
            if uid[0] == '{':
                uid = uid[1:-1]
            uid = uid.lower()
            if is_well_formed_uuid(uid):
                begin_line_no = -1
                end_line_no = -1

                # search backwards (for BEGIN:), note that there might be several levels of BEGIN-END
                level = 0
                j = i
                while j >= 0:
                    ln = splt[j]
                    if ln.startswith("BEGIN:"):
                        if level > 0:
                            level -= 1
                        else:
                            begin_line_no = j
                            break
                    if ln.startswith("END:"):
                        level += 1
                    j -= 1

                # search forwards (for END:), note that there might be several levels of BEGIN-END
                level = 0
                j = i
                while j < len(splt):
                    ln = splt[j]
                    if ln.startswith("END:"):
                        if level > 0:
                            level -= 1
                        else:
                            end_line_no = j
                            break
                    if ln.startswith("BEGIN:"):
                        level += 1
                    j += 1

                if begin_line_no != -1 and end_line_no != -1:
                    content = "\n".join(splt[begin_line_no:end_line_no + 1])
                    uidmap[uid] = content

    return uidmap

def hk_sync_rainlendar():
    ical_folder = get_config("ical_folder")
    rain_ics = get_config("rainlendar2_ics_file")
    backup_ics = rain_ics + ".bak"
    print "backup rainlender2 ics file"
    shutil.copyfile(rain_ics, backup_ics)
    f = open(rain_ics)
    rain_content = f.read()
    rain_ics_map = parse_ics_uid_map(rain_content)
    f.close()

    for root, dirnames, fnames in os.walk(ical_folder):
        for fn in fnames:
            if fn.lower().endswith(".ics"):
                fpath = os.path.join(root, fn)
                f = open(fpath)
                f_content = f.read()
                ical_ics_map = parse_ics_uid_map(f_content)
                f.close()
                for k in ical_ics_map.keys():
                    if rain_ics_map.has_key(k) == False:
                        print "New item with UID: %s" % k
                        rain_ics_map[k] = ical_ics_map[k]


    # rewrite new rain_content
    new_content = ""
    splt = re.split("\n|\r", rain_content)
    idx = 0
    while idx < len(splt):
        line = splt[idx]
        new_content += line + "\n"
        idx += 1
        if line.startswith("BEGIN:"):
            # skip the first BEGIN:CAL
            break
    merged_written = False
    level = 0
    while idx < len(splt):
        line = splt[idx]
        if line.startswith("BEGIN:"):
            level += 1
            if merged_written == False:
                for k in rain_ics_map.keys():
                    new_content += rain_ics_map[k] + "\n"
                merged_written = True
        if level == 0:
            new_content += line + "\n"
        if line.startswith("END:"):
            level -= 1
        idx += 1
    new_content2 = new_content
    new_content = ""
    splt = re.split("\n|\r", new_content2)
    for sp in splt:
        if len(sp) != 0:
            new_content += sp + "\n"
#  print new_content
    f = open(rain_ics, "w")
    f.write(new_content)
    f.close()

def hk_gem_cleanup():
    try:
        root_required()
        mac_required()
        # the macos hack to clean up gems
        p = os.popen("gem env gempath")
        gempath = p.read().strip().split(":")
        p.close()
        for gpath in gempath:
            hk_exec("sudo sh -c 'GEM_HOME=%s gem cleanup'" % gpath)
    except:
        traceback.print_exc()

def hk_sys_maint():
    root_required()
    mac_required()
    print "-" * 80
    print "This script will do system maintenance:"
    print
    print "  1: gem update --no-rdoc --no-ri"
    print "  2: port selfupdate && port list outdated && port upgrade outdated"
    print "  3: tlmgr update --list && tlmgr update --all"
    print
    print "However, the following should be done by you, manually:"
    print
    print "  * backup your code, git push to Github, Dropbox"
    print "  * backup psp"
    print "  * backup nds"
    print "  * backup Mac files by Time Machine"
    print "  * backup your hard disk by SyncToy"
    print "  * backup your music"
    print
    print "Press ENTER to continue, or press CTRL+C to quit."
    raw_input()
    try:
        print
        print "-" * 80
        print "phase 1: gem update --no-rdoc --no-ri"
        hk_exec("gem update --no-rdoc --no-ri")
    except:
        traceback.print_exc()
    try:
        print
        print "-" * 80
        print "phase 2: port selfupdate && port list outdated && port upgrade outdated && port uninstall inactive"
        hk_exec("port selfupdate && port list outdated && port upgrade outdated && port uninstall inactive")
    except:
        traceback.print_exc()
    try:
        print
        print "-" * 80
        print "phase 3: tlmgr update --list && tlmgr update --all"
        hk_exec("tlmgr update --list && tlmgr update --all")
    except:
        traceback.print_exc()

def hk_backup_evernote():
    print "Running backup for Evernote..."
    os.chdir("/Users/santa/Library/Application Support/Evernote/data")
    os.system("git ls-files -d -z | xargs -0 git rm")
    os.system('git add . ; git commit -am "backup on %s"' % time.asctime())
    os.system("git gc --aggressive --prune; git push --all")
    os.chdir("/Users/santa/Dropbox/Backups/mac_backup/evernote_git")
    os.system("git gc --aggressive --prune")
    print "done backup for Evernote"

def hk_sys_backup():
    mac_required()
    hk_backup_conf()  # backup config files
    hk_itunes_backup() # backup itunes files
    os.system("rm -rf /Users/santa/Dropbox/Backups/mac_backup/Evernote.zip")
    os.system("rm -rf /Users/santa/Dropbox/Backups/mac_backup/Papers")
    os.system("rm -rf /Users/santa/Dropbox/Backups/mac_backup/Papers2")
    os.system("rm -rf /Users/santa/Dropbox/Backups/mac_backup/Savings")
    os.system("rm -rf \"/Users/santa/Dropbox/Backups/mac_backup/The Hit List Library.thllibrary\"")

    print "* backup Papers2..."
    os.system("cp -rv /Users/santa/Papers2 /Users/santa/Dropbox/Backups/mac_backup")

    print "* backup The Hit List..."
    os.system("cp -rv \"/Users/santa/Library/Application Support/The Hit List/The Hit List Library.thllibrary\" /Users/santa/Dropbox/Backups/mac_backup")

    if os.path.exists("/Users/santa/Library/Application Support/Cultured Code/Things/Database.xml"):
        print "* backup Things..."
        hk_make_dirs("/Users/santa/Dropbox/Backups/mac_backup/Things")
        os.system("cp -v \"/Users/santa/Library/Application Support/Cultured Code/Things/Database.xml\" /Users/santa/Dropbox/Backups/mac_backup/Things")

    print "* backup iTunes library..."
    hk_make_dirs("/Users/santa/Dropbox/Backups/mac_backup/iTunes")
    os.system("cp -v /Users/santa/Music/iTunes/iTunes* /Users/santa/Dropbox/Backups/mac_backup/iTunes")

    print "* backup Savings library..."
    hk_make_dirs("/Users/santa/Dropbox/Backups/mac_backup/Savings")
    os.system("cp -rv \"/Users/santa/Library/Application Support/Savings\" /Users/santa/Dropbox/Backups/mac_backup")

    hk_backup_evernote()
    hk_backup_addr_book();

    print "everything done!"

def hk_timemachine_image():
    volname = get_config("timemachine.imgvolname")
    imgpath = get_config("timemachine.imgpath")
    imgsize = get_config("timemachine.imgsize")
    uuid = get_config("timemachine.uuid")
    hk_exec("hdiutil create -size %s -fs HFS+J -volname '%s' -type SPARSEBUNDLE %s" % (imgsize, volname, imgpath))
    f = open("%s/com.apple.TimeMachine.MachineID.plist" % imgpath, "w")
    f.write("""<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
            <key>com.apple.backupd.HostUUID</key>
            <string>%s</string>
    </dict>
    </plist>""" % uuid)
    f.close()

def hk_rsync_to_labpc():
    if os.path.exists("/Volumes/Takaramono$"):
        print "Backing up to /Volumes/Takaramono$"
        hk_exec("rsync -avx --delete /Users/santa/Archive/ /Volumes/Takaramono$/backup/archive/")
        hk_exec("cp /Volumes/Takaramono$/backup/music/itunes_genuine_report.csv /Users/santa/Music")
        hk_exec("rsync -avx --delete /Users/santa/Music/ /Volumes/Takaramono$/backup/music/")
        hk_exec("rsync -avx --delete /Users/santa/Movies/ /Volumes/Takaramono$/backup/video/")
        hk_exec("rsync -avx --delete /Users/santa/Manga/ /Volumes/Takaramono$/manga/")
    else:
        print "Backup folder /Volumes/Takaramono$ not mounted!"

def hk_size_ftp_ls_lr():
    fpath = raw_input("Please provide the path of ls-lR file: ")
    f = open(fpath)
    total_sz = 0
    for l in f.readlines():
        sp = l.split()
        if len(sp) > 5 and len(sp[0]) == len("drwxrwxrwx"):
            try:
                sz = int(sp[4])
                total_sz += sz
            except:
                print "Error parsing: %s" % l.strip()
                traceback.print_exc()
    f.close()
    print "%d bytes, or %s" % (total_sz, pretty_fsize(total_sz))



def hk_zip():
    arc_name = sys.argv[2]
    src_list = list(set(sys.argv[3:]))  # remove duplicates
    print "target archive name: %s" % arc_name
    print "items to be archived:", src_list
    if os.path.exists(arc_name):
        print "archive %s already exists!" % arc_name
        exit(1)
    with closing(ZipFile(arc_name, "w", ZIP_DEFLATED)) as zip_file:
        for item in src_list:
            if os.path.isdir(item):
                zip_add_dir(zip_file, item)
            elif os.path.isfile(item):
                zip_add_file(zip_file, item)
            else:
                raise Exception("Cannot handle: %s" % item)


def hk_help():
    print """housekeeper.py: helper script to manage my important collections
usage: housekeeper.py <command>
available commands:

    backup-addr-book                   backup my Address Book
    backup-conf                        backup my config files
    backup-evernote                    bakcup evernote documents
    backup-psp                         backup my psp
    batch-rename                       batch rename files under a folder
    check-ascii-fnames                 make sure all file has ascii-only name
    check-crc32                        check file integrity by crc32
    clean-eject-usb <name>             cleanly eject usb drives (cleans .Trash, .SpotLight folders)
    gem-cleanup                        cleanup gem files
    help                               display this info
    itunes-backup                      backup iTunes library
    itunes-bad-cover                   list cd covers with bad ratio
    itunes-check-exists (deprecated)   check if music in iTunes library really exists
    itunes-export-cover                export covers from iTunes library
    itunes-find-ophan (deprecated)     check if music is in music folder but not in iTunes
    itunes-genuine-check               check if music in iTunes is genuine
    itunes-play-count                  display the play count of iTunes library
    itunes-rm-useless-cover            remove useless covers from iTunes library
    itunes-stats                       display iTunes library info
    jpeg2jpg                           convert .jpeg ext name to .jpg
    lowercase-ext                      make sure file extensions are lower case
    psp-sync-pic                       sync images to psp
    papers-find-ophan                  check if pdf is in papers folder but not in Papers library
    rm-all-gems                        remove all rubygems (currently Mac only)
    rm-empty-dir                       remove empty dir
    rsync-to-labpc                     use rsync to backup my craps onto LabPC
    size-ftp-ls-lr                     get the total size of an FTP site by its ls-lR file
    sync-rainlendar (deprecated)       sync iCal & rainlendar
    sys-backup                         system backup (currently Mac only)
    sys-maint                          system maintenance (currently Mac only)
    timemachine-image                  create new Time Machine image
    update-chrome                      update chrome browser (Windows only)
    upgrade-dropbox-pic                update dropbox photos folder, prefer highres pictures
    write-crc32                        write crc32 data in every directory, overwrite old crc32 files
    write-crc32-new-only               write crc32 data in every directroy, new files only
    zip <arc_name> <names>...          cleanly create a zip archive
    zip-sub-dir                        pack each sub directory into zip files

author: Santa Zhang (santa1987@gmail.com)"""

if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "help":
        hk_help()
    elif sys.argv[1] == "backup-addr-book":
        hk_backup_addr_book()
    elif sys.argv[1] == "backup-conf":
        hk_backup_conf()
    elif sys.argv[1] == "backup-evernote":
        hk_backup_evernote()
    elif sys.argv[1] == "backup-psp":
        hk_backup_psp()
    elif sys.argv[1] == "batch-rename":
        hk_batch_rename()
    elif sys.argv[1] == "check-crc32":
        hk_check_crc32()
    elif sys.argv[1] == "check-ascii-fnames":
        hk_check_ascii_fnames()
    elif sys.argv[1] == "clean-eject-usb":
        if len(sys.argv) < 3:
            print "usage: housekeeper.py clean-eject-usb <usb_name>"
            exit(0)
        hk_clean_eject_usb(sys.argv[2])
    elif sys.argv[1] == "gem-cleanup":
        hk_gem_cleanup()
    elif sys.argv[1] == "itunes-backup":
        hk_itunes_backup()
    elif sys.argv[1] == "itunes-bad-cover":
        hk_itunes_bad_cover()
    elif sys.argv[1] == "itunes-check-exists":
        hk_itunes_check_exists()
    elif sys.argv[1] == "itunes-export-cover":
        hk_itunes_export_cover()
    elif sys.argv[1] == "itunes-find-ophan":
        hk_itunes_find_ophan()
    elif sys.argv[1] == "itunes-genuine-check":
        hk_itunes_genuine_check()
    elif sys.argv[1] == "itunes-play-count":
        hk_itunes_play_count()
    elif sys.argv[1] == "itunes-rm-useless-cover":
        hk_itunes_rm_useless_cover()
    elif sys.argv[1] == "itunes-stats":
        hk_itunes_stats();
    elif sys.argv[1] == "jpeg2jpg":
        hk_jpeg2jpg()
    elif sys.argv[1] == "lowercase-ext":
        hk_lowercase_ext()
    elif sys.argv[1] == "psp-sync-pic":
        hk_psp_sync_pic()
    elif sys.argv[1] == "papers-find-ophan":
        hk_papers_find_ophan()
    elif sys.argv[1] == "rm-all-gems":
        hk_rm_all_gems()
    elif sys.argv[1] == "rm-empty-dir":
        hk_rm_empty_dir()
    elif sys.argv[1] == "rsync-to-labpc":
        hk_rsync_to_labpc()
    elif sys.argv[1] == "size-ftp-ls-lr":
        hk_size_ftp_ls_lr()
    elif sys.argv[1] == "sync-rainlendar":
        hk_sync_rainlendar()
    elif sys.argv[1] == "sys-backup":
        hk_sys_backup()
    elif sys.argv[1] == "sys-maint":
        hk_sys_maint()
    elif sys.argv[1] == "timemachine-image":
        hk_timemachine_image()
    elif sys.argv[1] == "update-chrome":
        hk_update_chrome()
    elif sys.argv[1] == "upgrade-dropbox-pic":
        hk_upgrade_dropbox_pic()
    elif sys.argv[1] == "write-crc32":
        hk_write_crc32()
    elif sys.argv[1] == "write-crc32-new-only":
        hk_write_crc32_new_only()
    elif sys.argv[1] == "zip":
        if len(sys.argv) < 4:
            print "Not enough parameters!"
            exit(0)
        hk_zip()
    elif sys.argv[1] == "zip-sub-dir":
        hk_zip_sub_dir()
    else:
        print "command '%s' not understood, see 'housekeeper.py help' for more info" % sys.argv[1]

