#!/usr/bin/env python3

import os
import sys
import json
import shutil
import re
import gzip
import zipfile
import tarfile
from argparse import ArgumentParser
from charset_normalizer import from_path
from colorama import Fore, init


def show_error(message: str):
    print(f"{Fore.RED}Error:{Fore.RESET} {message}")


def show_change(count: int, path: str):
    print(f"{Fore.GREEN if count else Fore.YELLOW}{count}:{Fore.RESET} {path}")


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


def handle_zip(path: str):
    temp = path.replace(".zip", "")
    os.makedirs(temp)
    try:
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(temp)
    except RuntimeError:
        show_error(f"failed to extract {path.replace(new_dir, '')}")
        return
    clean_files(temp)
    os.remove(path)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for zroot, zdirs, zfilenames in os.walk(temp):
            for zfilename in zfilenames:
                zpath = os.path.join(zroot, zfilename)
                zf.write(zpath, arcname=zpath.replace(temp, ""))
    shutil.rmtree(temp)


def handle_tar(path: str):
    if path.endswith("gz"):
        temp = path.replace(".tar.gz", "")
        temp = temp.replace(".tgz", "")
        arctype = ":gz"
    else:
        temp = path.replace(".tar", "")
        arctype = ""
    os.makedirs(temp)
    try:
        with tarfile.open(path, "r" + arctype) as tf:
            tf.extractall(temp)
    except tarfile.ExtractError:
        show_error(f"failed to extract {path.replace(new_dir, '')}")
        return
    clean_files(temp)
    os.remove(path)
    with tarfile.open(path, "w" + arctype) as tf:
        for troot, tdirs, tfilenames in os.walk(temp):
            for tfilename in tfilenames:
                tpath = os.path.join(troot, tfilename)
                tf.add(tpath, arcname=tpath.replace(temp, ""))
    shutil.rmtree(temp)


def handle_gzip(path: str):
    temp = path.replace(".gz", "")
    try:
        with gzip.open(path, "rb") as gzf:
            with open(temp, "wb") as f:
                f.write(gzf.read())
    except gzip.BadGzipFile:
        show_error(f"failed to extract {path.replace(new_dir, '')}")
        return

    clean_a_file(temp)

    with open(temp, "rb") as f:
        with gzip.open(path, "wb") as gzf:
            gzf.write(f.read())

    os.remove(temp)


def clean_a_file(path: str):
    rel_path = path.replace(new_dir, "")
    count = 0
    try:
        enc_type = from_path(path).best().encoding
        with open(path, "r", encoding=enc_type) as f:
            text = f.read()
    except Exception:
        show_error(f"failed to read {rel_path}")
        return

    for regex, substitute in filter_list.items():
        count += len(re.findall(regex, text, flags=re.IGNORECASE))
        text = re.sub(regex, substitute, text, flags=re.IGNORECASE)

    if count:
        with open(path, "w", encoding=enc_type) as f:
            f.write(text)
    show_change(count, rel_path)


def clean_files(dir: str):
    for root, dirs, filenames in os.walk(dir):
        for filename in filenames:
            path = os.path.join(root, filename)

            if zipfile.is_zipfile(path):
                handle_zip(path)
                continue

            if tarfile.is_tarfile(path):
                handle_tar(path)
                continue

            if path.endswith(".gz"):
                handle_gzip(path)
                continue

            clean_a_file(path)


def parse_arguments():
    parser = ArgumentParser(
        description="Replace matched strings in file content with specified substitute using regular expressions",
        add_help=False,
    )
    required = parser.add_argument_group("required")
    optional = parser.add_argument_group("optional")
    required.add_argument(
        "-d",
        "--directory",
        type=str,
        help="path to a directory containing files",
        required=True,
    )
    required.add_argument(
        "-f",
        "--filter",
        type=str,
        help="path to a json file in REGEX:WORD format",
        required=True,
    )
    optional.add_argument(
        "-h", "--help", action="help", help="show this help message and exit"
    )
    return parser.parse_args()


def main():
    try:
        init()
        args = parse_arguments()

        if not os.path.exists(args.directory):
            show_error("directory not found")
            sys.exit(1)

        if not os.path.isdir(args.directory):
            show_error(f"{args.directory} is not a directory")
            sys.exit(1)

        if not os.listdir(args.directory):
            show_error("no files in directory")
            sys.exit(1)

        global filter_list
        filter_list = load_json(args.filter)

        global new_dir
        new_dir = os.path.join(args.directory, "CLEAN")

        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)
        shutil.copytree(args.directory, new_dir)

        clean_files(new_dir)
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
