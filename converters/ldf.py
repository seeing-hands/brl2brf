# Converter between LDF and BRF format
# Note: The LDF format was created by Levelstar for the Icon and Braille Plus devices
# BRF is used as the destination format because LDF's Braille format is closest to it
# Except that LDF Braille renders letters in lowercase

from .converter import converter
from xml.etree import ElementTree
import zipfile
import io

# Notes on the format
# LDF files are zip archives with an XML file enclosed
# They have both text and Braille content. The converter will convert both of these as follows:
# Converting an LDF file that's all Braille will produce a Braille file in BRF format.
# Converting an LDF file that's all text will produce a text file in ASCII format (Unicode is not supported).
# Converting a file with both types of content will produce a file where the Braille parts are in Braille and
# the text parts are rendered directly and will therefore show up in computer Braille.
# Converting a file to LDF format will only use one format, which is user-selectable
# Some formatting options are available in LDF which do not make sense in a Braille format
# These will be discarded during conversion. The default options of left alignment and single spacing will be used when converting to LDF.
# "allignment" is a typo, but not my typo. Spelling it "alignment" makes the file not work.

LDF_CONTENT_FILE_NAME = "content.xml"
LDF_TYPE = "LevelStar Document Format Ver 1.0"


class brf_to_ldf (converter):
    name = "brf_to_ldf"
    source_format = "brf"
    output_format = "ldf"
    options = [
        {
            "name": "ldf_type",
            "description": "The type of the content in the LDF file",
            "options": [
                {
                    "name": "braille",
                    "description": "Braille content, in EBAE grade 2 English Braille",
                    "default": True
                },
                {
                    "name": "text",
                    "description": "Text, in computer Braille or ASCII text",
                }
            ]
        }
    ]

    def __init__(self, generic_options, converter_options):
        converter.__init__(self, generic_options=generic_options, converter_options=converter_options)
        self.content_xml = ElementTree.Element("content", {"type": LDF_TYPE})
        if converter_options.get("ldf_type", "braille") == "text":
            self.content_type = "text/plain"
        else:
            self.content_type = "text/braille"

    def ldf_text(self, data):
        if self.content_type == "text/plain":
            return data
        elif self.content_type == "text/braille":
            return data.lower()
        else:
            raise ConverterError("Unknown content type {self.content_type}")

    def convert(self, brf, closing=False):
        self.input_buffer += brf
        while b"\n" in self.input_buffer:
            i = self.input_buffer.index(b"\n")
            paragraph_text = self.input_buffer[0:i].strip(b"\r")
            self.add_paragraph(paragraph_text)
            self.input_buffer = self.input_buffer[i + 1:]
        if closing:
            self.add_paragraph(self.input_buffer)
            self.input_buffer = b""
        return b""

    def add_paragraph(self, text):
        paragraph = ElementTree.Element("p", {"allignment": "left"})
        if text != b"":
            textblock = ElementTree.Element("text",
                {
                    "content_type": self.content_type,
                    "style": "default"
                },
            )
            textblock.text = self.ldf_text(text.decode("UTF-8"))
            paragraph.append(textblock)
        self.content_xml.append(paragraph)

    def close(self):
        if self.input_buffer != "":
            self.convert(b"", closing=True)
        content = ElementTree.ElementTree(self.content_xml)
        zf = io.BytesIO()
        z = zipfile.ZipFile(zf, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=False)
        cf = z.open(LDF_CONTENT_FILE_NAME, "w")
        ElementTree.indent(content, space="\t")
        content.write(cf, encoding='us-ascii', xml_declaration=False, short_empty_elements=False)
        cf.close()
        z.close()
        return zf.getvalue()


class ldf_to_brf (converter):
    name = "ldf_to_brf"
    source_format = "ldf"
    output_format = "brf"
    options = []

    def __init__(self, generic_options, converter_options):
        converter.__init__(self, generic_options=generic_options, converter_options=converter_options)
        self.ldf_file = io.BytesIO()

    def convert(self, ldf):
        # LDF files aren't processed in chunks. Add this to the buffer which will be processed on completion
        self.ldf_file.write(ldf)
        return b""

    def close(self):
        # All conversion occurs here
        self.ldf_file.seek(0)
        output_buffer = io.BytesIO()
        z = zipfile.ZipFile(self.ldf_file, "r")
        for fn in z.namelist():
            if fn != LDF_CONTENT_FILE_NAME:
                self.warning("unexpected_file", f"The file {fn} inside the LDF was not expected and has been ignored.")
        try:
            f = z.open(LDF_CONTENT_FILE_NAME, "r")
            x = ElementTree.parse(f)
        except KeyError:
            raise ConverterError(f"The file {LDF_CONTENT_FILE_NAME} was not found in the LDF file")
        root = x.getroot()
        if root.tag != "content" or root.attrib.get("type", "No type specified") != LDF_TYPE:
            self.warning("unknown_format", f"Root element is not the expected <content type=\"{LDF_TYPE}\">.")
        for paragraph in root:
            if paragraph.tag != "p":
                self.warning("unknown_format", f"Paragraph element is not the expected <p>.")
            if paragraph.attrib.get("allignment", "left") != "left":
                self.warning("formatting_removed", f"Alignment is not preserved when converting LDF files.")
            for textblock in paragraph:
                if textblock.attrib.get("style", "default") != "default":
                    self.warning("formatting_removed", f"Unknown style value {textblock.attrib['style']} has been discarded.")
                content_type = textblock.attrib.get("content_type", "None specified")
                if content_type == "text/braille":
                    output_buffer.write(textblock.text.encode("UTF-8").upper())
                else:
                    if content_type != "text/plain":
                        self.warning("unexpected_content_type", f"The type {content_type} is unknown and will be treated as text")
                    output_buffer.write(textblock.text.encode("UTF-8"))
            output_buffer.write(b"\r\n")
        return output_buffer.getvalue()
