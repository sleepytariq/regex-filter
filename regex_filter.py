import os
import sys
import json
import shutil
import re
import tempfile
import string
import random
from compression_handler import is_compressed, decompress, compress
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
                show_error(
                    f"failed to extract {p.replace(temp_dir, '').lstrip(os.path.sep)}"
                )
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
    modifiers.add_argument(
        "-r", "--rename", action="store_true", help="use filter to rename files"
    )
    optional.add_argument(
        "-h", "--help", action="help", help="show this help message and exit"
    )
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
