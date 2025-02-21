# Converter to and from GF format
# GF is a file type supported by the notepad application on the BrailleSense Polaris from Hims/Selvas
# The manual does not explain what this is or where else it might be used
# The GF format uses the same characters that the BRF format does except that the BRF format uses uppercase letters while the GF format uses lowercase letters

from .converter import converter


class gf_to_brf (converter):
    name = "gf_to_brf"
    source_format = "gf"
    output_format = "brf"
    options = []

    def convert(self, gf):
        """
        Convert a GF-formatted string to BRF.
        """
        return gf.upper()


class brf_to_gf (converter):
    name = "brf_to_gf"
    source_format = "brf"
    output_format = "gf"
    options = []

    def convert(self, brf):
        """
        Convert a BRF-formatted string to GF.
        """
        return brf.lower()
