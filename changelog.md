# BRL2BRF Release History
For more information, see the readme.md file or the project page at [https://github.com/seeing-hands/brl2brf]
## Version 1.0.1
* Changes
    * Previously, BRF files were generated with Unix line breaks (\n). Some BRF files use Windows line breaks instead, and as far as we can tell, those files are handled correctly by all systems. Since no specification exists, we have changed the converter to use Windows line breaks for BRF files.
* Bug fixes
    * Fixed a bug that could fail to get the converter during single file conversion

## Version 1.0.0
* First release
