#!/usr/bin/env python3

import bz2
import gzip
import json
import lzma
import os
import random
import re
import shutil
import string
import sys
import tarfile
import tempfile
import zipfile
from argparse import ArgumentParser

import py7zr
from charset_normalizer import from_path


def show_error(message: str):
    print(f"[ERROR]: {message}")


def load_json(path: str):
    try:
        with open(path, "r") as f:
            dictionary = json.load(f)
        return dictionary
    except json.JSONDecodeError:
        show_error("failed to load json file")
        sys.exit(1)
    except FileNotFoundError:
        show_error("json file not found")
        sys.exit(1)


def is_gzipfile(path: str):
    with open(path, "rb") as f:
        return f.read(2) == b"\x1f\x8b"


def is_bzip2file(path: str):
    with open(path, "rb") as f:
        return f.read(3) == b"\x42\x5a\x68"


def is_lzmafile(path: str):
    with open(path, "rb") as f:
        return f.read(5) == b"\xfd\x37\x7a\x58\x5a"


def is_compressed(path: str):
    if os.path.isdir(path):
        return False

    return (
        zipfile.is_zipfile(path)
        or tarfile.is_tarfile(path)
        or py7zr.is_7zfile(path)
        or is_gzipfile(path)
        or is_bzip2file(path)
        or is_lzmafile(path)
    )


def decompress(path: str):
    temp = path + "_temp"
    try:
        if zipfile.is_zipfile(path):
            os.makedirs(temp)
            with zipfile.ZipFile(path, "r") as zf:
                zf.extractall(temp)
            arctype = "zip"

        elif tarfile.is_tarfile(path):
            if path.endswith("gz"):
                tartype = ":gz"
            elif path.endswith("bz") or path.endswith("bz2"):
                tartype = ":bz2"
            elif path.endswith("xz"):
                tartype = ":xz"
            else:
                tartype = ""
            with tarfile.open(path, "r" + tartype) as tf:
                tf.extractall(temp)
            arctype = "tar" + tartype

        elif py7zr.is_7zfile(path):
            with py7zr.SevenZipFile(path, "r") as zf:
                zf.extractall(temp)
            arctype = "7zip"

        elif is_gzipfile(path):
            with gzip.open(path, "rb") as gzf:
                with open(temp, "wb") as f:
                    f.write(gzf.read())
            arctype = "gzip"

        elif is_bzip2file(path):
            with bz2.open(path, "rb") as bzf:
                with open(temp, "wb") as f:
                    f.write(bzf.read())
            arctype = "bzip2"

        elif is_lzmafile(path):
            with lzma.open(path, "rb") as lf:
                with open(temp, "wb") as f:
                    f.write(lf.read())
            arctype = "lzma"

        else:
            return
        os.remove(path)
        os.rename(temp, path)
        return arctype
    except Exception:
        try:
            if os.path.isdir(temp):
                shutil.rmtree(temp)
            else:
                os.remove(temp)
        except FileNotFoundError:
            pass


def compress(path: str, arctype: str):
    temp = path + "_temp"
    if arctype == "zip":
        with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    p = os.path.join(root, filename)
                    zf.write(p, arcname=p.replace(path, "").lstrip(os.path.sep))

    elif arctype.startswith("tar"):
        tartype = arctype.replace("tar", "")
        with tarfile.open(temp, "w" + tartype) as tf:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    p = os.path.join(root, filename)
                    tf.add(p, arcname=p.replace(path, "").lstrip(os.path.sep))

    elif arctype == "7zip":
        with py7zr.SevenZipFile(temp, "w") as zf:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    p = os.path.join(root, filename)
                    zf.write(p, arcname=p.replace(path, "").lstrip(os.path.sep))

    elif arctype == "gzip":
        with open(path, "rb") as f:
            with gzip.open(temp, "wb") as gzf:
                gzf.write(f.read())

    elif arctype == "bzip2":
        with open(path, "rb") as f:
            with bz2.open(temp, "wb") as bzf:
                bzf.write(f.read())

    elif arctype == "lzma":
        with open(path, "rb") as f:
            with lzma.open(temp, "wb") as lf:
                lf.write(f.read())

    else:
        return

    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except FileNotFoundError:
        pass
    os.rename(temp, path)


def get_random_string():
    chars = string.ascii_letters + string.digits
    return "".join([random.choice(chars) for _ in range(5)]) + "_"


def modify_file(path: str):
    try:
        enc_type = from_path(path).best().encoding
        with open(path, "r", encoding=enc_type) as f:
            text = f.read()
    except Exception:
        show_error(f"failed to read {path.replace(temp_dir, '').lstrip(os.path.sep)}")
        return

    total_count = 0
    for regex, substitute in filter_list.items():
        text, count = re.subn(regex, substitute, text, flags=re.IGNORECASE)
        total_count += count

    if not total_count:
        print(f"[NOT MODIFIED]: {path.replace(temp_dir, '').lstrip(os.path.sep)}")
        return

    with open(path, "w", encoding=enc_type) as f:
        f.write(text)
    print(f"[MODIFIED {total_count}]: {path.replace(temp_dir, '').lstrip(os.path.sep)}")


def rename_file(path: str):
    new_name = name = os.path.basename(path)
    for regex, substitute in filter_list.items():
        new_name = re.sub(regex, substitute, new_name, flags=re.IGNORECASE)

    if new_name == name:
        print(f"[NOT RENAMED]: {path.replace(temp_dir, '').lstrip(os.path.sep)}")
        return

    new_path = os.path.join(os.path.dirname(path), new_name)
    if os.path.exists(new_path):
        new_name = get_random_string() + new_name
        new_path = os.path.join(os.path.dirname(path), new_name)
    os.rename(path, new_path)
    print(f"[RENAMED]: {path.replace(temp_dir, '').lstrip(os.path.sep)} => {new_name}")


def clean_files(path: str, mode: str):
    for p in [os.path.join(path, item) for item in os.listdir(path)]:
        if os.path.isdir(p):
            clean_files(p, mode)
            if mode == "rename":
                rename_file(p)
            continue

        if is_compressed(p):
            arctype = decompress(p)
            if arctype:
                if os.path.isdir(p):
                    clean_files(p, mode)
                elif mode == "modify":
                    modify_file(p)
                compress(p, arctype)
            else:
                show_error(f"failed to extract {p.replace(temp_dir, '').lstrip(os.path.sep)}")
            if mode == "rename":
                rename_file(p)
            continue

        if mode == "modify":
            modify_file(p)

        if mode == "rename":
            rename_file(p)


def get_args():
    parser = ArgumentParser(
        description="Replace matched strings in file content and file names with specified substitute using regular expressions",
        add_help=False,
    )
    required = parser.add_argument_group("required")
    modifiers = parser.add_argument_group("modifiers")
    optional = parser.add_argument_group("optional")
    required.add_argument(
        "-i",
        "--input",
        type=str,
        nargs="+",
        help="path to files or directories containing files",
        required=True,
    )
    required.add_argument(
        "-f",
        "--filter",
        type=str,
        help="path to a json file in REGEX:WORD format",
        required=True,
    )
    required.add_argument(
        "-o",
        "--output",
        type=str,
        help="path to output directory",
        required=True,
    )
    modifiers.add_argument(
        "-m",
        "--modify",
        action="store_true",
        help="use filter to modify content of files",
    )
    modifiers.add_argument("-r", "--rename", action="store_true", help="use filter to rename files")
    optional.add_argument("-h", "--help", action="help", help="show this help message and exit")
    return parser.parse_args()


def main():
    try:
        args = get_args()

        if not (args.modify or args.rename):
            show_error("use -m and/or -r modifiers")
            sys.exit(1)

        global filter_list
        filter_list = load_json(args.filter)

        global temp_dir
        temp_dir = tempfile.mkdtemp()

        for item in args.input:
            if not os.path.exists(item):
                continue

            if os.path.isdir(item):
                item = item.rstrip(os.path.sep)
                shutil.copytree(item, os.path.join(temp_dir, os.path.basename(item)))
            else:
                shutil.copyfile(item, os.path.join(temp_dir, os.path.basename(item)))

        if args.modify:
            clean_files(temp_dir, "modify")

        if args.modify and args.rename:
            print("-" * os.get_terminal_size().columns)

        if args.rename:
            clean_files(temp_dir, "rename")

        out_dir = os.path.join(args.output, "REGEX_FILTER")
        shutil.rmtree(out_dir, ignore_errors=True)
        shutil.move(temp_dir, out_dir)
    except KeyboardInterrupt:
        shutil.rmtree(temp_dir, ignore_errors=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
