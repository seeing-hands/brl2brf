# BRF and Unicode converter
# Note: This code used to be in the unicode.py module
# It was moved so that all the code in the unicode module is generic
from .unicode import UnicodeConverter

brf_table_chars = " A1B'K2L@CIF/MSP\"E3H9O6R^DJG>NTQ,*5<-U8V.%[$+X!&;:4\\0Z7(_?W]#Y)="
brf_table_bytes = b" A1B'K2L@CIF/MSP\"E3H9O6R^DJG>NTQ,*5<-U8V.%[$+X!&;:4\\0Z7(_?W]#Y)="


class unicode_to_brf (UnicodeConverter):
    name = "unicode_to_brf"
    source_format = "unicode"
    output_format = "brf"
    options = UnicodeConverter.input_options + [
        {
            "name": "eight_dot_characters",
            "description": "How should characters with dots 7 or 8 be handled?",
            "choices": [
                {
                    "name": "warn",
                    "description": "Warn about their presence and exclude them from the file",
                    "default": True
                },
                {
                    "name": "delete",
                    "description": "Remove them from the output"
                },
                {
                    "name": "bypass",
                    "description": "Place the Unicode characters into the file"
                },
                {
                    "name": "strip",
                    "description": "Strip out dots 7 and 8 and put the corresponding 6-dot character in the output"
                }
            ]
        }
    ]

    def __init__(self, generic_options=[], converter_options=[]):
        UnicodeConverter.__init__(self, generic_options, converter_options)
        self.eight_dot_behavior = converter_options.get("eight_dot_characters", "warn")

    def convert(self, unicode):
        """
        Convert a unicode-formatted string to BRF.

        Notes:
            Unicode braille uses the codepoints 0x2800 to 0x28ff with a little endian encoding of dots 1-8.
            BRF as understood by this script only supports 6-dot Braille.
            Unicode codepoints using dots 7 and 8 will trigger a warning.
            Other characters will be ignored.
        """
        brf = ""
        for c in self.unicode_decode(unicode):
            cn = ord(c)
            if cn < 0x2800 or cn >= 0x2900:
                brf += c
            elif cn >= 0x2840:
                if self.eight_dot_behavior == "warn":
                    self.warning("8_to_6_dot_conversion", f"The character {c} cannot be directly converted to BRF, which only supports 6 dot characters.")
                elif self.eight_dot_behavior == "delete":
                    continue
                elif self.eight_dot_behavior == "strip":
                    brf += brf_table_chars[(cn - 0x2800) % len(brf_table_chars)]
                elif self.eight_dot_behavior == "bypass":
                    brf += c
            else:
                brf += brf_table_chars[cn - 0x2800]
        return brf.encode(self.output_encoding)


class brf_to_unicode (UnicodeConverter):
    name = "brf_to_unicode"
    source_format = "brf"
    output_format = "unicode"
    options = UnicodeConverter.output_options

    def convert(self, brf):
        unicode = ""
        for c in brf:
            if c in brf_table_bytes:
                unicode += chr(0x2800 + brf_table_bytes.index(c))
            else:
                unicode += chr(c)
        return unicode.encode(self.output_encoding)

    def close(self):
        # The input buffer is not used. Skip unicode_converter version
        self.closed = True
        return b""
