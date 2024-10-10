# Converter to and from Unicode Braille characters in UTF-8
from .converter import converter, ConverterError


class UnicodeConverterError(ConverterError):
    """
    A subclass of converter error that deals specifically with Unicode encoding or decoding problems.
    """
    def __init__(self, message, chain=[]):
        """
        The message parameter is the expected string explaining what went wrong.
        The chain parameter can contain other exceptions to provide detail. Usually, these are instances of UnicodeDecodeError.
        """
        self.chain = chain


class UnicodeConverter(converter):
    """
    Useful utilities for converters using Unicode Braille.
    This class provides generic utilities for importing and exporting Unicode Braille data.
    It does not, in itself, implement a format converter.
    """
    input_options = [
        {
            "name": "input_encoding",
            "description": "The Unicode encoding to use to decode files.",
            "choices": [
                {
                    "name": "auto",
                    "description": "Automatically determine the encoding among the available options.",
                    "default": True
                },
                {
                    "name": "UTF-8",
                    "default": False
                },
                {
                    "name": "UTF-16",
                    "default": False
                },
                {
                    "name": "UTF-32",
                    "default": False
                }
            ]
        }
    ]

    output_options = [
        {
            "name": "output_encoding",
            "description": "The Unicode encoding to use in created files.",
            "choices": [
                {
                    "name": "UTF-8",
                    "default": True
                },
                {
                    "name": "UTF-16",
                    "default": False
                },
                {
                    "name": "UTF-32",
                    "default": False
                }
            ]
        }
    ]

    def __init__(self, generic_options={}, converter_options={}):
        converter.__init__(self, generic_options=generic_options, converter_options=converter_options)
        input_encoding = converter_options.get("input_encoding", "auto")
        self.auto_encoding = (input_encoding == "auto")
        self.input_encoding = input_encoding if input_encoding != "auto" else None
        self.output_encoding = converter_options.get("output_encoding", "UTF-8")

    def close(self):
        """
        The default close function calls convert to clear out any unprocessed Unicode data
        If the child class uses other logic, this should be overridden.
        """
        data = self.input_buffer
        self.input_buffer = b""
        output = self.convert(data)
        self.closed = True
        return output

    def unicode_decode(self, data):
        if data == b"":
            return ""
        if self.input_encoding:
            all_data = self.input_buffer + data
            try:
                unicode_data = all_data.decode(encoding=self.input_encoding)
                self.input_buffer = b""
                return unicode_data
            except UnicodeDecodeError as ude:
                if ude.reason == "unexpected end of data" or ude.reason == "truncated data":
                    if ude.start > 0:
                        truncated_data = all_data[0:ude.start]
                        try:
                            truncated_unicode_data = self.unicode_decode(truncated_data)
                            self.input_buffer = all_data[ude.start:]
                            return truncated_unicode_data
                        except UnicodeDecodeError as ude_second:
                            raise UnicodeConverterError("Unicode decoding is consistently failing", [ude_second, ude])

        elif self.auto_encoding:
            # Guess the encoding
            # Note: The encoding is guessed from the first chunk, then frozen
            self.input_encoding = self.guess_encoding_of(data, self.count_unicode_braille_chars)
            return self.unicode_decode(data)
        else:
            raise ConverterError("The input encoding is not set.")

    @staticmethod
    def count_unicode_braille_chars(data):
        """
        For use in encoding guessing.
        Returns the number of characters in a string between unicode 0x2800 and 0x2900
        """
        r = 0
        for c in data:
            cn = ord(c)
            if cn >= 0x2800 and cn < 0x2900:
                r += 1
        return r

    @staticmethod
    def guess_encoding_of(data, content_prediction_function):
        candidates = []
        for encoding in ["UTF-8", "UTF-16", "UTF-32"]:
            try:
                text = data.decode(encoding=encoding)
                candidates.append((encoding, text, None))
            except UnicodeDecodeError as ude:
                if ude.reason == "unexpected end of data" or ude.reason == "truncated data":
                    try:
                        text = data[0:ude.start].decode(encoding=encoding)
                        candidates.append((encoding, text, None))
                    except UnicodeDecodeError as ude:
                        candidates.append((encoding, "", ude))
                else:
                    candidates.append((encoding, "", ude))
        options = [c[0] for c in candidates if c[2] is None]
        if len(options) == 1:
            return options[0]
        elif len(options) == 0:
            raise ConverterError("Could not find a valid encoding")
        else:
            return max(candidates, key=(lambda x: content_prediction_function(x[1])))[0]


# Generic converter for 8-dot single-byte Braille formats


class unicode_to_generic8dot (UnicodeConverter):
    source_format = "unicode"
    options = UnicodeConverter.input_options

    def convert(self, unicode):
        output = b""
        for c in self.unicode_decode(unicode):
            cn = ord(c)
            if cn < 256:
                # characters in one-byte range are emitted directly into the file
                output += bytes([cn])
            elif cn < 0x2800 or cn >= 0x2900:
                self.warning("character_out_of_range", f"The character {c} cannot be directly converted to {self.output_format} format.")
            elif c in self.unencodable_chars.keys():
                self.warning("character_unsupported", f"The character {unencodable_chars[c]} cannot be directly converted to {self.output_format} format.")
                output += b" "
            else:
                output += bytes([self.table_bytes[cn - 0x2800]])
        return output


class generic8dot_to_unicode (UnicodeConverter):
    output_format = "unicode"
    options = UnicodeConverter.output_options

    def convert(self, input):
        unicode_blocks = []
        unicode = ""
        for chunk in input.split(b"\r\n"):
            for c in chunk:
                if c in self.directly_used_bytes:
                    unicode += chr(c)
                elif c in self.table_bytes:
                    unicode += chr(0x2800 + self.table_bytes.index(c))
                    print(f"Finding character {c}: {self.table_bytes.index(c)}")
                else:
                    self.warning("unexpected_character", f"The character {c} is not expected in this file.")
                    unicode += chr(c)
            unicode_blocks.append(unicode)
            unicode = ""

        return ("\r\n".join(unicode_blocks)).encode(self.output_encoding)

    def close(self):
        # The input buffer is not used. Skip unicode_converter version
        self.closed = True
        return b""
