# XML v1 to XML v2 Namespace Checker for Trados Studio

This Python script identifies missing namespaces in XML v1 settings files used in Trados Studio prior to migrating to XML v2. The goal is to pinpoint any missing namespaces required by Trados Studio's 2024 CU1 version to prevent errors during migration and set up any necessary namespaces.

## Purpose
The script scans an XML settings file from Trados Studio's XML v1 format and reports any missing namespace declarations for prefixes found within XPath selectors. This is essential to avoid errors that can arise when migrating to XML v2 in Trados Studio 2024 CU1. Any missing namespaces need to be added to the configuration to ensure a smooth migration.

## Features
- **Reports Missing Namespaces**: The script lists any prefixes used within XPath selectors in the settings file that are missing associated namespace URIs.
- **Namespace Information**: Outputs the missing prefix and alerts the user that a URI setup is needed.

## Prerequisites
- Python 3.x
- XML file in XML v1 format, typically named as `.sdlftsettings`

## Usage

1. Clone this repository or download the script directly.
2. Run the script by executing:

    ```bash
    python find_missing_namespaces.py
    ```

3. When prompted, enter the full path to your Trados Studio XML settings file.

Example:
```plaintext
Please enter the path to the XML settings file: C:\path\to\your\file.sdlftsettings
```

4. The script will parse the file and output any missing namespace prefixes along with placeholders for URIs that need to be set up.

Example Output:
```plaintext
Missing namespace declarations found:
Prefix: drc
Uri: [MISSING URI]
```

## Troubleshooting
- **File Not Found**: Ensure the file path entered is correct and accessible.
- **Invalid XML**: If there is a parsing error, check that the XML file is well-formed.

## Contributing
If you find any bugs or have suggestions for improvement, please feel free to open an issue or submit a pull request.