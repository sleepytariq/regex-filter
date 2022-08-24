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

# setup colorama
init()
cyan = Fore.CYAN
yellow = Fore.YELLOW
green = Fore.GREEN
red = Fore.RED
magenta = Fore.MAGENTA
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


def generate_random_string():
    s = ""
    for _ in range(5):
        s += choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
    return s + "_"


# load the file using the encoding detected by charset_normalizer's from_path()
def read_file(file_path):
    enc_type = from_path(file_path).best().encoding
    with open(file_path, "r", encoding=enc_type) as f:
        text = f.read()
    return (text, enc_type)


def clean_files(text_files, filter_list, new_dir):
    # loop and clean text files
    for text_file in text_files:

        # keep count of regex matches
        count = 0

        # prepare filename
        filename = f"{cyan}{os.path.basename(text_file)}{reset}"

        # read text_file and get expand the text and enc_type tuple
        try:
            text, enc_type = read_file(text_file)
        except Exception:
            print(f"{red}[X]{reset} FAILED TO READ {filename}")
            copy(text_file, new_dir)
            continue

        # loop through the filter_list and replace the regex matches with the substitute word
        # increment the count variable by the number of matches for each regex
        for regex, substitute in filter_list.items():
            count += len(findall(regex, text, flags=IGNORECASE))
            text = sub(regex, substitute, text, flags=IGNORECASE)

        # write the new text to a new file under the new_dir directory
        with open(f"{new_dir}/{os.path.basename(text_file)}", "w", encoding=enc_type) as f:
            f.write(text)

        # print the result to the user
        if count > 0:
            print(f"{green}[+]{reset} CHANGED {cyan}{count}{reset} MATCHES FROM {filename}")
        else:
            print(f"{yellow}[!]{reset} NO CHANGES FROM {filename}")


def rename_files(filter_list, new_dir):
    # loop through each file in the new_dir
    for text_file in os.listdir(new_dir):
        changed = False
        new_name = text_file

        # loop through the filter_list and replace the regex matches with the substitute word
        for regex, substitute in filter_list.items():
            new_name = sub(regex, substitute, new_name)

        # print the result to the user
        if new_name != text_file:
            if os.path.exists(f"{new_dir}/{new_name}"):
                new_name = generate_random_string() + new_name
            os.rename(f"{new_dir}/{text_file}", f"{new_dir}/{new_name}")
            print(f"{green}[+]{reset} RENAMED {cyan}{text_file}{reset} TO {cyan}{new_name}{reset}")
        else:
            print(f"{yellow}[!]{reset} DID NOT RENAME {cyan}{text_file}{reset}")


def parse_arguments():

    # create the ArgumentParser object without the help argument
    parser = ArgumentParser(description="Replace matched strings in file names or file content with specified substitute using regular expressions", add_help=False)

    # create the arguments groups
    required = parser.add_argument_group("required")
    modifiers = parser.add_argument_group("modifiers")
    optional = parser.add_argument_group("optional")

    # add the following arguments and readd the help argument
    required.add_argument("-d", "--directory", type=str, help="path to a directory containing files", required=True)
    required.add_argument("-f", "--filter", type=str, help="path to a json file in REGEX:WORD format", required=True)
    modifiers.add_argument("-m", "--modify", action="store_true", help="use the filter to modify content of files")
    modifiers.add_argument("-r", "--rename", action="store_true", help="use the filter to rename files")
    optional.add_argument("-h", "--help", action="help", help="show this help message and exit")

    return parser.parse_args()


def main():

    # setup signal handler to handle ctrl + c
    signal(SIGINT, signal_handler)

    # parsed arguments from user
    args = parse_arguments()

    if (args.modify or args.rename) == False:
        print(f"{red}[X]{reset} YOU NEED TO USE --modify AND/OR --rename MODIFIERS")
        exit(1)

    # check if directory exists
    if not os.path.exists(args.directory):
        print(f"{red}[X]{reset} DIRECTORY NOT FOUND")
        exit(1)

    # check if it is a directory
    if not os.path.isdir(args.directory):
        print(f"{red}[X]{reset} {cyan}{args.directory}{reset} IS NOT A DIRECTORY")
        exit(1)

    # init variables from input
    new_dir = f"{args.directory}/cleaned_files"
    filter_list = load_json(args.filter)
    text_files = [f"{args.directory}/{item}" for item in os.listdir(args.directory) if os.path.isfile(f"{args.directory}/{item}")]

    # check if directory contains files
    if not text_files:
        print(f"{red}[X]{reset} NO FILES IN DIRECTORY")
        exit(1)

    # create the new directory to save the new cleaned files
    if os.path.exists(new_dir):
        rmtree(new_dir)
    os.makedirs(new_dir)

    # if both -m and -r arguments are passed
    if args.modify and args.rename:
        clean_files(text_files, filter_list, new_dir)
        print(f"{magenta}{'-' * os.get_terminal_size().columns}{reset}")
        rename_files(filter_list, new_dir)
        exit(0)

    # if only -m argument is passed
    if args.modify:
        clean_files(text_files, filter_list, new_dir)
        exit(0)

    # if only -r argument is passed
    if args.rename:
        for text_files in text_files:
            copy(text_files, new_dir)
        rename_files(filter_list, new_dir)
        exit(0)


if __name__ == "__main__":
    main()
