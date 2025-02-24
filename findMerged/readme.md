# Identify Merged Segments in SDLXLIFF Files

## Overview

This script processes SDLXLIFF files to identify merged segments, such as `MergedParagraph` and `MergedSegment`. It scans a user-specified folder for SDLXLIFF files and extracts relevant information about merged segments, including the segment ID, source text, and merge type.

## Features

- Automatically scans all `.sdlxliff` files in a given folder.
- Detects segments marked as **MergedParagraph** or **MergedSegment**.
- Extracts and displays:
  - **Segment ID**
  - **Source Text**
  - **Merge Type**
  - **Filename**
- Outputs results in a readable format for easy review.

## Installation

1. Ensure you have Python installed (version 3.6+ recommended).
2. Clone this repository or download the script:
   ```sh
   git clone https://github.com/yourusername/sdlxliff-merged-segments.git
   cd sdlxliff-merged-segments
   ```
3. No additional dependencies are required as the script uses Python's built-in libraries.

## Usage

1. Run the script:
   ```sh
   python identify_merged_segments.py
   ```
2. Enter the path to the folder containing SDLXLIFF files when prompted.
3. The script will scan the files and display merged segments.

## Example Output

```
Please enter the folder path containing sdlxliff files: c:\Users\someuser\somepathtothefolder\

File: 02 - merged.xlsx.sdlxliff
Segment #2:
Source: Parameter Specification
Merge Type: MergedParagraph
--------------------------------------------------
File: 02 - merged.xlsx.sdlxliff
Segment #7:
Source: 50 Hz Capacity
Merge Type: MergedParagraph
--------------------------------------------------
File: 04 - merged.docx.sdlxliff
Segment #49:
Source: The Green Future Wind Farm is a sustainable project that aligns with global climate goals. By implementing robust mitigation measures, the project aims to minimise environmental impact while maximising clean energy production.
Merge Type: MergedSegment
--------------------------------------------------
```

## Error Handling

- If an invalid folder is entered, the script exits silently.
- If an SDLXLIFF file is not properly formatted, it is skipped.
- If no merged segments are found, no output is shown.

## Contributing

Feel free to submit issues or pull requests for improvements.

```