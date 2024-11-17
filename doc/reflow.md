# BRL2BRF: Reflow
This converter can be used to reflow a Braille file to a specific line length.

## Why is that useful?
Reflowing a file is useful when trying to fit the content into a specific size of window. With the most common single line Braille displays, this is often not an issue because displays can wrap words onto different lines when necessary and have options to ignore blank spaces. There are some other situations where proper line placement is important, including these:
* When embossing a file onto paper, having lines that are too long will likely result in some of it being cut off.
* Having lines that are too short will waste paper on useless margins.
* Some displays, especially multiline displays, do not automatically reflow files and require that they presented as they would if embossed. Notably, this includes the Canute 360 from [Bristol Braille](https://www.bristolbraille.org).
* If a file has already been reflowed for shorter lines, some single-line displays will try to display it like that, leaving extra gaps on the side. This converter can remove these line breaks and make it more natural to read.

## Limitations
Reflowing a file is possible in a number of products. This converter is intended for quick or automated conversions, and therefore it only has a few options. Here are some of the options it doesn't have:
* Page numbers: It neither creates, removes, nor relocates page numbers. This operates on raw Braille data.
* Margins: It does not simulate margins. You can reflow a file to a size appropriate for a page including margins, then emboss it with those margins. For example, if you are printing onto US letter-sized paper which can hold 34-character lines, you can reflow for 32 characters to have a one-cell margin as long as you emboss it with that set in whatever software you use to interface with your embosser.

## Usage
To indicate that you want to use the reflow capability, specify the options "-c reflow" on the command line. You should then select options to configure what kind of reflow you would like. Those options include the following:

### line_length
Set this to the number of characters in your line.

### word_wrap
This has the following options:
* wrap (default): Moves words onto the next line if they will overflow
* split: Splits the word across lines with an interleaving string (a hyphen, dots 3-6, by default, but configurable with the split_character option)
* cut: Splits the word without notification

### split_character
If a word has to be split across lines, either because you requested it or because it is too long to fit, what characters should indicate this. Defaults to a hyphen (dots 3-6). This must be a string of Unicode Braille characters.

### linebreaks
How to handle explicit line breaks in the source material
* strict: All line breaks are retained. This will not allow a file to be reflowed to a longer line length than it started.
* double (default): Two or more line breaks are retained, whereas single line breaks are replaced by spaces for reflowing.
* remove: All line breaks are replaced by spaces.

## Examples
### Reflowing a file so it fits on a piece of paper
If you want to print a file with no line lengths and print it on a piece of paper, do the following:
* Figure out how long your lines should be. As an example, if using US letter-sized paper, that would be 34 characters per line with no margins or 32 characters per line with a typical one-cell margin to either side
* Run BRL2BRF with the following options:
```
-c reflow -co reflow.line_length=34
```

### Reflowing a file to fit on a Canute 360
This is basically the same as the above example about paper. Just set the line length to 40:
```
-c reflow -co reflow.line_length=40
```
Note that the Canute uses BRF files, so if you are using this, make sure you set your output format to BRF.

