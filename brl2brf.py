#!/usr/bin/env python3
"""
BRL2BRF: Convert between raw Braille file formats

This script was written by Seeing Hands (seeinghands.org).

Copyright (c) 2022-2023 Seeing Hands
Licensed under the MIT license. See the "license" file for details.
"""

import argparse
import os
import sys
import re

VERSION = "1.0.0"

format_choices = ["brf", "brl"]


def convert_string_brl_to_brf(brl):
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
        .replace(b"\r\n", b"\n")
    )

    return brf


def convert_string_brf_to_brl(brf):
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
        .replace(b"\n", b"\r\n")
    )

    return brl


def convert_file(inf, outf, converter=convert_string_brl_to_brf):
    """
    Convert a file using a provided convertion function.

    Parameters:
        inf: The input file stream, opened for read in binary mode.
        outf: The output file stream, opened for write or append in binary mode.
        converter: The function that converts strings from one format to another. The default will convert BRL files with a variety of possible codes to BRF as understood by strict libraries.
    """
    for line in inf:
        outf.write(converter(line))


def guess_format_from(filename):
    """
    This just checks the extention case-insensitively for the available formats
    """

    extention = filename.lower().split(".")[-1]
    if extention in format_choices:
        return extention
    return None


def get_conversion_function(source_format, output_format):
    """
    Part of the CLI: not intended to be called in scripts.
    Gets the appropriate conversion function for a set of format choices.
    If the choices are invalid, an error message is printed to stderr and the script exits.
    """
    if source_format is None and output_format is None:
        sys.stderr.write("Could not identify the conversion you want to perform. Please provide --source-format and/or --output-format\n")
        sys.exit(-1)
    # Since there are two formats, if we could only get one, we will assume the alternative is used
    elif source_format is None:
        source_format = "brf" if output_format == "brl" else "brl"
    elif output_format is None:
        output_format = "brf" if source_format == "brl" else "brl"
    elif source_format == output_format:
        sys.stderr.write("Source format and output format appear to be the same. If this is incorrect, please supply --source-format and --output-format\n")
        sys.exit(-1)

    converter = None
    if source_format == "brl" and output_format == "brf":
        converter = convert_string_brl_to_brf
    elif source_format == "brf" and output_format == "brl":
        converter = convert_string_brf_to_brl
    else:
        sys.stderr.write("No available converter from " +source_format +" to " +output_format +".\n")

    return (converter, source_format, output_format)


def list_files(basedir=".", recursive=True):
    for fn in os.listdir(basedir):
        ffn = os.path.join(basedir, fn)
        if os.path.isfile(ffn):
            yield ffn
        else:
            if recursive:
                for sfn in list_files(ffn, recursive=True):
                    yield sfn


def ensure_directory_for(path, verbose=False):
    """
    Create the directories, if they don't exist, so the provided path is valid.
    """
    head, tail = os.path.split(path)
    if head == "" or os.path.exists(head):
        return
    ensure_directory_for(head)
    if verbose:
        sys.stderr.write("Creating directory: " +head +"\n")
    os.mkdir(head)


def convert_directory(directory, pattern, output_pattern, recursive, converter, verbose=False):
    """
    Part of the CLI. Not intended for inclusion in scripts.
    Convert a directory of files.
    """
    # Convert the user's pattern into a regular expression
    # Note that I'm not letting them put their own regex in here
    # This is so that they can have one asterisk substituted with a part of their choosing,
    # whereas allowing them to put in their own expression would break the named group that stores that bit
    if pattern.count("*") > 1:
        sys.stderr.write("The search pattern may only contain one asterisk (*) character.\n")
        sys.exit(-1)
    file_pattern = re.compile(
        "^" +re.escape(pattern).replace("\\*", "(?P<name>.*)") +"$",
        re.IGNORECASE
    )

    for filename in list_files(directory, recursive):
        m = file_pattern.match(filename[len(directory):])
        if m:
            converted_file_name = output_pattern.replace("*", m.group("name"))
            ensure_directory_for(converted_file_name, verbose=verbose)
            if verbose:
                sys.stderr.write("Converting " +filename +" to " +converted_file_name +"\n")
            with open(filename, "rb") as input_file:
                with open(converted_file_name, "wb") as output_file:
                    convert_file(input_file, output_file, converter)


def main(argv):
    "The CLI frontend for the converter tool"

    args = argparse.ArgumentParser(
        description="Convert between raw braille file formats",
        epilog="For more information and examples, consult the included readme or the project page at: https://github.com/seeing-hands/brl2brf",
        add_help=False,
        exit_on_error=False
    )
    args.add_argument("--help", help="Print help message listing all arguments", action="store_true")
    args.add_argument("--version", help="Print the version of the tool", action="store_true")
    args.add_argument("-v", "--verbose",
        help="Print progress messages to standard error", action="store_true")

    input_args = args.add_mutually_exclusive_group(required=True)
    input_args.add_argument("-i", "--stdin",
        help="Read input file from standard input", action="store_true")
    input_args.add_argument("-f", "--file",
        help="The path to an input file", action="store")
    input_args.add_argument("-d", "--directory",
        help="The path to a directory where input files are found (argument --pattern is required)", action="store")

    # Output args are not required because the directory method will find the output paths for itself
    output_args = args.add_mutually_exclusive_group(required=False)
    output_args.add_argument("-o", "--stdout",
        help="Print output to standard output", action="store_true")
    output_args.add_argument("-w", "--output",
        help="The path to an output file", action="store")

    # The arguments for directory mode
    directory_args = args.add_argument_group(title="Directory mode",
        description="Arguments particular to the automatic conversion of a directory of files")
    directory_args.add_argument("-p", "--pattern",
        help="The search pattern for files to be converted. For example: *.brl", action="store")
    directory_args.add_argument("-np", "--name-pattern",
        help="The pattern to be used for created files. If not provided, the new pattern will be created from the specified format, just changing the extentions. A * character can be provided, which will be replaced by the characters covered by the wildcard in the original file name.",
        action="store")
    directory_args.add_argument("-r", "--recursive",
        help="Process subdirectories recursively", action="store_true")

    args.add_argument("-sf", "--source-format",
        help="Specify the format of the source file. If not provided, it will be assumed from file names", action="store",
        choices=format_choices)
    args.add_argument("-of", "--output-format",
        help="Specify the format of the output file. If not provided, it will be assumed from file names", action="store",
        choices=format_choices)

    if "--help" in sys.argv:
        args.print_help(file=sys.stderr)
        sys.exit(0)

    if "--version" in sys.argv:
        sys.stderr.write("BRL2BRF version " +VERSION +"\nWritten by Seeing Hands\n")
        sys.exit(0)

    try:
        config = args.parse_args()
    except argparse.ArgumentError as ae:
        args.print_usage(file=sys.stderr)
        sys.stderr.write(str(ae) +"\n")
        sys.stderr.write("For more information, specify --help\n")
        sys.exit(-1)

    converter = None

    if config.directory is not None:
        if config.pattern is None:
            sys.stderr.write("The --pattern parameter is required when using directory mode. Specify --help for more information.\n")
            sys.exit(-1)
        source_format = config.source_format
        if source_format is None:
            source_format = guess_format_from(config.pattern)
        output_format = config.output_format
        if output_format is None and config.name_pattern is not None:
            output_format = guess_format_from(config.name_pattern)
        converter, source_format, output_format = get_conversion_function(source_format, output_format)
        output_pattern = config.name_pattern
        if output_pattern is None:
            output_pattern = "*." +output_format
        if not os.path.exists(config.directory):
            sys.stderr.write("Could not open directory: " +config.directory)
            sys.exit(-1)
        return convert_directory(
            config.directory,
            config.pattern,
            output_pattern,
            config.recursive,
            converter,
            config.verbose
        )

    # Not set to directory mode, convert a single file
    input_file = None
    output_file = None
    source_format = config.source_format
    output_format = config.output_format

    # Check that we have output arguments that we need
    if not config.stdout and config.output is None:
        args.print_usage(file=sys.stderr)
        sys.stderr.write("Error: Neither --stdout nor --output were specified.\n")
        sys.exit(-1)

    if config.stdin:
        input_file = sys.stdin.buffer
    else:
        try:
            input_file = open(config.file, "rb")
        except FileNotFoundError:
            sys.stderr.write("Could not open file: " +config.file +".\n")
            sys.exit(-1)

        if source_format is None:
            source_format = guess_format_from(config.file)

    if config.stdout:
        output_file = sys.stdout.buffer
    else:
        try:
            output_file = open(config.output, "wb")
        except FileNotFoundError:
            sys.stderr.write("Could not open file: " + config.file + " for writing.\n")
            sys.exit(-1)

        if output_format is None:
            output_format = guess_format_from(config.output)

    converter = get_conversion_function(source_format, output_format)
    convert_file(input_file, output_file, converter)
    if not config.stdin:
        input_file.close()

    if not config.stdout:
        output_file.close()


if __name__ == "__main__":
    main(sys.argv)
