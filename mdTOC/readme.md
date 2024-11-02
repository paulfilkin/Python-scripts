# Markdown TOC Generator

This Python script generates a Table of Contents (TOC) based on the headings within a Markdown (`.md`) file. It is particularly useful if the Markdown tools you're using do not support custom TOC features. The generated TOC provides anchor links to each heading, making it easy to navigate long documents.

## Features

- **Automated TOC Creation**: The script scans all headers (from H1 to H6) in the specified Markdown file and generates a TOC.
- **Anchor Links**: Converts headings into anchor links following Markdown conventions by making them lowercase, hyphenating spaces, and removing punctuation.
- **Header Modification**: Optionally adjusts headers to include explicit IDs (e.g., `{#custom-id}`).
- **Direct File Update**: Writes the TOC along with the modified content back to the original file, excluding any previous `[TOC]` tag.

## Prerequisites

- Python 3.x
- Basic understanding of Markdown syntax

## Usage

1. Place the script in the same directory as the Markdown file you want to update, or provide the file path.
2. Update the last line in the script to point to your Markdown file, e.g., `generate_toc('yourfile.md')`.
3. Run the script with:

   ```bash
   python script_name.py
   ```

   Replace `script_name.py` with the actual name of your script file.

## Example

Given a sample Markdown file (`input.md`) with the following content:

```markdown
# Main Heading

## Subheading 1

### Subheading 1.1

## Subheading 2
```

Running this script will generate and insert a TOC as shown below:

```markdown
## Table of Contents

- [Main Heading](#main-heading)
  - [Subheading 1](#subheading-1)
    - [Subheading 1.1](#subheading-11)
  - [Subheading 2](#subheading-2)

# Main Heading

## Subheading 1

### Subheading 1.1

## Subheading 2
```

## Sample File

A sample file (`input.md`) is provided in this repository for testing purposes. This file contains sample headings to help you see how the TOC is generated and inserted.

## Limitations

- The script does not preserve any existing TOC; it rewrites it each time it runs.
- It assumes Markdown files follow standard heading syntax (`#` for headings), up to H6.

## Notes

- Be sure to **back up your file** before running the script, as it overwrites the original file with the new TOC added.