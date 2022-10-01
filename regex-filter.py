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
from colorama import Fore, Style, init


def show_error(message: str):
    print(f"{Style.BRIGHT}{Fore.LIGHTRED_EX}Error:{Style.RESET_ALL} {message}")


def show_change(count: int, path: str):
    print(
        f"{Style.BRIGHT}{Fore.LIGHTGREEN_EX if count > 0 else Fore.LIGHTBLUE_EX}({count}):{Style.RESET_ALL} {path}"
    )


def load_json(json_file: str):
    try:
        with open(json_file, "r") as f:
            arr = json.load(f)
    except json.JSONDecodeError:
        show_error("failed to load json file")
        sys.exit(1)
    except FileNotFoundError:
        show_error("json file not found")
        sys.exit(1)
    return arr


def clean_a_file(filter_list: dict, file: str):
    file_rel_path = file.split("CLEAN")[1]
    count = 0
    try:
        enc_type = from_path(file).best().encoding
        with open(file, "r", encoding=enc_type) as f:
            text = f.read()
    except Exception:
        show_error(f"failed to read {file_rel_path}")
        return

    for regex, substitute in filter_list.items():
        count += len(re.findall(regex, text, flags=re.IGNORECASE))
        text = re.sub(regex, substitute, text, flags=re.IGNORECASE)

    if count > 0:
        with open(file, "w", encoding=enc_type) as f:
            f.write(text)
    show_change(count, file_rel_path)


def clean_files(filter_list: dict, directory: str):
    for file in [os.path.join(directory, item) for item in os.listdir(directory)]:
        if os.path.isdir(file):
            clean_files(filter_list, file)
            continue

        if zipfile.is_zipfile(file):
            temp = file.replace(".zip", "")
            os.makedirs(temp)
            try:
                with zipfile.ZipFile(file, "r") as zf:
                    zf.extractall(temp)
            except RuntimeError:
                show_error(f"failed to extract {file}")
                continue
            os.remove(file)
            clean_files(filter_list, temp)
            out_files = [os.path.join(temp, item) for item in os.listdir(temp)]
            with zipfile.ZipFile(file, "w") as zf:
                for out_file in out_files:
                    zf.write(out_file, arcname=os.path.basename(out_file))
            shutil.rmtree(temp)
            continue

        if tarfile.is_tarfile(file):
            if file.endswith("tar"):
                temp = file.replace(".tar", "")
                arctype = ""
            elif file.endswith("gz"):
                temp = file.replace(".tar.gz", "")
                temp = temp.replace(".tgz", "")
                arctype = ":gz"
            os.makedirs(temp)
            try:
                with tarfile.open(file, "r" + arctype) as tf:
                    tf.extractall(temp)
            except tarfile.ExtractError:
                show_error(f"failed to extract {file}")
                continue
            os.remove(file)
            clean_files(filter_list, temp)
            out_files = [os.path.join(temp, item) for item in os.listdir(temp)]
            with tarfile.open(file, "w" + arctype) as tf:
                for out_file in out_files:
                    tf.add(out_file, arcname=os.path.basename(out_file))
            shutil.rmtree(temp)
            continue

        if file.endswith(".gz"):
            temp = file.replace(".gz", "")
            try:
                with gzip.open(file, "rb") as gzf:
                    with open(temp, "wb") as f:
                        f.write(gzf.read())
            except gzip.ExtractError:
                show_error(f"failed to extract {file}")
                continue
            clean_a_file(filter_list, temp)
            with open(temp, "rb") as f:
                with gzip.open(file, "wb") as gzf:
                    gzf.write(f.read())
            os.remove(temp)
            continue

        clean_a_file(filter_list, file)


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

        new_dir = os.path.join(args.directory, "CLEAN")

        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)

        shutil.copytree(args.directory, new_dir)
        filter_list = load_json(args.filter)
        clean_files(filter_list, new_dir)
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
