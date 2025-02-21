#!/usr/bin/env python3
"""
BRL2BRF: Convert between raw Braille file formats

This script was written by Seeing Hands (seeinghands.org).

Copyright (c) 2022-2025 Seeing Hands
Licensed under the MIT license. See the "license" file for details.
"""

import argparse
import os
import sys
import re
import converters

VERSION = "1.2.1"


def convert_file(inf, outf, converter, warnings="display", warning_table=[]):
    """
    Convert a file using a provided converter instance.

    Parameters:
        inf: The input file stream, opened for read in binary mode.
        outf: The output file stream, opened for write or append in binary mode.
        converter: The converter instance that converts strings from one format to another.
    """
    def handle_warnings(warnings, default_warning_treatment, warning_table):
        for w in converter.warnings:
            treatment = default_warning_treatment
            for warning_source, warning_code, behavior in warning_table:
                if w[0] == warning_source:
                    if w[1] == warning_code or w[1] == "*":
                        treatment = behavior
                        break
            if treatment == "ignore":
                continue
            else:
                sys.stderr.write(F"Warning {w[0]}.{w[1]}: {w[2]}\n")
                if treatment == "error":
                    sys.stderr.write("Above warning treated as error.\n")
                    sys.exit(-2)

    for line in inf:
        outf.write(converter.convert_string(line))
        handle_warnings(converter.warnings, warnings, warning_table)
        converter.clear_warnings()
    outf.write(converter.close())
    handle_warnings(converter.warnings, warnings, warning_table)
    converter.clear_warnings()


def guess_format_from(filename, choices=converters.source_formats):
    """
    This just checks the extention case-insensitively for the available formats
    """

    extention = filename.lower().split(".")[-1]
    if extention in choices:
        return extention
    return None


def get_conversion_function(source_format, output_format, explicit_converters=[], generic_options={}, converter_options={}):
    """
    Part of the CLI: not intended to be called in scripts.
    Gets the appropriate conversion function for a set of format choices.
    If the choices are invalid, an error message is printed to stderr and the script exits.
    For finding a converter chain in scripts, use the function converters.find_converter
    """
    if source_format is None or output_format is None:
        sys.stderr.write("Could not identify the conversion you want to perform. Please provide --source-format and/or --output-format\n")
        sys.exit(-1)
    elif source_format == output_format and len(explicit_converters) == 0:
        sys.stderr.write("Source format and output format appear to be the same. If this is incorrect, please supply --source-format and --output-format\n")
        sys.exit(-1)

    converter_function = converters.find_converter(source_format, output_format, explicit_converters, generic_options, converter_options)
    if converter_function is None:
        sys.stderr.write(f"Could not find a converter from {source_format} to {output_format}")
    return (converter_function, source_format, output_format)


def validate_converter_option(option_string, converter_options_dict):
    """
    Part of the CLI. Splits an option into components, validates that they make sense, and returns a dictionary of the components.
    On errors, prints an error message and exits.
    """
    parts = option_string.split("=", 1)
    if len(parts) != 2:
        sys.stderr.write(f"Converter option {option_string}:\nFormat not recognized. Specify converter options as <converter>.<option>=<value>\n")
        sys.exit(-1)
    value = parts[1]
    parts = parts[0].split(".", 1)
    if len(parts) != 2:
        sys.stderr.write(f"Converter option {option_string}:\nFormat not recognized. Specify converter options as <converter>.<option>=<value>\n")
        sys.exit(-1)
    converter_name = parts[0]
    option_name = parts[1]
    if converter_name not in converters.converter_names:
        sys.stderr.write(f"Converter option {option_string}:\nNo such converter: {converter_name}\n")
        sys.exit(-1)

    found_option = False
    valid_value = False
    for c in converters.converters:
        if c.name == converter_name:
            for o in c.options:
                if o["name"] == option_name:
                    found_option = True
                    option_type = o.get("type", "choice")
                    if option_type == "choice":
                        for c in o["choices"]:
                            if c["name"] == value:
                                valid_value = True
                                break
                    if option_type == "int":
                        try:
                            value = int(value)
                            valid_value = True
                        except ValueError:
                            valid_value = False
                    if option_type == "str":
                        valid_value = True
                    break
            break

    if not found_option:
        sys.stderr.write(f"Converter option {option_string}:\nNo such option for {converter_name}: {option_name}\nTry using `--converter-help {converter_name}` for more information")
        sys.exit(-1)
    if not valid_value:
        sys.stderr.write(f"Converter option {option_string}:\nInvalid value for {converter_name}.{option_name}: {value}\nTry using `--converter-help {converter_name}` for more information")
        sys.exit(-1)
    if converter_name in converter_options_dict.keys():
        converter_options_dict[converter_name][option_name] = value
    else:
        converter_options_dict[converter_name] = {option_name: value}


def make_warning_table(user_warning_params):
    r = []
    for param_string in user_warning_params:
        parts = param_string.split("=", 1)
        if len(parts) != 2:
            sys.stderr.write(f"Warning {param_string}:\nFormat not recognized. Specify warning handlers as <converter>.<warning code>={ignore,display,error}\n")
            sys.exit(-1)
        treatment = parts[1]
        parts = parts[0].split(".", 1)
        if len(parts) != 2:
            sys.stderr.write(f"Warning {param_string}:\nFormat not recognized. Specify warning handlers as <converter>.<warning code>={ignore,display,error}\n")
            sys.exit(-1)
        converter_name = parts[0]
        warning_code = parts[1]
        if converter_name not in converters.converter_names:
            sys.stderr.write(f"Warning handler {param_string}:\nNo such converter: {converter_name}\n")
            sys.exit(-1)
        if treatment not in ["ignore", "display", "error"]:
            sys.stderr.write(f"Warning handler {param_string}:\nInvalid treatment: {treatment}\n")
            sys.exit(-1)
        r.append((converter_name, warning_code, treatment))
    return r


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
        sys.stderr.write("Creating directory: " + head + "\n")
    os.mkdir(head)


def convert_directory(directory, pattern, output_pattern, recursive, converter, default_warning_treatment, warning_table, verbose=False):
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
        "^" + re.escape(pattern).replace("\\*", "(?P<name>.*)") + "$",
        re.IGNORECASE
    )

    for filename in list_files(directory, recursive):
        m = file_pattern.match(filename[len(directory):])
        if m:
            converted_file_name = output_pattern.replace("*", m.group("name"))
            ensure_directory_for(converted_file_name, verbose=verbose)
            if verbose:
                sys.stderr.write("Converting " + filename + " to " + converted_file_name + "\n")
            with open(filename, "rb") as input_file:
                with open(converted_file_name, "wb") as output_file:
                    convert_file(input_file, output_file, converter(), default_warning_treatment, warning_table)


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

    # Input args are not required because having a required group will block special options like --converter-help
    # For normal usage, exactly one is required and this will be checked
    input_args = args.add_mutually_exclusive_group()
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
        choices=converters.source_formats)
    args.add_argument("-of", "--output-format",
        help="Specify the format of the output file. If not provided, it will be assumed from file names", action="store",
        choices=converters.output_formats)

    args.add_argument("-c", "--converter", action="append",
        help="Specify a converter to use. Format converters can usually be assigned automatically.",
        choices=converters.converter_names, default=[])
    args.add_argument("-co", "--converter-option", action="append", default=[],
        help="Specify an option of a converter. For a list, use the --converter-help argument.")
    args.add_argument("--converter-help",
        help="Get information about a converter and its options.",
        choices=converters.converter_names)

    args.add_argument("--warnings",
        help="Set default handling for converter warnings",
        choices=["display", "ignore", "error"], default="display")
    args.add_argument("--warning", action="append",
        help="Set handling for specific converter warnings. Use the format <converter_name>.<warning_name>={display,ignore,error}",
        default=[])

    if "--help" in sys.argv:
        args.print_help(file=sys.stderr)
        sys.exit(0)

    if "--version" in sys.argv:
        sys.stderr.write("BRL2BRF version " + VERSION + "\nWritten by Seeing Hands\n")
        sys.exit(0)

    try:
        config = args.parse_args()
    except argparse.ArgumentError as ae:
        args.print_usage(file=sys.stderr)
        sys.stderr.write(str(ae) + "\n")
        sys.stderr.write("For more information, specify --help\n")
        sys.exit(-1)

    # Set up converters requested on the command line
    # Print converter help if requested
    if config.converter_help is not None:
        for c in converters.converters:
            if c.name == config.converter_help:
                sys.stderr.write(c.usage())
                sys.exit(0)

    generic_options = {}

    converter_options = {}
    for converter_option in config.converter_option:
        validate_converter_option(converter_option, converter_options)

    warning_table = make_warning_table(config.warning)

    converter = None

    if config.directory is not None:
        if config.pattern is None:
            sys.stderr.write("The --pattern parameter is required when using directory mode. Specify --help for more information.\n")
            sys.exit(-1)
        source_format = config.source_format
        if source_format is None:
            source_format = guess_format_from(config.pattern, choices=converters.source_formats)
        output_format = config.output_format
        if output_format is None and config.name_pattern is not None:
            output_format = guess_format_from(config.name_pattern, choices=converters.output_formats)
        converter, source_format, output_format = get_conversion_function(source_format, output_format, config.converter, generic_options, converter_options)
        output_pattern = config.name_pattern
        if output_pattern is None:
            output_pattern = "*." + output_format
        if not os.path.exists(config.directory):
            sys.stderr.write("Could not open directory: " + config.directory)
            sys.exit(-1)
        return convert_directory(
            config.directory,
            config.pattern,
            output_pattern,
            config.recursive,
            converter,
            config.warnings,
            warning_table,
            config.verbose
        )

    # Not set to directory mode, convert a single file
    # Check that we have input arguments that we need
    if not config.stdin and config.file is None:
        args.print_usage(file=sys.stderr)
        sys.stderr.write("Error: Exactly one of the --stdin, --file, or --directory options are required.\n")
        sys.exit(-1)

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
            sys.stderr.write("Could not open file: " + config.file + ".\n")
            sys.exit(-1)

        if source_format is None:
            source_format = guess_format_from(config.file, choices=converters.source_formats)

    if config.stdout:
        output_file = sys.stdout.buffer
    else:
        try:
            output_file = open(config.output, "wb")
        except FileNotFoundError:
            sys.stderr.write("Could not open file: " + config.file + " for writing.\n")
            sys.exit(-1)

        if output_format is None:
            output_format = guess_format_from(config.output, choices=converters.output_formats)

    converter, source_format, output_format = get_conversion_function(source_format, output_format, config.converter, generic_options, converter_options)
    convert_file(input_file, output_file, converter(), config.warnings, warning_table)
    if not config.stdin:
        input_file.close()

    if not config.stdout:
        output_file.close()


if __name__ == "__main__":
    main(sys.argv)
