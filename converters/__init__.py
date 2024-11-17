# BRL2BRF converters
# This directory contains converter modules which encode or decode a certain format
# Each converter is an instance of class brl2brf.converter
# This file contains generic utilities for tracking and working with converters
from .converter import converter, ConverterError, converter_chain

# Add any new converters to this list
from . import brl
from . import kwb
from . import helptech
from . import braban
from . import ldf
from . import pef
from . import brf
from . import reflow

converters = [
    brl.brl_to_brf,
    brl.brf_to_brl,
    kwb.kwb_to_brf,
    brf.unicode_to_brf,
    brf.brf_to_unicode,
    helptech.helptech_to_unicode,
    helptech.unicode_to_helptech,
    braban.bra_to_unicode,
    braban.unicode_to_bra,
    braban.ban_to_unicode,
    braban.unicode_to_ban,
    ldf.ldf_to_brf,
    ldf.brf_to_ldf,
    pef.pef_to_unicode,
    reflow.reflow
]

source_formats = sorted(list(set(
    [c.source_format for c in converters]
)))

output_formats = sorted(list(set(
    [c.output_format for c in converters]
)))

converter_names = sorted(
    [c.name for c in converters]
)


def get_converter(converter_name, generic_options, converter_options):
    converter = None
    for c in converters:
        if c.name == converter_name:
            converter = c
            break
    if converter is None:
        raise ValueError(f"No such converter: {converter_name}")

    def make_converter_instance():
        return converter(generic_options=generic_options, converter_options=converter_options)
    return make_converter_instance


def chain_converters(cnames, generic_options, converter_options):
    if len(cnames) == 0:
        raise ValueError("Cannot construct a chain of zero converters.")
    if len(cnames) == 1:
        options = {}
        for co in converter_options.keys():
            if co == cnames[0]:
                options = converter_options[co]
        return get_converter(cnames[0], generic_options, options)
    chain = []
    for i in range(len(cnames)):
        options = {}
        for co in converter_options:
            if co == cnames[i]:
                options = converter_options[co]
        chain.append(get_converter(cnames[i], generic_options, options))

    def make_chain_instance():
        cs = []
        for c in chain:
            cs.append(c())
        return converter_chain(cs)

    return make_chain_instance


def find_converter(source_format, output_format, explicit_converters=[], generic_options={}, converter_options={}):
    """
    Find the converter or set of converters that takes the provided source format, results in the provided output format,
    and includes any converters specified explicitly.

    Parameters:
    source_format: One of the elements of source_formats
    output_format: One of the elements of output_formats
    explicit_converters: A list of converters that are required to be in the chain

    Returns:
    A function which, when called, returns an instance of type converter which performs the desired conversion,
    or None if no such converter can be identified.
    Note: The returned type may be a single converter or a chain of converters, derived from converter_chain.

    Note: In the event where multiple converter chains are valid, preference will be given to the shortest chain that satisfies the requirement.
    Note: This function returns a creator which can be called repeatedly to generate more instances of the same converter with the same configuration.
    """

    shortest = []
    shortest_length = len(converters)
    for chain in find_converter_chain(source_format, output_format):
        if len(chain) < shortest_length:
            valid_chain = True
            for ec in explicit_converters:
                if ec not in chain:
                    valid_chain = False
                    break
            if valid_chain:
                shortest = chain
                shortest_length = len(chain)
    if len(shortest) == 0:
        return None
    return chain_converters(shortest, generic_options, converter_options)


def find_converter_chain(source_format, output_format, chain=[]):
    """
    Graph-walk converters to find possible paths. This is an internal function.

    Performance note: This is an exhaustive search. It is fine when we have 2-10 converters and probably works fine with quite a few more.
    If we ever get a hundred converters, this should be improved.
    """
    if source_format not in source_formats:
        return
    if output_format not in output_formats:
        return
    for c in converters:
        if c.name in chain:
            # Converters may not occur twice in a chain
            continue
        if c.source_format == source_format:
            if c.output_format == output_format:
                yield chain + [c.name]
            for subchain in find_converter_chain(c.output_format, output_format, chain + [c.name]):
                yield subchain
