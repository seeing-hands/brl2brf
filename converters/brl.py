# Converter to and from BRL format
# Note: BRF format is considered the canonical format, so most converters are named based on the other one and convert to or from BRF
# This is not a requirement, just a tendency
from .converter import converter


class brl_to_brf (converter):
    name = "brl_to_brf"
    source_format = "brl"
    output_format = "brf"
    options = []

    def convert(self, brl):
        """
        Convert a BRL-formatted string to BRF.

        Notes:
            The input file format typically has a .brl extention, but is not known to be standardized.
            The devices that provide the canonical samples were from Hims.
            Specifically, the Braille Edge and QBraille XL Braille displays generate these files.
            This conversion is designed to support formats that do not do all the things that BRL files may have.
            Even perfectly normal BRF content can be processed by this and produce identical output.
        """
        brf = (
            brl.upper()
            .replace(b"}", b"]")
            .replace(b"{", b"[")
            .replace(b"`", b"@")
            .replace(b"~", b"^")
            .replace(b"|", b"\\")
        )

        return brf


class brf_to_brl (converter):
    name = "brf_to_brl"
    source_format = "brf"
    output_format = "brl"
    options = []

    def convert(self, brf):
        """
        Convert a BRF-formatted string to BRL.

        Notes:
            The input file format typically has a .brf extention.
            This format is the one expected by HumanWare Braille displays.
        """
        brl = (
            brf.lower()
            .replace(b"]", b"}")
            .replace(b"[", b"{")
            .replace(b"@", b"`")
            .replace(b"^", b"~")
            .replace(b"\\", b"|")
        )

        return brl
