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
                    brf += brf_table_chars[(c - 0x2800) % len(brf_table_chars)]
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
