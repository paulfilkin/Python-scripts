# Excel Translation Merger

## Overview
This Python script merges translation data from multiple Excel files into a single output file. It processes files in a specified folder, extracting source and target texts, and consolidates them into a merged Excel file.

## Features
- Select a folder containing Excel files via a graphical prompt.
- Specify a target language label for processing.
- Automatically detects and processes files exported using the **Export to Excel** plugin from the [RWS AppStore](https://appstore.rws.com/Plugin/27).
- Extracts the `Source text` and `Target text` columns.
- Merges data from all found files into a single `Merged_Translations.xlsx` file.

## Prerequisites
Ensure you have the following dependencies installed before running the script:

- Python 3.x
- Required Python packages:
  ```sh
  pip install pandas openpyxl
  ```
  
- `tkinter` (comes pre-installed with Python on most systems)

## Usage
1. Run the script:
   ```sh
   python script.py
   ```
2. Select the folder containing the Excel files when prompted.
3. Enter the target language label (e.g., `fr-FR`, `de-DE`).
4. The script will process matching files and generate a `Merged_Translations.xlsx` file in the same folder.

## File Naming Convention
The script looks for Excel files named in the format:
```
Generated_01 - Filename.Preview.xlsx
Generated_02 - Filename.Preview.xlsx
...
Generated_11 - Filename.Preview.xlsx
```
These files are exported from Trados Studio using the **Export to Excel** plugin. The original SDLXLIFF files would have had a corresponding naming convention, such as:
```
01 - Filename.sdlxliff
```
The exported Excel files are stored in the target language folder for each language in the Trados Studio project, named according to language codes (e.g., `de-DE`, `es-ES`).

## Output
- The merged Excel file (`Merged_Translations.xlsx`) will contain two columns:
  - `en-US`: Source text
  - `<target_label>`: Target text (based on user input)

## Possible Enhancements
If interested, the script could be enhanced to:
- Prompt for the `.sdlproj` file.
- Automatically process all language folders based on the languages identified in the `.sdlproj`.
- Merge all languages into a single Excel file for creating a multilingual TMX.
- Extend functionality to generate a TMX file directly from the merged data.

## Error Handling
- If no folder is selected, the script exits.
- If a file is missing or has incorrect columns, it is skipped with an error message.
- Any unexpected errors are displayed in the console.