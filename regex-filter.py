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


def signal_handler(signal, frame):
    exit(1)


def load_json(json_file):
    try:
        with open(json_file, "r") as jf:
            arr = load(jf)
    except JSONDecodeError:
        print(f"{Fore.RED}[X]{Fore.RESET} FAILED TO LOAD JSON FILE")
        exit(1)
    except FileNotFoundError:
        print(f"{Fore.RED}[X]{Fore.RESET} JSON FILE NOT FOUND")
        exit(1)
    return arr


def clean_files(filter_list, new_dir):
    for text_file in [os.path.join(new_dir, item) for item in os.listdir(new_dir)]:
        count = 0
        try:
            enc_type = from_path(text_file).best().encoding
            f = open(text_file, "r+", encoding=enc_type)
            text = f.read()
        except Exception:
            print(f"{Fore.RED}[X]{Fore.RESET} FAILED TO READ {Fore.CYAN}{os.path.basename(text_file)}{Fore.RESET}")
            continue

        for regex, substitute in filter_list.items():
            count += len(findall(regex, text, flags=IGNORECASE))
            text = sub(regex, substitute, text, flags=IGNORECASE)

        if count > 0:
            f.seek(0)
            f.write(text)
            f.truncate()
            print(f"{Fore.GREEN}[+]{Fore.RESET} CHANGED {Fore.CYAN}{count}{Fore.RESET} MATCHES FROM {Fore.CYAN}{os.path.basename(text_file)}{Fore.RESET}")
        else:
            print(f"{Fore.YELLOW}[!]{Fore.RESET} NO CHANGES FROM {Fore.CYAN}{os.path.basename(text_file)}{Fore.RESET}")

        f.close()


def rename_files(filter_list, new_dir):
    for text_file in os.listdir(new_dir):
        changed = False
        new_name = text_file

        for regex, substitute in filter_list.items():
            new_name = sub(regex, substitute, new_name)

        if new_name != text_file:
            if os.path.exists(os.path.join(new_dir, new_name)):
                new_name = "".join([choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890") for _ in range(5)]) + "_" + new_name
            os.rename(os.path.join(new_dir, text_file), os.path.join(new_dir, new_name))
            print(f"{Fore.GREEN}[+]{Fore.RESET} RENAMED {Fore.CYAN}{text_file}{Fore.RESET} TO {Fore.CYAN}{new_name}{Fore.RESET}")
        else:
            print(f"{Fore.YELLOW}[!]{Fore.RESET} DID NOT RENAME {Fore.CYAN}{text_file}{Fore.RESET}")


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
    signal(SIGINT, signal_handler)
    init()
    args = parse_arguments()

    if not (args.modify or args.rename):
        print(f"{Fore.RED}[X]{Fore.RESET} YOU NEED TO USE --modify AND/OR --rename MODIFIERS")
        exit(1)

    if not os.path.exists(args.directory):
        print(f"{Fore.RED}[X]{Fore.RESET} DIRECTORY NOT FOUND")
        exit(1)

    if not os.path.isdir(args.directory):
        print(f"{Fore.RED}[X]{Fore.RESET} {Fore.CYAN}{args.directory}{Fore.RESET} IS NOT A DIRECTORY")
        exit(1)

    new_dir = os.path.join(args.directory, "cleaned_files")
    filter_list = load_json(args.filter)
    text_files = [os.path.join(args.directory, item) for item in os.listdir(args.directory) if os.path.isfile(os.path.join(args.directory, item))]

    if not text_files:
        print(f"{Fore.RED}[X]{Fore.RESET} NO FILES IN DIRECTORY")
        exit(1)

    if os.path.exists(new_dir):
        rmtree(new_dir)
    os.makedirs(new_dir)

    for text_file in text_files:
        copy(text_file, new_dir)

    del text_files

    if args.modify:
        clean_files(filter_list, new_dir)

    if args.modify and args.rename:
        print(f"{Fore.MAGENTA}{'=' * os.get_terminal_size().columns}{Fore.RESET}")

    if args.rename:
        rename_files(filter_list, new_dir)


if __name__ == "__main__":
    main()
