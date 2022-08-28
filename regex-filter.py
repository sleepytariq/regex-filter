import os
from shutil import copy, rmtree
from re import findall, sub, IGNORECASE
from colorama import Fore, init
from json import load, JSONDecodeError
from argparse import ArgumentParser
from sys import exit
from charset_normalizer import from_path
from random import choice
from signal import signal, SIGINT

init()
cyan = Fore.CYAN
yellow = Fore.YELLOW
green = Fore.GREEN
red = Fore.RED
reset = Fore.RESET


def signal_handler(signal, frame):
    exit(1)


def load_json(json_file):
    try:
        with open(json_file, "r") as jf:
            arr = load(jf)
    except JSONDecodeError:
        print(f"{red}[X]{reset} FAILED TO LOAD JSON FILE")
        exit(1)
    except FileNotFoundError:
        print(f"{red}[X]{reset} JSON FILE NOT FOUND")
        exit(1)
    return arr


def clean_files(filter_list, new_dir):
    for text_file in [f"{new_dir}/{item}" for item in os.listdir(new_dir)]:
        count = 0

        try:
            enc_type = from_path(text_file).best().encoding
            f = open(text_file, "r+", encoding=enc_type)
            text = f.read()
        except Exception:
            print(f"{red}[X]{reset} FAILED TO READ {cyan}{os.path.basename(text_file)}{reset}")
            continue

        for regex, substitute in filter_list.items():
            count += len(findall(regex, text, flags=IGNORECASE))
            text = sub(regex, substitute, text, flags=IGNORECASE)

        if count > 0:
            f.seek(0)
            f.write(text)
            f.truncate()
            print(f"{green}[+]{reset} CHANGED {cyan}{count}{reset} MATCHES FROM {cyan}{os.path.basename(text_file)}{reset}")
        else:
            print(f"{yellow}[!]{reset} NO CHANGES FROM {cyan}{os.path.basename(text_file)}{reset}")

        f.close()


def rename_files(filter_list, new_dir):
    for text_file in os.listdir(new_dir):
        changed = False
        new_name = text_file

        for regex, substitute in filter_list.items():
            new_name = sub(regex, substitute, new_name)

        if new_name != text_file:
            if os.path.exists(f"{new_dir}/{new_name}"):
                new_name = "".join([choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890") for _ in range(5)]) + "_" + new_name
            os.rename(f"{new_dir}/{text_file}", f"{new_dir}/{new_name}")
            print(f"{green}[+]{reset} RENAMED {cyan}{text_file}{reset} TO {cyan}{new_name}{reset}")
        else:
            print(f"{yellow}[!]{reset} DID NOT RENAME {cyan}{text_file}{reset}")


def parse_arguments():
    parser = ArgumentParser(description="Replace matched strings in file names or file content with specified substitute using regular expressions", add_help=False)
    required = parser.add_argument_group("required")
    modifiers = parser.add_argument_group("modifiers")
    optional = parser.add_argument_group("optional")
    required.add_argument("-d", "--directory", type=str, help="path to a directory containing files", required=True)
    required.add_argument("-f", "--filter", type=str, help="path to a json file in REGEX:WORD format", required=True)
    modifiers.add_argument("-m", "--modify", action="store_true", help="use the filter to modify content of files")
    modifiers.add_argument("-r", "--rename", action="store_true", help="use the filter to rename files")
    optional.add_argument("-h", "--help", action="help", help="show this help message and exit")
    return parser.parse_args()


def main():
    args = parse_arguments()

    if not (args.modify or args.rename):
        print(f"{red}[X]{reset} YOU NEED TO USE --modify AND/OR --rename MODIFIERS")
        exit(1)

    if not os.path.exists(args.directory):
        print(f"{red}[X]{reset} DIRECTORY NOT FOUND")
        exit(1)

    if not os.path.isdir(args.directory):
        print(f"{red}[X]{reset} {cyan}{args.directory}{reset} IS NOT A DIRECTORY")
        exit(1)

    new_dir = f"{args.directory}/cleaned_files"
    filter_list = load_json(args.filter)

    if os.path.exists(new_dir):
        rmtree(new_dir)
    os.makedirs(new_dir)

    for text_file in [f"{args.directory}/{item}" for item in os.listdir(args.directory) if os.path.isfile(f"{args.directory}/{item}")]:
        copy(text_file, new_dir)

    if args.modify:
        clean_files(filter_list, new_dir)

    if args.rename:
        rename_files(filter_list, new_dir)


if __name__ == "__main__":
    signal(SIGINT, signal_handler)
    main()
