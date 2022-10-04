# Usage
```console
usage: regex-filter.py -i INPUT [INPUT ...] -f FILTER -o OUTPUT [-m] [-r] [-h]

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

The json file must be in `REGEX:WORD` format where the keys are the regex and the values are the replacement

## Example
```json
{
	"(\\d{1,3}\\.){3}\\d{1,3}" : "x.x.x.x"
}
```

A new directory named `REGEX_FILTER` will be created in the given output directory containing the cleaned input
