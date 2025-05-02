# XLIFF Source-to-Target Copy Scripts Documentation

This document describes two Python scripts for processing XLIFF (`.xlf`) files to copy the contents of `<source>` elements to `<target>` elements. The scripts use the `lxml` library to handle XML processing and are designed for XLIFF files with the `urn:oasis:names:tc:xliff:document:1.2` namespace and optional `ispring` custom namespace.

## Script 1: Single File Processing

### Overview
This script processes a single XLIFF file, copying the content of each `<source>` element to a corresponding `<target>` element. If a `<target>` element exists, it is updated; if not, a new one is created with `state="new"`. The output is written to a new file with a `t_` prefix (e.g., `input.xlf` becomes `t_input.xlf`).

### Features
- Processes one `.xlf` file at a time.
- Preserves the original file and creates a new output file.
- Handles nested elements (e.g., `<g>` tags) using `copy.deepcopy` for accurate copying.
- Supports XLIFF namespace and iSpring custom namespace.
- Validates input file existence and `.xlf` extension.

### Usage
1. Ensure `lxml` is installed: `pip install lxml`
2. Run the script: `python xliff_copy_source_to_target.py`
3. Enter the path to the XLIFF file when prompted.
4. Check the output file (prefixed with `t_`) in the same directory as the input file.

## Script 2: Folder-Based Recursive Processing with Backup

### Overview
This enhanced script processes all XLIFF files in a specified folder and its subfolders recursively. It copies `<source>` content to `<target>` elements, overwriting the original files. Before processing, it creates a ZIP backup of the entire folder to preserve the original files and folder structure.

### Features
- Recursively processes all `.xlf` files in a folder and its subfolders.
- Overwrites original files with updated content.
- Creates a timestamped ZIP backup of the entire folder before processing.
- Handles errors gracefully, continuing with other files if one fails.
- Provides detailed feedback and a summary of processed files and `<target>` elements.
- Uses the same core XLIFF processing logic as Script 1 for consistency.

### Usage
1. Ensure `lxml` is installed: `pip install lxml`
2. Run the script: `python xliff_copy_source_to_target_folder.py`
3. Enter the path to the folder containing XLIFF files when prompted.
4. Review the console output for processing details and the backup location.
5. Check the original files (now updated) and the ZIP backup in the parent directory of the input folder.

## Common Notes
- **Dependencies**: Both scripts require the `lxml` library (`pip install lxml`). Script 2 also uses standard Python libraries (`pathlib`, `zipfile`, `os`, `datetime`).
- **XLIFF Structure**: The scripts assume XLIFF files use the `urn:oasis:names:tc:xliff:document:1.2` namespace and may include the `http://ispringsolutions.com/custom-xliff` namespace for iSpring elements.
- **Error Handling**: Both scripts validate input paths. Script 2 includes additional error handling for individual file processing to ensure robustness when processing multiple files.
- **Output**: Script 1 creates new files with a `t_` prefix, while Script 2 overwrites original files after creating a ZIP backup.

## Example XLIFF File
Both scripts are designed to handle XLIFF files with structures like this:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<xliff xmlns="urn:oasis:names:tc:xliff:document:1.2"
       xmlns:ispring="http://ispringsolutions.com/custom-xliff"
       version="1.2">
  <file datatype="x-is-ispring-presentation" source-language="nb">
    <body>
      <group id="presentation.slides">
        <trans-unit id="slide1.shapes.textbox1.text">
          <source>
            <g ctype="x-is-par" id="p0">
              <g ctype="x-is-run" id="p0_r0" ispringstart-data="d0">Leksjon 1 - Innledning</g>
            </g>
          </source>
          <target/>
        </trans-unit>
      </group>
    </body>
  </file>
</xliff>
```

The scripts copy the `<source>` content (including nested `<g>` elements) to the `<target>` element, resulting in:
```xml
<target state="new">
  <g ctype="x-is-par" id="p0">
    <g ctype="x-is-run" id="p0_r0" ispringstart-data="d0">Leksjon 1 - Innledning</g>
  </g>
</target>
```

## Choosing the Right Script
- Use **Script 1** for processing a single XLIFF file when you want to preserve the original and create a new output file.
- Use **Script 2** for batch processing multiple XLIFF files in a folder structure, with the safety of a ZIP backup and the convenience of overwriting originals.
