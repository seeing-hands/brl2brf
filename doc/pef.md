# BRL2BRF: PEF
The PEF, Portable Embosser Format, file type 

## Notes for developers
If you just want to translate PEF files, it works the same way that other formats do. If you're interested in the details of the format, read on.
### Specifications
The PEF format is written as if it's specified, but all the links are broken. I've looked for archived versions of these documents, but if they were ever posted at the URLs they specify, they were not indexed by archives I know about.
* The specification document is supposed to be hosted at http://www.daisy.org/ns/2008/pef
* The paper namespace is supposed to be hosted at http://www.aph.org/ns/paper-dimensions/1.0 No archived version is known. It seems pretty self-explanatory.

### Why we only decode PEF right now
Getting Braille out of a PEF file is not too hard. Since all the formats we have can deal with raw Braille content, the output can be translated into any of the other supported output formats without asking the user to fill in lots of details. If they don't like the hard limit on paper sizes, they can use the reflow converter to change this.
Getting Braille into a PEF file requires knowing or at least guessing a bunch of details. The paper size, line length, lines per page, volume and section boundaries, and many other details need to be guessed. While we could take all these inputs and map them to options, that slows down the process. We could try to guess some of these, E.G. setting the line length to the maximum line length in the input, but that is a recipe for deciding that a file was meant to be formatted as one line per paragraph just because it wasn't reflowed before conversion. Since many programs that use PEF files can accept a BRF file as input and reflow it according to embosser settings, this may be something best left to them.