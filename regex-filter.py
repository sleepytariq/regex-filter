#!/usr/bin/env python3

import os
import sys
import json
import shutil
import re
from argparse import ArgumentParser
from charset_normalizer import from_path
from colorama import Fore, Back, Style, init


def show_error(message: str):
    print(f"{Style.BRIGHT}{Fore.WHITE}{Back.RED}ERROR{Style.RESET_ALL} {message}")


def show_info(message: str):
    print(f"{Style.BRIGHT}{Fore.WHITE}{Back.BLUE}INFO{Style.RESET_ALL} {message}")


def show_change(message: str):
    print(f"{Style.BRIGHT}{Fore.WHITE}{Back.GREEN}CHANGED{Style.RESET_ALL} {message}")


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
    count = 0
    try:
        enc_type = from_path(file).best().encoding
        f = open(file, "r+", encoding=enc_type)
        text = f.read()
    except Exception:
        show_error(f"failed to read {os.path.basename(file)}")
        return

    for regex, substitute in filter_list.items():
        count += len(re.findall(regex, text, flags=re.IGNORECASE))
        text = re.sub(regex, substitute, text, flags=re.IGNORECASE)

    if count > 0:
        f.seek(0)
        f.write(text)
        f.truncate()
        show_change(f"({count}) {file}")
    else:
        show_info(f"no changes to {file}")

    f.close()


def clean_files(filter_list: dict, directory: str):
    for file in [os.path.join(directory, item) for item in os.listdir(directory)]:

        if os.path.isdir(file):
            clean_files(filter_list, file)
            continue

        if file.endswith(".zip"):
            shutil.unpack_archive(file, directory)
            os.remove(file)
            file = file.replace(".zip", "")
            if os.path.isdir(file):
                clean_files(filter_list, file)
                shutil.make_archive(file, "zip")
                shutil.rmtree(file)
            else:
                clean_a_file(filter_list, file)
                shutil.make_archive(file, "zip")
                os.remove(file)
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

    init()

    args = parse_arguments()

    if not os.path.exists(args.directory):
        show_error("directory not found")
        sys.exit(1)

    if not os.path.isdir(args.directory):
        show_error(f"{args.directory} is not a directory")
        sys.exit(1)

    if not os.path.exists(args.directory.rstrip("/") + "_bak"):
        shutil.copytree(args.directory, args.directory.rstrip("/") + "_bak")

    filter_list = load_json(args.filter)
    files = [os.path.join(args.directory, item) for item in os.listdir(args.directory)]

    if not files:
        show_error("no files in directory")
        sys.exit(1)

    clean_files(filter_list, args.directory)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
