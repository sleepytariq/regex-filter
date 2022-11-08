#!/usr/bin/env python3

import gzip
import json
import os
import random
import re
import shutil
import string
import sys
import tarfile
import tempfile
import zipfile
import py7zr
from argparse import ArgumentParser
from charset_normalizer import from_path


def show_error(message: str) -> None:
    print(f"[ERROR]: {message}")


def load_json(path: str) -> dict[str, str]:
    try:
        with open(path, "r") as f:
            dictionary = json.load(f)
        return dictionary
    except json.JSONDecodeError:
        show_error("failed to parse json file")
        sys.exit(1)
    except FileNotFoundError:
        show_error("json file not found")
        sys.exit(1)


def is_gzipfile(path: str) -> bool:
    with open(path, "rb") as f:
        return f.read(2) == b"\x1f\x8b"


def is_compressed(path: str) -> str | bool:
    if os.path.isdir(path):
        return False

    if zipfile.is_zipfile(path):
        return "zip"

    if tarfile.is_tarfile(path):
        if path.endswith("gz"):
            tartype = ":gz"
        elif path.endswith("bz") or path.endswith("bz2"):
            tartype = ":bz2"
        elif path.endswith("xz"):
            tartype = ":xz"
        else:
            tartype = ""
        return "tar" + tartype

    if py7zr.is_7zfile(path):
        return "7zip"

    if is_gzipfile(path):
        return "gzip"

    return False


def decompress(path: str, arctype: str) -> None:
    if arctype != "gzip":
        with tempfile.TemporaryDirectory() as td:
            if arctype == "zip":
                with zipfile.ZipFile(path, "r") as zf:
                    zf.extractall(td)

            elif arctype.startswith("tar"):
                tartype = arctype.replace("tar", "")
                with tarfile.open(path, "r" + tartype) as tf:
                    tf.extractall(td)

            elif arctype == "7zip":
                with py7zr.SevenZipFile(path, "r") as zf:
                    zf.extractall(td)

            os.remove(path)
            shutil.copytree(td, path)
        return

    with tempfile.TemporaryFile("wb+") as tf:
        with gzip.open(path, "rb") as gzf:
            tf.write(gzf.read())
        tf.seek(0)
        with open(path, "wb") as f:
            f.write(tf.read())


def compress(path: str, arctype: str) -> None:
    temp = path + "_temp"

    if arctype == "zip":
        with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    p = os.path.join(root, filename)
                    zf.write(p, arcname=p.replace(path + os.path.sep, ""))

    elif arctype.startswith("tar"):
        tartype = arctype.replace("tar", "")
        with tarfile.open(temp, "w" + tartype) as tf:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    p = os.path.join(root, filename)
                    tf.add(p, arcname=p.replace(path + os.path.sep, ""))

    elif arctype == "7zip":
        with py7zr.SevenZipFile(temp, "w") as zf:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    p = os.path.join(root, filename)
                    zf.write(p, arcname=p.replace(path + os.path.sep, ""))

    elif arctype == "gzip":
        with open(path, "rb") as f:
            with gzip.open(temp, "wb") as gzf:
                gzf.write(f.read())

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
    except Exception as e:
        show_error(f"failed to read {path.replace(temp_dir_name + os.path.sep, '')}")
        return

    total_count = 0
    for regex, sub in filter_list.items():
        text, count = re.subn(regex, sub, text, flags=re.IGNORECASE)
        total_count += count

    if not total_count:
        print(f"[NOT MODIFIED]: {path.replace(temp_dir_name + os.path.sep, '')}")
        return

    with open(path, "w", encoding=enc_type) as f:
        f.write(text)
    print(f"[MODIFIED {total_count}]: {path.replace(temp_dir_name + os.path.sep, '')}")


def rename_file(path: str):
    new_name = old_name = os.path.basename(path)
    for regex, sub in filter_list.items():
        new_name = re.sub(regex, sub, new_name, flags=re.IGNORECASE)

    if new_name == old_name:
        print(f"[NOT RENAMED]: {path.replace(temp_dir_name + os.path.sep, '')}")
        return

    new_path = os.path.join(os.path.dirname(path), new_name)
    if os.path.exists(new_path):
        new_name = get_random_string() + new_name
        new_path = os.path.join(os.path.dirname(path), new_name)
    os.rename(path, new_path)
    print(f"[RENAMED]: {path.replace(temp_dir_name + os.path.sep, '')} => {new_name}")


def clean_files(path: str, mode: str):
    for p in [os.path.join(path, item) for item in os.listdir(path)]:

        if os.path.isdir(p):
            clean_files(p, mode)
            if mode == "rename":
                rename_file(p)
            continue

        if arctype := is_compressed(p):
            try:
                decompress(p, arctype)
            except Exception:
                show_error(f"failed to extract {p.replace(temp_dir_name + os.path.sep, '')}")
            if os.path.isdir(p):
                clean_files(p, mode)
            elif mode == "modify":
                modify_file(p)
            compress(p, arctype)
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
        "-f", "--filter", type=str, help="path to a json file in REGEX:WORD format", required=True
    )
    required.add_argument(
        "-o", "--output", type=str, help="path to output directory", required=True
    )
    modifiers.add_argument(
        "-m", "--modify", action="store_true", help="use filter to modify content of files"
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

        with tempfile.TemporaryDirectory() as td:
            global temp_dir_name
            temp_dir_name = td

            for item in args.input:
                if not os.path.exists(item):
                    show_error(f"{item} does not exist")
                    sys.exit(1)

                if os.path.isdir(item):
                    item = item.rstrip(os.path.sep)
                    shutil.copytree(item, os.path.join(temp_dir_name, os.path.basename(item)))
                else:
                    shutil.copyfile(item, os.path.join(temp_dir_name, os.path.basename(item)))

            if args.modify:
                clean_files(temp_dir_name, "modify")

            if args.modify and args.rename:
                print("-" * os.get_terminal_size().columns)

            if args.rename:
                clean_files(temp_dir_name, "rename")

            out_dir = os.path.join(args.output, "REGEX_FILTER")
            shutil.rmtree(out_dir, ignore_errors=True)
            shutil.move(temp_dir_name, out_dir)
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
