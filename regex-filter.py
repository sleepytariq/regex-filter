import os
from re import findall, sub, IGNORECASE
from colorama import Fore, init
from json import load, JSONDecodeError
from argparse import ArgumentParser
from sys import exit
from charset_normalizer import from_path

# colorama setup
init()
cyan = Fore.CYAN
yellow = Fore.YELLOW
green = Fore.GREEN
red = Fore.RED
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

def read_file(file_path):
    # load the file using charset_normalizer's from_path()
    bin_file = from_path(file_path).best()
    text = str(bin_file)
    enc_type = bin_file.encoding
    return (text, enc_type)

def parse_arguments():
    parser = ArgumentParser(description="Replace matched strings with specified substitute")
    parser.add_argument("directory", type=str, help="Path to a directory containing files to filter")
    parser.add_argument("filter", type=str, help="Path to a json file containing REGEX:WORD")
    return parser.parse_args()

def main():

    # parsed arguments from user
    args = parse_arguments()

    # check if directory exists
    if not os.path.exists(args.directory):
        print(f"{red}[X]{reset} DIRECTORY NOT FOUND")
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

        # loop through the filter_list and remove the regex matches with the substitute word
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

if __name__ == "__main__":
	main()
