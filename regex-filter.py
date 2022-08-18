import os
import re
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
	"""
	This function will try to load the passed json file and return a dictionary
	A JSONDecodeError exception will be caught upon failure
	"""
	try:
		with open(json_file, "r") as jf:
			arr = load(jf)
	except JSONDecodeError:
		print(f"{red}[X]{reset} FAILED TO LOAD JSON FILE")
		exit(1)
	return arr

def parse_arguments():
    parser = ArgumentParser(description="Replace matched strings with specified substitute")
    parser.add_argument("directory", type=str, help="Path to a directory containing files to filter")
    parser.add_argument("filter", type=str, help="Path to a json file containing REGEX:WORD")
    return parser.parse_args()

def main():
    args = parse_arguments()
    new_dir = f"{args.directory}/cleaned_files"
    filter_list = load_json(args.filter)
    text_files = [f"{args.directory}/{item}" for item in os.listdir(args.directory) if os.path.isfile(f"{args.directory}/{item}")]
    os.makedirs(f"{new_dir}", exist_ok=True)
    for text_file in text_files:

        # keep count of regex matches
        count = 0

        # prepare filename
        filename = f"{cyan}{os.path.basename(text_file)}{reset}"
        
        # load the file using charset_normalizer's from_path()
        try:
            enc_type = from_path(text_file).best().encoding
            with open(text_file, "r", encoding=enc_type) as f:
                text = f.read()
        except Exception:
            print(f"{red}[X]{reset} FAILED TO READ {filename}")
            continue

        # loop through the filter_list and remove the regex matches with the substitute word
        # increment the count variable by the number of matches for each regex
        for regex, substitute in filter_list.items():
            count += len(re.findall(regex, text, flags=re.IGNORECASE))
            text = re.sub(regex, substitute, text, flags=re.IGNORECASE)

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
