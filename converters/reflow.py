# Reflow a file to an explicit line length with various wrapping settings
from .unicode import UnicodeConverter
import re


class reflow (UnicodeConverter):
    name = "reflow"
    source_format = "unicode"
    output_format = "unicode"
    options = (
        UnicodeConverter.input_options + UnicodeConverter.bidirectional_output_options + [
            {
                "name": "line_length",
                "required": True,
                "description": "The length in characters of the line to reflow.",
                "type": "int"
            },
            {
                "name": "word_wrap",
                "description": "Whether to wrap words when possible",
                "choices": [
                    {
                        "name": "wrap",
                        "description": "Move words onto the next line if they will overflow",
                        "default": True
                    },
                    {
                        "name": "split",
                        "description": "Split the word across lines with an interleaving string",
                    },
                    {
                        "name": "cut",
                        "description": "Split the word without notification",
                    }
                ]
            },
            {
                "name": "split_character",
                "description": "If a word is split, either deliberately or because there is no space, what characters should be inserted to denote this",
                "type": "string",
                "default": "\u2824"
            },
            {
                "name": "linebreaks",
                "description": "How to handle explicit line breaks in the source material",
                "choices": [
                    {
                        "name": "strict",
                        "description": "All line breaks are retained. This will not allow a file to be reflowed to a longer line length than it started.",
                    },
                    {
                        "name": "double",
                        "description": "Two or more line breaks are retained, whereas single line breaks are replaced by spaces for reflowing.",
                        "default": True
                    },
                    {
                        "name": "remove",
                        "description": "All line breaks are replaced by spaces.",
                    }
                ]
            }
        ]
    )

    blank_chars = [" ", "\u2800", "\n", "\r"]

    def __init__(self, generic_options, converter_options):
        UnicodeConverter.__init__(self, generic_options, converter_options)
        self.line_length = converter_options.get("line_length", 40)
        self.word_wrap = converter_options.get("word_wrap", "wrap")
        self.linebreaks = converter_options.get("linebreaks", "double")
        self.split_str = converter_options.get("split_character", "\u2824")
        self.linebreak_str = "\r\n"
        self.space_char = " "
        self.text_buffer = ""

    def close(self):
        return self.convert(b"", closing=True)

    def convert(self, data, closing=False):
        self.text_buffer += self.unicode_decode(data)
        if self.linebreaks == "remove":
            self.text_buffer = self.text_buffer.replace("\r\n", self.space_char).replace("\n", self.space_char)
        if self.linebreaks == "double":
            i = len(self.text_buffer)-1
            while i > 0 and self.text_buffer[i] in "\r\n":
                i -= 1
            suffix = self.text_buffer[i:]
            self.text_buffer = re.sub("([^\n\r])(\r?\n)([^\n\r])", f"\\1{self.space_char}\\3", self.text_buffer[0:i]) + suffix
        lines = []
        while len(self.text_buffer) > self.line_length:
            nli = -1
            if "\n" in self.text_buffer:
                nli = self.text_buffer.index("\n")
            if "\r" in self.text_buffer:
                cri = self.text_buffer.index("\r")
                if cri < nli: nli = cri
            if nli != -1 and nli < self.line_length:
                # This line is already explicitly at size. Retain it
                while nli < len(self.text_buffer) and self.text_buffer[nli] in "\r\n":
                    nli += 1
                lines.append(self.text_buffer[0:nli])
                self.text_buffer = self.text_buffer[nli:]
                continue
            # Time to split lines
            if self.word_wrap == "cut":
                # slice off a chunk and start again
                lines.append(self.text_buffer[0:self.line_length] + self.linebreak_str)
                self.text_buffer = self.text_buffer[self.line_length:]
            if self.word_wrap == "split":
                if self.text_buffer[self.line_length] in self.blank_chars:
                    # No need to insert a split character
                    lines.append(self.text_buffer[0:self.line_length] + self.linebreak_str)
                    self.text_buffer = self.text_buffer[self.line_length:]
                else:
                    # Insert the split character
                    ll = self.line_length - len(self.split_str)
                    lines.append(self.text_buffer[0:ll] + self.split_str + self.linebreak_str)
                    self.text_buffer = self.text_buffer[ll:]
            if self.word_wrap == "wrap":
                made_line = False
                ci = self.line_length
                while ci >= 0:
                    if self.text_buffer[ci] in self.blank_chars:
                        made_line = True
                        break
                    ci -= 1
                if made_line:
                    lines.append(self.text_buffer[0:ci] + self.linebreak_str)
                    self.text_buffer = self.text_buffer[ci+1:]
                else:
                    # Can't wrap this line. Split it instead
                    ll = self.line_length - len(self.split_str)
                    lines.append(self.text_buffer[0:ll] + self.split_str + self.linebreak_str)
                    self.text_buffer = self.text_buffer[ll:]
        if closing:
            # Normally, retain any dangling chunk and attach next material
            # When closing, emit any dangling material
            lines.append(self.text_buffer)
            self.text_buffer = ""
        return self.unicode_encode("".join(lines))
