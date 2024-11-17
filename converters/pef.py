# PEF decoder
# Note: The PEF format is intended for paper Braille documents
# For notes, see the file doc/pef.md
# There are a lot of notes which are relevant to understanding what this does and why.

from .unicode import UnicodeConverter
from xml.etree import ElementTree
import io

# The PEF XML namespace. The URI is broken
PEF_NS = "http://www.daisy.org/ns/2008/pef"

def pef_tag(tag):
    return "{" +PEF_NS +"}" +tag

class pef_to_unicode(UnicodeConverter):
    name = "pef_to_unicode"
    source_format = "pef"
    output_format = "unicode"
    options = UnicodeConverter.output_options

    def __init__(self, generic_options, converter_options):
        UnicodeConverter.__init__(self, generic_options=generic_options, converter_options=converter_options)
        self.pef_file = io.BytesIO()

    def convert(self, pef):
        # Currently, PEF files aren't processed in chunks. Add this to the buffer which will be processed on completion
        # Note: This may be changed in the future to do the more typical streaming conversion
        self.pef_file.write(pef)
        return b""

    def read_pef_into(self, element, components):
        for subelem in element:
            if subelem.tag == pef_tag("row"):
                if subelem.text is None:
                    components.append("")
                else:
                    components.append(subelem.text)

            else:
                if subelem.tag not in [pef_tag("volume"), pef_tag("section"), pef_tag("page")]:
                    # Not a container element known to contain data, but we'll try it anyway
                    self.warning("unexpected_element", f"The element {subelem.tag} is unknown.")
                self.read_pef_into(subelem, components)

    def close(self):
        # All conversion occurs here
        self.pef_file.seek(0)
        x = ElementTree.parse(self.pef_file)
        unicode_components = []
        r = x.getroot()
        if r.tag != pef_tag("pef"):
            self.warning("Unknown_element", f"The element {r.tag} is not the expected type <pef>. Parsing will continue, but this may not be a PEF file.")

        for element in r:
            if element.tag == pef_tag("head"):
                # Head tag contains meta elements, but we don't use them
                continue
            elif element.tag == pef_tag("body"):
                self.read_pef_into(element, unicode_components)
            else:
                self.warning("Unknown_element", f"The element {element.tag} is unknown and has been ignored.")
        s= "\r\n".join(unicode_components).encode(self.output_encoding)
        return s
