# BRL2BRF: Convert between raw Braille file formats

## What is it?
This script can convert files between two formats which have both been used to store raw Braille data. These formats are usually known as .brl, or unformatted Braille files, and .brf, or formatted Braille files. The "formatted" label is a misnomer, as the BRF format does not contain any more structure than the other.

## What isn't it?
This is not a complex Braille converter. It cannot, for example, convert plain text to contracted Braille, nor even reflow a Braille file to different line lengths. This was only designed to perform a quick conversion from one raw file type to another. For more complex Braille conversion needs, we suggest that you use a program like [BrailleBlaster](https://brailleblaster.org/).

## Why is this useful
There are some devices which understand only one Braille format. This is true of some Braille displays that have a specific internal format and may also be true of any system whose software for handling Braille data has been written to only accept one encoding. If you give the wrong format to a system like this, it will likely ignore, replace, or crash on some characters.

## Installation
The script is written as a single Python script. You do not need to install any dependencies to use it. Simply download the `brl2brf.py` file and execute it with
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
I can't necessarily tell you. The easiest way to guess is to use the file extention. If you have a .brl file and it's not working for some reason, try converting it to .brf and see if that one works. If it doesn't, treat that file as if it was a .brf file and convert it to .brl, and see if that one works.

### I tried both formats and neither work
Having seen proprietary Braille systems, I know this will eventually happen and I won't be able to anticipate it. The bad news is that this script won't convert for you. The good news is that it can. All you have to do is to create a file that this system does recognize and accept and send it to me along with a description of the system that created it. I will investigate the format and add it to the converter.

## License
This script is licensed under the MIT license. This license should basically let you do as you wish with the software, but if you would like to do something under different terms, contact [Seeing Hands](https://www.seeinghands.org).

## Contacting the author
If you have a GitHub account, I encourage you to open an issue for any problems you encounter. If you don't have an account and don't want to make one, you can use the contact form on the [Seeing Hands website](https://www.seeinghands.org).