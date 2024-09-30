# BRL2BRF: BRA and BAN formats
The BRA and BAN Braille file types are somewhat unusual. This file will list some information about these files. A lot of this will only be of interest to developers or those interested in the details of the format.

## Notes for users

## Notes for developers
### How the format can be studied
The Braille software [EBrai](https://cti.once.es/repos/ebrai64/EBrai64Setup.exe) from the organization [ONCE](https://once.es) can generate both types of files. This was used to determine the structure of the formats and to build the converter.
You can study the formats by using the same software. Some notes are useful:
* The software is only available in Spanish.
* In order to use it, your computer must have a Spanish language pack installed and a Spanish keyboard layout.

### How the formats are rendered
Rendering for these file types is inconsistent. Some displays do not support them at all. Some displays render them as raw Braille files, essentially what we're going for. Some ones convert them to text and then translate that text. Humanware Brailliant and related displays are examples of this latter case, and in this case, it appears that only Spanish text is reliably back-translated before display. This means that, although some of the raw characters may be supported by the format, not every display is guaranteed to open them correctly.

### What is in the formats
The formats are known as BRA (Braille ASCII) and BAN (Braille ANSI). You're right, that doesn't make any sense. They both represent eight-dot Braille using one byte per character, meaning that neither is limited to 7-bit ASCII characters like BRF and BRL are. As with the other known character set, that brings several downsides:
Whitespace characters like tab, new line, and carridge return are also used to represent Braille patterns. This limits what the formats can be used for. In our converter, we consider any \r\n characters to be a new line (Unix line breaks are not allowed) and any \r or \n on its own to represent a Braille pattern. That will mostly work, but it does mean that you can't put those specific Braille patterns in the file because they will be treated as a new line.
For six-dot Braille, this is not an issue. Both formats can represent six-dot Braille without ambiguity.
For eight-dot Braille, the BAN format is strongly preferred. In BAN, every byte from 0 to 255 represents a different eight-dot pattern, as is required to fit them all. In BRA, there are some duplicates. I don't know why. This means that it is not possible to distinguish between several pairs of characters during translation to or from BRA. Those pairs are as follows:
* Byte 193 (\xc1) gives both ⢑ (1-5-8) and ⣁ (1-7-8)
* Byte 202 (\xca) gives both ⣆ (2-3-7-8) and ⣊ (2-4-7-8)
* Byte 209 (\xd1) gives both ⢗ (1-2-3-5-8) and ⣑ (1-5-7-8)
* Byte 213 (\xd5) gives both ⢸ (1-2-3-8) and ⣕ (1-3-5-7-8)
* Byte 229 (\xe5) gives both ⣒ (2-5-7-8) and ⣥ (1-3-6-7-8)
* Byte 247 (\xf7) gives both ⡨ (4-6-7) and ⣷ (1-2-3-5-6-7-8)
* Byte 254 (\xfe) gives both ⣨ (4-6-7-8) and ⣾ (2-3-4-5-6-7-8)
* Bytes 1, 5, 9, 15, 21, 27, and 29 don't do anything
In our BRA translator, the first option is always selected. There is no better hueristic that doesn't rely on lots of knowledge about the source material.
