# BRL2BRF: Convert between raw Braille file formats

## What is it?
This script can convert files among multiple formats (5 currently supported) which have been used to store raw Braille data. These formats are usually generated or read by devices or software that handle Braille documents, but a lack of standardization through history means that one program might generate a file that another one can't read. This tool is an attempt to bridge the gap and allow people to use a Braille file anywhere, no matter where it came from.

## What isn't it?
This is not a complex Braille converter. It cannot, for example, convert plain text to contracted Braille. This was only designed to perform a quick conversion from one raw file type to another. For more complex Braille conversion needs, we suggest that you use a program like [BrailleBlaster](https://brailleblaster.org/).

## Why is this useful
There are some devices which understand only one Braille format. This is true of some Braille displays that have a specific internal format and may also be true of any system whose software for handling Braille data has been written to only accept one encoding. If you give the wrong format to a system like this, it will likely ignore, replace, or crash on some characters.

## Installation
Obtain the code by cloning this repository or downloading one of the releases
```
python3 brl2brf.py
```

## Usage examples:
### Get full usage and documentation of all parameters
```
python3 brl2brf.py --help
```

### Convert a file from BRL format to BRF
```
python3 brl2brf.py -f myfile.brl -w myfile.brf
```

### Convert a file from BRF format to BRL
```
python3 brl2brf.py -f myfile.brf -w myfile.brl
```

### Convert a BRL file sent to standard input and print the BRF contents to standard output
```
python3 brl2brf.py -i -o -sf brl
```

### Convert a file from BRF format to Helptech format, still using a .brl extention
```
python3 brl2brf.py -f myfile.brf -w myfile.brl -of helptech
```

### Convert all the files with a .brl extention in the folder "books" to BRF files in the same folder
```
python3 brl2brf.py -d books -p *.brl -np books/*.brf
```

### Convert all the files with a .brl extention in the folder "books" to BRF files in a new folder called "converted_books"
```
python3 brl2brf.py -d books -p *.brl -np converted_books/*.brf
```

### Convert all the files with a .brl extention in the folder "books" to BRF files in a new folder called "converted_books", including all subdirectories
```
python3 brl2brf.py -d books -p *.brl -np converted_books/*.brf -r
```

## Frequently asked questions
### Which format do I have, and which one do I need
I can't necessarily tell you. The most reliable way to guess the format is to know what format your system supports. Here is a short list of known formats:
* HelpTech/HandyTech displays: helptech format
* Hims displays: BRL format
* Humanware displays: BRF format
If your device isn't listed or you don't know the source of the file, the easiest way to guess is to use the file extention, which the program will do automatically. If this isn't generating usable results, try a different set of formats.

### I tried all formats and none work
Having seen proprietary Braille systems, I know this will eventually happen and I won't be able to anticipate it. The bad news is that this script won't convert for you. The good news is that it can. All you have to do is to create a file that this system does recognize and accept and send it to me along with a description of the system that created it. I will investigate the format and add it to the converter. I have done this with some formats before, and I'd be happy to add yours to the list.

## License
This script is licensed under the MIT license. This license should basically let you do as you wish with the software, but if you would like to do something under different terms, contact [Seeing Hands](https://www.seeinghands.org).

## Contacting the author
If you have a GitHub account, I encourage you to open an issue for any problems you encounter. If you don't have an account and don't want to make one, you can use the contact form on the [Seeing Hands website](https://www.seeinghands.org).