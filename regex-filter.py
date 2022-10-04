#!/usr/bin/env python3

import os
import sys
import json
import shutil
import re
import gzip
import zipfile
import tarfile
import tempfile
import string
import random
from argparse import ArgumentParser
from charset_normalizer import from_path
from colorama import Fore, init


def show_error(message: str):
    print(f"{Fore.RED}Error:{Fore.RESET} {message}")


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


def handle_zip_content(path: str):
    temp = path.replace(".zip", "")
    os.makedirs(temp)
    try:
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(temp)
    except RuntimeError:
        show_error(
            f"failed to extract {path.replace(temp_dir, '').lstrip(os.path.sep)}"
        )
        return
    clean_files(temp)
    os.remove(path)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for zroot, zdirs, zfilenames in os.walk(temp):
            for zfilename in zfilenames:
                zpath = os.path.join(zroot, zfilename)
                zf.write(zpath, arcname=zpath.replace(temp, ""))
    shutil.rmtree(temp)


def handle_zip_rename(path: str):
    temp = path.replace(".zip", "")
    os.makedirs(temp)
    try:
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(temp)
    except RuntimeError:
        show_error(
            f"failed to extract {path.replace(temp_dir, '').lstrip(os.path.sep)}"
        )
        return
    rename_files(temp)
    os.remove(path)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for zroot, zdirs, zfilenames in os.walk(temp):
            for zfilename in zfilenames:
                zpath = os.path.join(zroot, zfilename)
                zf.write(zpath, arcname=zpath.replace(temp, ""))
    shutil.rmtree(temp)
    rename_a_file(path)


def handle_tar_content(path: str):
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
        show_error(
            f"failed to extract {path.replace(temp_dir, '').lstrip(os.path.sep)}"
        )
        return
    clean_files(temp)
    os.remove(path)
    with tarfile.open(path, "w" + arctype) as tf:
        for troot, tdirs, tfilenames in os.walk(temp):
            for tfilename in tfilenames:
                tpath = os.path.join(troot, tfilename)
                tf.add(tpath, arcname=tpath.replace(temp, ""))
    shutil.rmtree(temp)


def handle_tar_rename(path: str):
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
        show_error(
            f"failed to extract {path.replace(temp_dir, '').lstrip(os.path.sep)}"
        )
        return
    rename_files(temp)
    os.remove(path)
    with tarfile.open(path, "w" + arctype) as tf:
        for troot, tdirs, tfilenames in os.walk(temp):
            for tfilename in tfilenames:
                tpath = os.path.join(troot, tfilename)
                tf.add(tpath, arcname=tpath.replace(temp, ""))
    shutil.rmtree(temp)
    rename_a_file(path)


def handle_gzip_content(path: str):
    temp = path.replace(".gz", "")
    try:
        with gzip.open(path, "rb") as gzf:
            with open(temp, "wb") as f:
                f.write(gzf.read())
    except gzip.BadGzipFile:
        show_error(f"failed to extract {path.replace(temp_dir, '')}")
        return

    clean_a_file(temp)

    with open(temp, "rb") as f:
        with gzip.open(path, "wb") as gzf:
            gzf.write(f.read())

    os.remove(temp)


def clean_a_file(path: str):
    rel_path = path.replace(temp_dir, "").lstrip(os.path.sep)
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
    print(f"{Fore.GREEN if count else Fore.YELLOW}{count}:{Fore.RESET} {rel_path}")


def clean_files(dir: str):
    for root, dirs, filenames in os.walk(dir):
        for filename in filenames:
            path = os.path.join(root, filename)

            if zipfile.is_zipfile(path):
                handle_zip_content(path)
                continue

            if tarfile.is_tarfile(path):
                handle_tar_content(path)
                continue

            if path.endswith(".gz"):
                handle_gzip_content(path)
                continue

            clean_a_file(path)


def rename_a_file(path: str):
    path = path.rstrip(os.path.sep)
    name = os.path.basename(path)
    new_name = name
    for regex, substitute in filter_list.items():
        new_name = re.sub(regex, substitute, new_name, flags=re.IGNORECASE)

    if new_name != name:
        new_path = os.path.join(os.path.dirname(path), new_name)
        if os.path.exists(new_path):
            new_name = get_random_string() + new_name
            new_path = os.path.join(os.path.dirname(path), new_name)
        os.rename(path, new_path)
        print(
            f"{path.replace(temp_dir, '').lstrip(os.path.sep)} {Fore.GREEN}-->{Fore.RESET} {new_path.replace(temp_dir, '').lstrip(os.path.sep)}"
        )
    else:
        print(
            f"{Fore.YELLOW}!{Fore.RESET} {path.replace(temp_dir, '').lstrip(os.path.sep)}"
        )


def rename_files(dir: str):
    for path in [os.path.join(dir, item) for item in os.listdir(dir)]:
        if os.path.isdir(path):
            rename_files(path)
            rename_a_file(path)
            continue

        if zipfile.is_zipfile(path):
            handle_zip_rename(path)
            continue

        if tarfile.is_tarfile(path):
            handle_tar_rename(path)
            continue

        rename_a_file(path)


def parse_arguments():
    parser = ArgumentParser(
        description="Replace matched strings in file content with specified substitute using regular expressions",
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
        help="use the filter to modify content of files",
    )
    modifiers.add_argument(
        "-r", "--rename", action="store_true", help="use the filter to rename files"
    )
    optional.add_argument(
        "-h", "--help", action="help", help="show this help message and exit"
    )
    return parser.parse_args()


def main():
    try:
        init()
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
            clean_files(temp_dir)

        if args.modify and args.rename:
            print("-" * os.get_terminal_size().columns)

        if args.rename:
            rename_files(temp_dir)

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
