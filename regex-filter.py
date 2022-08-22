import os
from re import findall, sub, IGNORECASE
from colorama import Fore, init
from json import load, JSONDecodeError
from argparse import ArgumentParser
from sys import exit
from charset_normalizer import from_bytes

# colorama setup
init()
cyan = Fore.CYAN
yellow = Fore.YELLOW
green = Fore.GREEN
red = Fore.RED
magenta = Fore.MAGENTA
reset = Fore.RESET

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

# load the file and detect the encoding using charset_normalizer's from_bytes()
def read_file(file_path):
    with open(file_path, "rb") as f:
        bytes_data = f.read()
    enc_type = from_bytes(bytes_data).best().encoding
    text = bytes_data.decode(enc_type)
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
            if len(findall(regex, new_name, flags=IGNORECASE)) > 0:
                new_name = sub(regex, substitute, new_name)
                changed = True
        
        # print the result to the user
        if changed:
            try:
                os.rename(f"{new_dir}/{text_file}", f"{new_dir}/{new_name}")
                print(f"{green}[+]{reset} RENAMED {cyan}{text_file}{reset} TO {cyan}{new_name}{reset}")
            except FileExistsError:
                print(f"{red}[X]{reset} CANNOT RENAME {cyan}{text_file}{reset} NEW NAME {cyan}{new_name}{reset} ALREADY EXISTS")
        else:
            print(f"{yellow}[!]{reset} DID NOT RENAME {cyan}{text_file}{reset}")

def parse_arguments():
    parser = ArgumentParser(description="Replace matched strings with specified substitute")
    parser.add_argument("directory", type=str, help="path to a directory containing files to clean")
    parser.add_argument("filter", type=str, help="path to a json file containing REGEX:WORD")
    parser.add_argument("-r", "--rename", action="store_true", help="use the json file to rename files")
    return parser.parse_args()

def main():

    # parsed arguments from user
    args = parse_arguments() 

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
    os.makedirs(new_dir, exist_ok=True)

    # main functionality of the program
    clean_files(text_files, filter_list, new_dir)

    # if -r or --rename arguments is passed, rename the files in new_dir
    if args.rename:
        print(f"{magenta}=============================={reset}")
        rename_files(filter_list, new_dir)

if __name__ == "__main__":
	main()
