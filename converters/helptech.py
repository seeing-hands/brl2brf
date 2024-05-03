# Convert between Helptech and Unicode Braille formats
from .unicode import UnicodeConverter

ht_table_bytes = b" a1b'k2l`cif/msp\"e3h9o6r~djg>ntq,*5<-u8v.%{$+x!&;:4|0z7(\x7f?w}#y)=\x00A\xc1B\xfaK\xb3L@CIF\xf4MSP\xd0E\xdaH\xe4O\x9eR^DJG\x92NTQ\xc4\xcf\xc7\xdc\xadU\xc3V\x9c\xfb[\xc5\xd1X\xed\x80\x8e\xf5\xa5\\\xd8Z\xc9\xb9_\xa9W]\x8fY\xdf\xfe\x00\xe0\xd2\xfd\xa8\xc2\x90\xd3\xf9\xb8\xd4\xcc\x8d\xe6\xe5\xe3\x9b\xee\xe2\xa6\x99\xd6\xe8\xd7\xf2\xeb\xa7\xbb\x84\xa4\xe7\xcb\xc6\xa0\xb5\x82\xb7\xac\x9a\xab\x9d\xa1\x94\x89\x95\xfc\x8a\xd5\xf3\xa3\xe9\x81\xea\xb4\xf0\x85\xf8\xa2\xb6\x8b\xe1\x98\x97\xba\xb0\x01\xbf\x02\xc0\x0b\xc8\x0c\x00\x03\x00\x06\xf6\x00\x13\x10\xef\x05\xcd\x08\xf7\x0f\xf1\x12\x1e\x04\n\x07\x91\x0e\x14\x11\xd9\x83\xbc\x88\xb1\x15\xdd\x16\xbd\x8c\x1b\x9f\xbe\x18\xec\x87\xce\x96\xaa\x1c\xde\x1a\xb2\xae\x1f\x93\x17\x1d\x86\x19\xaf\xdb"
unencodable_chars = {
    "\u2840": "dot 7",
    "\u2880": "dot 8",
    "\u28c8": "dots 4-7-8",
    "\u28ca": "dots 2-4-7-8",
    "\u28cd": "dots 1-3-4-7-8"
}


class helptech_to_unicode (UnicodeConverter):
    name = "helptech_to_unicode"
    source_format = "helptech"
    output_format = "unicode"
    options = UnicodeConverter.output_options

    def convert(self, ht):
        """
        Convert a helptech-formatted string to BRF.

        Notes:
            The input file format typically has a .brl extention, but is not known to be standardized.
            The devices that provide the canonical samples were from HelpTech.
            Specifically, the ActiveBraille Braille displays generate these files.
            This format is almost the same Braille subset that Hims devices generate, but not quite the same.
            Warning: This converter exports to Unicode to support 8-dot Braille, but the BRF converter only supports 6-dot Braille.
            If you convert an 8-dot Helptech file to BRF, dots 7 and 8 data will be handled by the unicode_to_brf converter options.
        """


class unicode_to_helptech (UnicodeConverter):
    name = "unicode_to_helptech"
    source_format = "unicode"
    output_format = "helptech"
    options = UnicodeConverter.input_options

    def convert(self, unicode):
        ht = b""
        for c in self.unicode_decode(unicode):
            cn = ord(c)
            if cn < 256:
                # characters in one-byte range are emitted directly into the file
                ht += bytes([cn])
            elif cn < 0x2800 or cn >= 0x2900:
                self.warning("character_out_of_range", f"The character {c} cannot be directly converted to HelpTech format.")
            elif c in unencodable_chars.keys():
                self.warning("character_unsupported", f"The character {unencodable_chars[c]} cannot be directly converted to HelpTech format.")
                ht += b" "
            else:
                ht += bytes([ht_table_bytes[cn - 0x2800]])
        return ht


class helptech_to_unicode (UnicodeConverter):
    name = "helptech_to_unicode"
    source_format = "helptech"
    output_format = "unicode"
    options = UnicodeConverter.output_options

    def convert(self, ht):
        unicode = ""
        # Remove \n characters from true line breaks because they're also used for 2-4-5-7-8 pattern
        data = ht.replace(b"\r\n", b"\r")
        for c in ht:
            if c == ord(b"\0"):
                # used to pad the table string, not a real character. Warning and emit directly
                self.warning("unexpected_character", f"The character {c} is not expected in this file.")
                unicode += chr(c)
            elif c == ord(b"\t"):
                # Whitespace transferred directly
                unicode += chr(c)
            elif c == ord(b"\r"):
                # Indicates line break
                unicode += "\r\n"
            elif c in ht_table_bytes:
                unicode += chr(0x2800 + ht_table_bytes.index(c))
            else:
                self.warning("unexpected_character", f"The character {c} is not expected in this file.")
                unicode += chr(c)
        return unicode.encode(self.output_encoding)

    def close(self):
        # The input buffer is not used. Skip unicode_converter version
        self.closed = True
        return b""
