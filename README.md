# Usage
```console
usage: regex-filter.py [-h] [-r] directory filter

Replace matched strings with specified substitute

positional arguments:
  directory     path to a directory containing files to clean
  filter        path to a json file containing REGEX:WORD

options:
  -h, --help    show this help message and exit
  -r, --rename  use the json file to rename files
```

The json file should be in `REGEX:WORD` format where the keys are the regex and the values are the word to replace matches with

## Example
```json
{
	"(\\d{1,3}\\.){3}\\d{1,3}" : "x.x.x.x"
}
```

A new directory named `cleaned_files` will be created in the given directory containing the new files
