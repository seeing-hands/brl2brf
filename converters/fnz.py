# Converter between FNZ and Unicode format
from .unicode import UnicodeConverter
from .converter import ConverterError
import re


class unicode_to_fnz (UnicodeConverter):
    name = "unicode_to_fnz"
    source_format = "unicode"
    output_format = "fnz"
    options = UnicodeConverter.input_options

    def __init__(self, generic_options, converter_options):
        UnicodeConverter.__init__(self, generic_options=generic_options, converter_options=converter_options)
        self.produced_header = False

    def header(self):
        # Note: This must appear at the top of any FNZ file
        # It stores the cursor position, but since anything being converted won't track that, it is hard-coded to the top
        self.produced_header = True
        return "x= 0\ny= 0\n"

    def convert(self, data):
        r = ""
        for c in self.unicode_decode(data):
            if c == "\r":
                # CR characters are stripped, only newlines are used for line breaks
                continue
            elif c == "\n":
                r += "\n"
            elif c in " \t":
                # Whitespace is stored as space characters
                r += " 0"
            elif ord(c) >= 0x2800 and ord(c) < 0x2900:
                cv = ord(c) - 0x2800
                r += f" {cv}"
            else:
                self.warning("untranslatable_character", f"The character {c} cannot be converted to FNZ format")
        if not self.produced_header:
            r = self.header() + r
        return r.encode("UTF-8")

    def close(self):
        if not self.produced_header:
            return self.header().encode("UTF-8")
        return b""


class fnz_to_unicode (UnicodeConverter):
    name = "fnz_to_unicode"
    source_format = "fnz"
    output_format = "unicode"
    options = UnicodeConverter.output_options

    def __init__(self, generic_options, converter_options):
        UnicodeConverter.__init__(self, generic_options=generic_options, converter_options=converter_options)
        self.awaiting_header_lines = 2

    @staticmethod
    def split_after(s, delimiter):
        i = 0
        while True:
            try:
                j = s.index(delimiter, i) + len(delimiter)
            except ValueError:
                break
            yield s[i:j]
            i = j + 1
        yield s[i:]

    def convert(self, fnz):
        if fnz == b"":
            return b""
        r = ""
        lines = self.split_after(fnz, b"\n")
        for line in lines:
            if self.awaiting_header_lines == 2:
                if re.match(b"^x= [0-9]*$", line.strip()):
                    self.awaiting_header_lines -= 1
                    continue
                elif line == b"":
                    continue
                else:
                    raise ConverterError(f"Looking for X coordinate line from FNZ header, but found {line.strip()}")
            if self.awaiting_header_lines == 1:
                if re.match(b"^y= [0-9]*$", line.strip()):
                    self.awaiting_header_lines -= 1
                    continue
                elif line == b"":
                    continue
                else:
                    raise ConverterError(f"Looking for Y coordinate line from FNZ header, but found {line.strip()}")

            chars = line.strip().split(b" ")
            for cn in chars:
                if cn == b"":
                    continue
                try:
                    n = int(cn.decode("UTF-8"))
                except ValueError:
                    raise ConverterError(f"Cannot parse \"{cn}\" as an integer while decoding FNZ")
                if n > 255:
                    self.warning("unexpected_character", f"The value {n} is too high for FNZ and has been skipped")
                r += chr(0x2800 + n)
            if line.endswith(b"\n"):
                r += "\n"
                print("Adding a newline")
        return r.encode(self.output_encoding)
