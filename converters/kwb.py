# Converter from KWB format
# Note: BRF format is considered the canonical format, so most converters are named based on the other one and convert to or from BRF
# This is not a requirement, just a tendency
from .converter import converter


class kwb_to_brf (converter):
    name = "kwb_to_brf"
    description = "Converts KWB files, generated by old BrailleNote devices."
    source_format = "kwb"
    output_format = "brf"
    options = [
        {
            "name": "linebreaks",
            "description": "How should line break characters for the size of the display be handled",
            "choices": [
                {
                    "name": "space",
                    "description": "Keep only user-inserted line breaks, removing the automatic word wrapping and separating words around line boundaries. Use this option if you intend to reflow the file.",
                    "default": True
                },
                {
                    "name": "retain",
                    "description": "Keep BrailleNote-generated line breaks.",
                    "default": False
                },
                {
                    "name": "delete",
                    "description": "Keep only user-inserted line breaks and do not split words around line boundaries. Use this if word wrap was disabled when creating the file or if long chunks of data that were not wrapped need to be obtained.",
                    "default": False
                }
            ]
        }
    ]

    # Constant characters
    SECTION_SEPARATOR = b"\x1a" # Found at end of header and content sections
    TEXT_SEPARATOR = b"\x02" # Found at boundaries between renderable content and non-renderable data

    def __init__(self, generic_options={}, converter_options={}):
        converter.__init__(self, generic_options=generic_options, converter_options=converter_options)
        self.autolinebreak_str = None
        if converter_options.get("linebreaks", "space") == "space":
            self.autolinebreak_str = b" "
        elif converter_options.get("linebreaks", "space") == "delete":
            self.autolinebreak_str = b""
        elif converter_options.get("linebreaks", "space") == "retain":
            self.autolinebreak_str = b"\r\n"
        else:
            raise ValueError(f"Unexpected setting for line break behavior: {converter_options.get('linebreaks', 'space')}")

        self.header = b""
        self.stage = 0
        # stages:
        # 0: Reading header
        # 1: Reading content section, splitting readable and unreadable chunks
        # 2: Ended content section, this should be the end of the file

    def convert_section(self, kwb):
        """
        Determines if a content section is readable or not and converts it if it is.
        """
        READABLE_CHARACTERS = b"\n\r !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_"
        for ci in range(len(kwb)):
            if kwb[ci] not in READABLE_CHARACTERS:
                # Not readable. Reject
                return b""
        return kwb.replace(b"\r", self.autolinebreak_str).replace(b"\n", b"\r\n")

    def convert(self, kwb):
        """
        Convert a KWB-formatted string to BRF.
        """

        if self.stage == 0: # parsing header
            parts = kwb.split(self.SECTION_SEPARATOR)
            self.header += parts[0]
            if len(parts) > 1:
                self.stage = 1
                if len(self.header) != 512:
                    self.warning("kwb_format_unexpected",
                        f"KWB header has unexpected length:\nExpected: 512, actual: {len(self.header)}"
                    )
                return self.convert(kwb[kwb.index(self.SECTION_SEPARATOR)+1:])
            else:
                return b""

        elif self.stage == 1:
            # building content chunks
            if kwb.count(self.TEXT_SEPARATOR) > 0:
                self.input_buffer += kwb[0:kwb.index(self.TEXT_SEPARATOR)]
                converted = self.convert_section(self.input_buffer)
                self.input_buffer = b""
                return (converted + self.convert(kwb[kwb.index(self.TEXT_SEPARATOR)+1:]))
            elif kwb.count(self.SECTION_SEPARATOR) > 0:
                self.input_buffer += kwb[0:kwb.index(self.SECTION_SEPARATOR)]
                converted = self.convert_section(self.input_buffer)
                self.input_buffer = b""
                self.stage = 2
                return (converted + self.convert(kwb[kwb.index(self.SECTION_SEPARATOR)+1:]))
            else:
                self.input_buffer += kwb
                return b""

        elif self.stage == 2:
            # content has ended
            if len(kwb) > 0:
                self.warning("kwb_format_unexpected",
                "Unexpected data found after content section")
            return b""

        else:
            raise ConverterError(f"Unknown stage value: {self.stage}")

    def close(self):
        self.closed = True
        if self.input_buffer != b"":
            return self.convert(self.input_buffer)
        return b""
