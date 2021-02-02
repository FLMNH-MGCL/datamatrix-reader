# DataMatrix-Reader

Locate and decode datamatrix information from specimen images, created for the Digitization Department of the McGuire Center for Lepidoptera at the Florida Museum of Natural History. Given a collection of specimen images, the program will decode the datamatrix inside each image and rename / sort them according to a predefined, standardized naming scheme. Successful reads and edits, as well as failures, will be logged accordingly.

The are currently two versions of this program: one written in Python and a port over to Rust. They both serve the same purpose and may be used somewhat interchangeably. With Rust, commandline arguments will be used as opposed to a TUI to handle input during runtime. **The Rust variant is more current and performant.**

### Installation and Usage

This is only compatible with **Linux and MacOS systems**. For both variants, you will need `zbar` and `dmtx-utils` installed on your system. To run the Rust version, be sure to install the correct [Rust](https://www.rust-lang.org/) version for your system, and the same goes for running the [Python](https://www.python.org/downloads/) version.

Installation of `zbar` and `dmtx-utils` for Linux will depend on your distribution. For MacOS, you may use [Homebrew](https://docs.brew.sh/Installation) for convenience. Command Line Tools for Xcode will be an additional requirement on MacOS to install the necessary dependencies. You may type and enter the `git` command in your terminal and (assuming you have not installed git manually) you will be prompted to install the tool set. Once installed, the procedure would look like:

```
$ brew install dmtx-utils
$ brew install zbar
$ git clone <git_url>
$ cd datamatrix-reader
$ python3 python/dm_reader.py
OR
$ cd rust
$ cargo run --release -- --help
$ cargo run --release -- [options] [flags]
```

This program's intended use is for the FLMNH, and as such the file naming scheme is specific. If this were to be adapted to a different project the renaming would need to be refactored in order to suit the new needs. In the Rust variant, this would not be too large a task, since it uses mostly regexes and a few string replacements (whitespace replaced with underscores). For example, the regex used to filter irrelevant text after decoding the datamatrix is:

`r"(.*?)MGCL\s?[0-9]{7,8}"`

If your institution had a datamatrix data convention of `XYZ ###` or `XYZ ####`, you could instead use

`r"(.*?)XYZ\s?[0-9]{3,4}"`

And remove the matching group to expose the targeted data

### References
