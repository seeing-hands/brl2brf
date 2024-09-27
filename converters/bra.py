# Convert between BRA and Unicode Braille formats
# Note: BRA, along with BAN, is a raw Braille format most common in Iberian countries
# I don't know why they have this, but it is still in active use as of 2024 and some displays support it natively
# BRA appears to support only 6-dot, not 8-dot characters
# Note: This format was reverse-engineered. If you are aware of a specification for this format, please alert us at brl2brf@seeinghands.org

from .unicode import UnicodeConverter

# Note: Null character (\0) is used to indicate an unknown character which did not appear in samples. This may be removed later.
bra_table_bytes = b" a,b.k;l\x00cif/msp\x00e:h\x00o+r\x00djg|ntq\x00\x00?2-u<v{\x00\x00\x000x$\x00\x00\x00\x008\x00z\x00(\x00\x00w7#y)\x00"


class unicode_to_bra (UnicodeConverter):
    name = "unicode_to_bra"
    source_format = "unicode"
    output_format = "bra"
    options = UnicodeConverter.input_options

    def convert(self, unicode):
        bra = b""
        for c in self.unicode_decode(unicode):
            cn = ord(c)
            if cn < 256:
                # characters in one-byte range are emitted directly into the file
                bra += bytes([cn])
            elif cn < 0x2800 or cn >= 0x2900:
                self.warning("character_out_of_range", f"The character {c} cannot be directly converted to bra format.")
            elif cn >= 0x2840:
                self.warning("character_out_of_range", f"The character {c} requires 8-dot Braille and cannot be directly converted to bra format.")
            else:
                bra_char = bra_table_bytes[cn - 0x2800]
                if bra_char == 0:
                    self.warning("character_unsupported", f"The character {c} is currently unknown and cannot be directly converted to bra format.")
                    bra += b" "
                else:
                    bra += bytes([bra_char])
        return bra


class bra_to_unicode (UnicodeConverter):
    name = "bra_to_unicode"
    source_format = "bra"
    output_format = "unicode"
    options = UnicodeConverter.output_options

    def convert(self, bra):
        unicode = ""
        for c in bra:
            if c == ord(b"\0"):
                # used to pad the table string, not a real character. Warning and emit directly
                self.warning("unexpected_character", f"The null character is not expected in this file.")
                unicode += chr(c)
            elif c in [ord(b"\t"), ord(b"\n"), ord(b"\r")]:
                # Whitespace transferred directly
                unicode += chr(c)
            elif c in bra_table_bytes:
                unicode += chr(0x2800 + bra_table_bytes.index(c))
            else:
                self.warning("unexpected_character", f"The character {c} is not expected in this file.")
                unicode += chr(c)
        return unicode.encode(self.output_encoding)

    def close(self):
        # The input buffer is not used. Skip unicode_converter version
        self.closed = True
        return b""
