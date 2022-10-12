## Installation
1. Clone the repository `git clone https://github.com/illbison/regex-filter` or download as [zip](https://github.com/illbison/regex-filter/archive/refs/heads/main.zip)
2. Install dependencies `pip install -r requirements.txt`
3. Run with `python regex_filter.py ...`

## Usage
```console
usage: regex_filter.py -i INPUT [INPUT ...] -f FILTER -o OUTPUT [-m] [-r] [-h]

Replace matched strings in file content and file names with specified substitute using regular expressions

required:
  -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                        path to files or directories containing files
  -f FILTER, --filter FILTER
                        path to a json file in REGEX:WORD format
  -o OUTPUT, --output OUTPUT
                        path to output directory

modifiers:
  -m, --modify          use filter to modify content of files
  -r, --rename          use filter to rename files

optional:
  -h, --help            show this help message and exit
```

The json file must be in `REGEX:WORD` format where the keys are the regex and the values are the replacement. See [example](example.json)

A new directory named `REGEX_FILTER` will be created in the given output directory containing the cleaned input
