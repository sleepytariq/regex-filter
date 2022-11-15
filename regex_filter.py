#!/usr/bin/env python3

import json
import os
import random
import re
import shutil
import string
import subprocess
import sys
import tempfile
from argparse import ArgumentParser

from charset_normalizer import from_path


def load_filter(path: str) -> dict[str, str]:
    try:
        with open(path, "r") as f:
            filter = json.load(f)
        return filter
    except json.JSONDecodeError:
        print("Error: Failed to parse filter")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: filter does not exist")
        sys.exit(1)
    except Exception:
        print("Error: Failed to read filter")
        sys.exit(1)


def get_random_string() -> str:
    chars = string.ascii_letters + string.digits
    return "".join([random.choice(chars) for _ in range(5)]) + "_"


def modify_file(path: str) -> None:
    try:
        enc_type = from_path(path).best().encoding
        with open(path, "r", encoding=enc_type) as f:
            text = f.read()
    except Exception:
        print(f"Error: Failed to read {path.replace(temp_dir + os.path.sep, '')}")
        return

    total_count = 0
    for regex, sub in filter.items():
        text, count = re.subn(regex, sub, text, flags=re.IGNORECASE)
        total_count += count

    if not total_count:
        print(f"Not Modified: {path.replace(temp_dir + os.path.sep, '')}")
        return

    with open(path, "w", encoding=enc_type) as f:
        f.write(text)

    print(f"Modified ({total_count}): {path.replace(temp_dir + os.path.sep, '')}")


def rename_file(path: str) -> None:
    new_name = current_name = os.path.basename(path)
    for regex, sub in filter.items():
        new_name = re.sub(regex, sub, new_name, flags=re.IGNORECASE)

    if new_name == current_name:
        print(f"Not Renamed: {path.replace(temp_dir + os.path.sep, '')}")
        return

    new_path = os.path.join(os.path.dirname(path), new_name)
    if os.path.exists(new_path):
        new_name = get_random_string() + new_name
        new_path = os.path.join(os.path.dirname(path), new_name)
    os.rename(path, new_path)
    print(f"Renamed: {path.replace(temp_dir + os.path.sep, '')} -> {new_name}")


def decompress(path: str) -> None:
    with tempfile.TemporaryDirectory() as td:
        subprocess.call(
            f'{sevenzip} x -y "{path}" -o"{td}"',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os.remove(path)
        shutil.copytree(td, path)


def compress(path: str) -> None:
    temp = path + "_temp"
    os.rename(path, temp)
    subprocess.call(
        f'{sevenzip} a -y "{path}" "{os.path.join(temp, "*")}"',
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.rmtree(temp)


def clean_files(path: str, mode: str) -> None:
    files = [os.path.join(path, item) for item in os.listdir(path)]
    for file in files:
        if os.path.isdir(file):
            clean_files(file, mode)
            if mode == "rename":
                rename_file(file)
            continue

        if sevenzip:
            code, output = subprocess.getstatusoutput(f'{sevenzip} t -y -p0 "{file}"')
            if code == 0:
                decompress(file)
                clean_files(file, mode)
                compress(file)
                if mode == "rename":
                    rename_file(file)
                continue
            else:
                if "Type =" in output:
                    print(
                        f"Error: Failed to extract {file.replace(temp_dir + os.path.sep, '')}"
                    )
                    continue

        if mode == "modify":
            modify_file(file)

        if mode == "rename":
            rename_file(file)


def get_args():
    parser = ArgumentParser(
        description="Replace matched strings in file content and file names with specified substitute using regular expressions",
        add_help=False,
    )
    required = parser.add_argument_group("Required")
    modifiers = parser.add_argument_group("Modifiers")
    optional = parser.add_argument_group("Optional")
    required.add_argument(
        "-i",
        "--input",
        type=str,
        nargs="+",
        help="Path to files or directories containing files",
        required=True,
    )
    required.add_argument(
        "-f",
        "--filter",
        type=str,
        help="Path to a json file in REGEX:WORD format",
        required=True,
    )
    required.add_argument(
        "-o", "--output", type=str, help="Path to output directory", required=True
    )
    modifiers.add_argument(
        "-m",
        "--modify",
        action="store_true",
        help="Use filter to modify content of files",
    )
    modifiers.add_argument(
        "-r", "--rename", action="store_true", help="Use filter to rename files"
    )
    optional.add_argument(
        "-h", "--help", action="help", help="Show this help message and exit"
    )

    return parser.parse_args()


def copy_to_temp(files: list[str]) -> None:
    for file in files:
        try:
            if os.path.isdir(file):
                shutil.copytree(file, os.path.join(temp_dir, shutil._basename(file)))
            else:
                shutil.copyfile(file, os.path.join(temp_dir, shutil._basename(file)))
        except FileNotFoundError:
            print(f"Error: {file} does not exist")
            sys.exit(1)
        except Exception:
            if os.path.isdir(file):
                print(f"Error: Failed to copy all of {file} to a temporary directory")
            else:
                print(f"Error: Failed to copy {file} to a temporary directory")


def copy_to_output(output: str) -> None:
    out_dir = os.path.join(output, "REGEX_FILTER")
    shutil.rmtree(out_dir, ignore_errors=True)
    try:
        shutil.copytree(temp_dir, out_dir)
    except Exception:
        print("Error: Unable to write to output directory")


def get_7z() -> str:
    sevenzip = ""
    for bin in ["7z", "7za", "7zr", "7zz"]:
        if shutil.which(bin):
            sevenzip = bin
            break

    if not sevenzip:
        print(
            "Error: Unable to find 7zip in PATH, compressed files will not be cleaned"
        )

    return sevenzip


def main():
    try:
        args = get_args()

        if not (args.modify or args.rename):
            print("Error: Use -m and/or -r modifiers")
            sys.exit(1)

        global filter
        filter = load_filter(args.filter)

        global sevenzip
        sevenzip = get_7z()

        global temp_dir
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_to_temp(args.input)

            width = os.get_terminal_size().columns

            if args.modify:
                print("MODIFY".center(width, "-"))
                clean_files(temp_dir, "modify")
                if not args.rename:
                    print("-" * width)

            if args.rename:
                print("RENAME".center(width, "-"))
                clean_files(temp_dir, "rename")
                print("-" * width)

            copy_to_output(args.output)

    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
