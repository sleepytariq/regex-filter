# Usage
```console
usage: regex-filter.py -d DIRECTORY -f FILTER [-m] [-r] [-h]

Replace matched strings with specified substitute

required:
  -d DIRECTORY, --directory DIRECTORY
                        path to a directory containing files to clean
  -f FILTER, --filter FILTER
                        path to a json file containing REGEX:WORD

modifiers:
  -m, --modify          use the filter to modify content of files
  -r, --rename          use the filter to rename files

optional:
  -h, --help            show this help message and exit
```

The json file should be in `REGEX:WORD` format where the keys are the regex and the values are the word to replace matches with

## Example
```json
{
	"(\\d{1,3}\\.){3}\\d{1,3}" : "x.x.x.x"
}
```

A new directory named `cleaned_files` will be created in the given directory containing the new files
