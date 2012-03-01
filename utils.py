#!/usr/bin/env python

# General utilities. And also provide useful routines for other scripts.
#
# Author: Santa Zhang (santa1987@gmail.com)
#

from __future__ import with_statement
from contextlib import closing
import sys
import os
import time
import random
import traceback
import re
from zipfile import ZipFile, ZIP_DEFLATED

def pretty_fsize(fsize, k=1024.):
    unit = "B"
    k *= 1.0
    if fsize > k:
        fsize = 1.0 * fsize / k
        unit = "KB"
    if fsize > k:
        fsize = 1.0 * fsize / k
        unit = "MB"
    if fsize > k:
        fsize = 1.0 * fsize / k
        unit = "GB"
    if fsize > k:
        fsize = 1.0 * fsize / k
        unit = "TB"
    return "%.2f%s" % (fsize, unit)

def root_required():
    if os.getuid() != 0:
        raise Exception("root required! please run with 'sudo'!")


def is_mac():
    return (os.name == 'posix' and os.path.exists("/mach_kernel"))

def mac_required():
    if not is_mac():
        raise Exception("Only Mac supported!")

def is_well_formed_uuid(uuid):
    uuid = uuid.lower()
    if re.match("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", uuid) == None:
        return False
    return True


def check_good_zip_fn(fn):
    if fn.startswith("/"):
        fn = fn[1:]
    print "    adding: %s" % fn
    ok = True
    for c in fn:
        if ord(c) > 127:
            ok = False
    if ok == False:
        print "*** warning: %s is not a good name! English-only filename is better." % fn
    return fn


def zip_add_dir(zip_file, dir_path):
    ok = True
    assert os.path.isdir(dir_path)
    splt = os.path.split(dir_path)
    if splt[1] != "":
        chop_len = len(os.path.split(dir_path)[0])
    else:
        chop_len = 0
    for root, dirs, files in os.walk(dir_path):
        for d_ent in dirs:
            # generate zip entry for each folder, even empty ones
            try:
                absfn = os.path.join(root, d_ent)
                zfn = absfn[chop_len:]
                zfn = check_good_zip_fn(zfn)
                zip_file.write(absfn, zfn)
            except Exception as e:
                ok = False
                raise e # re-throw
        for fn in files:
            # ignore useless files
            absfn = os.path.join(root, fn)
            if fn.lower() == ".ds_store" or fn.lower() == "thumbs.db":
                print "exclude useless file '%s' from zip file" % absfn
                continue
            try:
                zfn = absfn[chop_len:]
                zfn = check_good_zip_fn(zfn)
                zip_file.write(absfn, zfn)
            except Exception as e:
                ok = False
                raise e # re-throw
    return ok


def zip_add_file(zip_file, file_path):
    ok = True
    assert os.path.isfile(file_path)
    try:
        zfn = os.path.split(file_path)[1]
        zfn = check_good_zip_fn(zfn)
        zip_file.write(file_path, zfn)
    except Exception as e:
        ok = False
        raise e # re-throw
    return ok


def zipdir(basedir, archivename):
    ok = True
    assert os.path.isdir(basedir)
    with closing(ZipFile(archivename, "w", ZIP_DEFLATED)) as z:
        for root, dirs, files in os.walk(basedir):
            #NOTE: ignore empty directories
            for fn in files:
                # ignore useless files
                absfn = os.path.join(root, fn)
                if fn.lower() == ".ds_store" or fn.lower() == "thumbs.db":
                    print "exclude useless file '%s' from zip file" % absfn
                    continue
                try:
                    zfn = absfn[len(basedir)+len(os.sep):] #XXX: relative path
                    z.write(absfn, zfn)
                except Exception as e:
                    ok = False
                    raise e # re-throw
    return ok

def zipfile(fpath, archivepath):
    ok = True
    assert os.path.isfile(fpath)
    with closing(ZipFile(archivepath, "w", ZIP_DEFLATED)) as z:
        try:
            zfn = os.path.split(fpath)[1]
            z.write(fpath, zfn)
        except Exception as e:
            ok = False
            raise e # re-threow
    return ok

def os_is_windows():
    return os.name == "nt"

def os_is_linux():
    return os.name == "posix" and os.path.exists("/initrd.img")

def os_is_mac():
    return os.name == "posix" and os.path.exists("/mach_kernel")

def get_config(key, default_value=None):
    module_name = os.path.basename(sys.argv[0])
    if "." in module_name:
        module_name = os.path.splitext(module_name)[0]

    value = None
    for conf_main_fn in ["toolkit.conf", "toolkit.private.conf"]:
        conf_fn = os.path.join(os.path.split(__file__)[0], conf_main_fn)
        if os.path.exists(conf_fn) == False:
            continue

        if key.startswith(module_name + "."):
            full_key = key
        else:
            full_key = module_name + "." + key

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
                if line[:idx] == full_key + ".windows" and os_is_windows():
                    value = line[(idx + 1):]
                    break
                elif line[:idx] == full_key + ".mac" and os_is_mac():
                    value = line[(idx + 1):]
                    break
                elif line[:idx] == full_key + ".linux" and os_is_linux():
                    value = line[(idx + 1):]
                    break
                elif line[:idx] == full_key + ".posix" and os.name == "posix":
                    value = line[(idx + 1):]
                    break
                elif line[:idx] == full_key:
                    value = line[(idx + 1):]
                    break
                elif line[:idx] == key + ".windows" and os_is_windows():
                    value = line[(idx + 1):]
                    break
                elif line[:idx] == key + ".mac" and os_is_mac():
                    value = line[(idx + 1):]
                    break
                elif line[:idx] == key + ".linux" and os_is_linux():
                    value = line[(idx + 1):]
                    break
                elif line[:idx] == key + ".posix" and os.name == "posix":
                    value = line[(idx + 1):]
                    break
                elif line[:idx] == key:
                    value = line[(idx + 1):]
                    break
        finally:
            if f != None:
                f.close()
            if value != None:
                break

    if default_value != None and value == None:
        value = default_value
    if value == None:
        raise Exception("Config '%s' not found!" % key)
    else:
        if "passwd" in key:
            print "[config] %s=**** (private info hidden)" % key
        else:
            print "[config] %s=%s" % (key, value)
        return value

def is_hex(text):
    text = text.lower()
    for c in text:
        if ('0' <= c and c <= '9') or ('a' <= c and c <= 'f'):
            continue
        else:
            return False
    return True

def is_ascii(text):
    for c in text:
        if ord(c) >= 128 or ord(c) < 0:
            return False
    return True

def is_image(fname):
    fname = fname.lower()
    for ext in [".jpg", ".png", ".gif", ".swf", ".bmp", ".pgm"]:
        if fname.endswith(ext):
            return True
    return False

def is_movie(fname):
    fname = fname.lower()
    for ext in [".avi", ".mp4", ".wmv", ".mkv", ".rmvb", ".rm"]:
        if fname.endswith(ext):
            return True
    return False

def is_music(fname):
    fname = fname.lower()
    for ext in [".mp3", ".m4a", ".ape", ".flac", ".tta", ".wav"]:
        if fname.endswith(ext):
            return True
    return False

def write_log(text):
    try:
        print text
    except:
        pass
    main_name = os.path.basename(sys.argv[0])
    if "." in main_name:
        main_name = os.path.splitext(main_name)[0]
    log_folder = os.path.join(os.path.split(__file__)[0], "log")
    if os.path.exists(log_folder) == False:
        os.makedirs(log_folder)
    log_fn = os.path.join(log_folder, main_name + ".log")
    f = open(log_fn, "a")
    tm = time.strftime("%Y.%m.%d %H:%M:%S", time.localtime())
    try:
        f.write("[%s] %s\n" % (tm, text))
    except:
        pass
    f.close()

def random_token(size=5):
    token = ""
    alphabet = "abcdefghijklmnopqrst0123456789"
    for i in range(size):
        token += alphabet[random.randint(0, len(alphabet) - 1)]
    return token

