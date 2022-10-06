#!/usr/bin/env python3

import os
import sys
import json
import shutil
import re
import gzip
import zipfile
import tarfile
import py7zr
import tempfile
import string
import random
from argparse import ArgumentParser
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


def get_random_string():
    chars = string.ascii_letters + string.digits
    return "".join([random.choice(chars) for _ in range(5)]) + "_"


def is_gzipfile(path: str):
    with open(path, "rb") as f:
        return f.read(2) == b"\x1f\x8b"


def handle_zip(path: str, mode: str):
    temp = path + "_temp"
    os.rename(path, temp)
    os.makedirs(path)
    try:
        with zipfile.ZipFile(temp, "r") as zf:
            zf.extractall(path)
    except RuntimeError:
        show_error(
            f"failed to extract {path.replace(temp_dir, '').lstrip(os.path.sep)}"
        )
        return
    clean_files(path, mode)
    os.remove(temp)
    os.rename(path, temp)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, filenames in os.walk(temp):
            for filename in filenames:
                path = os.path.join(root, filename)
                zf.write(path, arcname=path.replace(temp, ""))
    shutil.rmtree(temp)
    if mode == "rename":
        rename_file(path)


def handle_tar(path: str, mode: str):
    if path.endswith("gz"):
        arctype = ":gz"
    elif path.endswith("bz") or path.endswith("bz2"):
        arctype = ":bz2"
    elif path.endswith("xz"):
        arctype = ":xz"
    elif path.endswith("lzma"):
        arctype = ":lzma"
    else:
        arctype = ""
    temp = path + "_temp"
    os.rename(path, temp)
    os.makedirs(path)
    try:
        with tarfile.open(temp, "r" + arctype) as tf:
            tf.extractall(path)
    except tarfile.ExtractError:
        show_error(
            f"failed to extract {path.replace(temp_dir, '').lstrip(os.path.sep)}"
        )
        return
    clean_files(path, mode)
    os.remove(temp)
    os.rename(path, temp)
    with tarfile.open(path, "w" + arctype) as tf:
        for root, dirs, filenames in os.walk(temp):
            for filename in filenames:
                path = os.path.join(root, filename)
                tf.add(path, arcname=path.replace(temp, ""))
    shutil.rmtree(temp)
    if mode == "rename":
        rename_file(path)


def handle_7zip(path: str, mode: str):
    temp = path + "_temp"
    os.rename(path, temp)
    os.makedirs(path)
    try:
        with py7zr.SevenZipFile(temp, "r") as zf:
            zf.extractall(path)
    except py7zr.Bad7zFile:
        show_error(
            f"failed to extract {path.replace(temp_dir, '').lstrip(os.path.sep)}"
        )
        return
    clean_files(path, mode)
    os.remove(temp)
    os.rename(path, temp)
    with py7zr.SevenZipFile(path, "w") as zf:
        for root, dirs, filenames in os.walk(temp):
            for filename in filenames:
                p = os.path.join(root, filename)
                zf.write(p, arcname=p.replace(temp, ""))
    shutil.rmtree(temp)
    if mode == "rename":
        rename_file(path)


def handle_gzip(path: str):
    temp = path + "_temp"
    os.rename(path, temp)
    try:
        with gzip.open(temp, "rb") as gzf:
            with open(path, "wb") as f:
                f.write(gzf.read())
    except gzip.BadGzipFile:
        show_error(f"failed to extract {path.replace(temp_dir, '')}")
        return

    modify_file(path)
    os.remove(temp)
    os.rename(path, temp)

    with open(temp, "rb") as f:
        with gzip.open(path, "wb") as gzf:
            gzf.write(f.read())

    os.remove(temp)


def modify_file(path: str):
    count = 0
    try:
        enc_type = from_path(path).best().encoding
        with open(path, "r", encoding=enc_type) as f:
            text = f.read()
    except Exception:
        show_error(f"failed to read {path.replace(temp_dir, '').lstrip(os.path.sep)}")
        return

    for regex, substitute in filter_list.items():
        count += len(re.findall(regex, text, flags=re.IGNORECASE))
        text = re.sub(regex, substitute, text, flags=re.IGNORECASE)

    if count:
        with open(path, "w", encoding=enc_type) as f:
            f.write(text)
        print(f"[MODIFIED {count}]: {path.replace(temp_dir, '').lstrip(os.path.sep)}")
    else:
        print(f"[NOT MODIFIED]: {path.replace(temp_dir, '').lstrip(os.path.sep)}")


def rename_file(path: str):
    new_name = name = os.path.basename(path)
    for regex, substitute in filter_list.items():
        new_name = re.sub(regex, substitute, new_name, flags=re.IGNORECASE)

    if new_name != name:
        new_path = os.path.join(os.path.dirname(path), new_name)
        if os.path.exists(new_path):
            new_name = get_random_string() + new_name
            new_path = os.path.join(os.path.dirname(path), new_name)
        os.rename(path, new_path)
        print(
            f"[RENAMED]: {path.replace(temp_dir, '').lstrip(os.path.sep)} => {new_path.replace(temp_dir, '').lstrip(os.path.sep)}"
        )
    else:
        print(f"[NOT RENAMED]: {path.replace(temp_dir, '').lstrip(os.path.sep)}")


def clean_files(dir: str, mode: str):
    for path in [os.path.join(dir, item) for item in os.listdir(dir)]:

        if os.path.isdir(path):
            if mode == "modify":
                clean_files(path, "modify")
            else:
                clean_files(path, "rename")
                rename_file(path)
            continue

        if zipfile.is_zipfile(path):
            handle_zip(path, mode)
            continue

        if tarfile.is_tarfile(path):
            handle_tar(path, mode)
            continue

        if py7zr.is_7zfile(path):
            handle_7zip(path, mode)
            continue

        if is_gzipfile(path) and mode == "modify":
            handle_gzip(path)
            continue

        if mode == "modify":
            modify_file(path)
        else:
            rename_file(path)


def parse_arguments():
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
    modifiers.add_argument(
        "-r", "--rename", action="store_true", help="use filter to rename files"
    )
    optional.add_argument(
        "-h", "--help", action="help", help="show this help message and exit"
    )
    return parser.parse_args()


def main():
    try:
        args = parse_arguments()

        if not (args.modify or args.rename):
            show_error("use -m and/or -r modifiers")
            sys.exit(1)

        global filter_list
        filter_list = load_json(args.filter)

        global temp_dir
        temp_dir = tempfile.mkdtemp()

        for item in args.input:
            if not os.path.exists(item):
                show_error(f"{item} not found")
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

        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        shutil.move(temp_dir, out_dir)
    except KeyboardInterrupt:
        try:
            shutil.rmtree(temp_dir)
        except NameError:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
