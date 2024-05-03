class ConverterError(Exception):
    """
    The general class for converter-related exceptions
    """


class converter:
    """
    The converter class represents a generic format converter.
    A converter converts in one direction only.
    Bidirectional converters are common, and are implemented by creating two converter instances which may share code.
    A converter may perform operations other than simple format conversion, for example changing the content.
    There are two ways to implement that behavior. One is to include options that change how the converter operates.
    The other is by having the source and output formats set to the same value and having the user manually add the converter with the -c option.
    Converters must be thread safe. For most converters, this is likely not to be a problem, as they will only need internal resources.
    Any use of common resources should use locks to ensure they can be run concurrently.
    A typical converter should take the converter_options and generic_options lists as arguments to the initialization function, but no other parameters.
    """

    name = "unnamed"
    description = "This converter has no description"
    source_format = None
    output_format = None
    options = []

    def __init__(self, generic_options={}, converter_options={}):
        if self.source_format is None or self.output_format is None:
            raise NotImplementedError("The source or output format is not set.")
        self.input_buffer = b""
        self.warnings = []
        self.closed = False

    def __del__(self):
        if len(self.input_buffer) != 0:
            raise ConverterError("Not all data was processed")

    def convert(self, s):
        """
        Takes a binary string (bytes) to be converted.
        This function must return a binary string.
        The returned string may but is not required to contain some or all of the converted data.
        If this function can convert the file on a line-by-line basis,
        returning converted data allows the main program to convert large files without holding most or all of the data in memory.
        This function can also simply add the data to the input buffer, to be processed later when close() is called.

        This function is required to be overridden by subclasses.
        """
        raise NotImplementedError("This function must be overridden by the converter.")

    def close(self):
        """
        This function must return a binary string.
        The returned string may but is not required to contain some or all of the converted data.
        The close function indicates that the caller has no more data to convert.
        If the input buffer is used to store data, this function should convert any remaining data in the input buffer and return it.
        If the buffer is not used, this function does not need to be overridden and will return an empty binary string.
        This function should set self.closed to True.
        """
        if self.closed:
            raise ConverterError("The close function cannot be called on a closed converter.")
        return b""
        self.closed = True

    # The below functions probably shouldn't be overridden by child classes
    def convert_string(self, s):
        """
        Converts a string sent by a caller. The sent string will be passed to the convert function.
        """
        if self.closed:
            raise ConverterError("The convert_string function cannot be called on a closed converter.")
        if type(s) is not bytes:
            raise TypeError(f"Only binary data (bytes) is supported, not {type(s)}")
        return self.convert(s)

    @classmethod
    def usage(cls):
        """
        Prints a description and usage information for the converter.
        """
        r = f"{cls.name}:\n{cls.description}\n"
        if len(cls.options) > 0:
            r += "\nOptions:\n"
            for o in cls.options:
                requirement = "required" if o.get("required", False) else "optional"
                r += f"  {o['name']}: {o['description']} ({requirement}):\n"
                for c in o["choices"]:
                    r += f"    {c['name']}: {c.get('description', '')}\n"
        return r

    def warning(self, warning_code, warning_description=""):
        """
        Add a conversion warning.
        Warnings should be used in the following cases:
        * An event that may indicate a problem has occured
        * It is still possible to convert the file.
        If the problem indicates with certainty that the file cannot be converted, an exception derived from ConverterException should be raised instead.

        Parameters:
            warning_code can be any string but is recommended to not contain spaces and be unique for each warning condition.
            Warning description: A string providing more information of the warning. This may contain a plain text description, file location, or similar.
        """
        self.warnings.append((self.name, warning_code, warning_description))

    def clear_warnings(self):
        self.warnings = []


class converter_chain(converter):
    """
    A class that chains multiple converters together. It otherwise acts as its own converter
    """

    def __init__(self, converters):
        self.source_format = converters[0].source_format
        self.output_format = converters[-1].output_format
        converter.__init__(self)
        self.converters = converters

    def convert(self, s):
        for c in self.converters:
            s = c.convert_string(s)
            if s is None:
                s = b""
            for warning_source, warning_code, warning_desc in c.warnings:
                self.warning(warning_code, warning_desc, warning_source)
        return s

    def close(self):
        r = b""
        for c in self.converters:
            r = c.close()
            for warning_source, warning_code, warning_desc in c.warnings:
                self.warning(warning_code, warning_desc, warning_source)
        return r

    def warning(self, warning_code, warning_desc, warning_source):
        # Pass through the original source. Don't identify the chain as the source.
        self.warnings.append((warning_source, warning_code, warning_desc))
