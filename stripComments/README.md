# stripComments (SDLXLIFF Files)

This Python script removes comments from SDLXLIFF files (used in Trados Studio projects) and generates a PDF log of all removed comments. It’s designed to process files within a specified Studio project’s target language folder, `de-DE` for example, and save the log alongside the `.sdlproj` file.

## Features
- Removes file-level `<sdl:cmt>` comments from the `<header>` section.
- Removes segment-level `<mrk mtype="x-sdl-comment">` comments from `<target>` elements.
- Creates backups of original SDLXLIFF files (`.bak` extension).
- Logs all removed comments in a timestamped PDF file (e.g., `comments_removed_log_20250321_123456.pdf`).
- Wraps text in PDF table headers and comments for readability.
- Saves the PDF in the same directory as the `.sdlproj` file.

## Requirements
- **Python 3.x** (tested with Python 3.12)
- **Libraries**:
  - `lxml`: For parsing and modifying SDLXLIFF XML files.
  - `reportlab`: For generating the PDF log.
- Install dependencies via pip:
  ```bash
  pip install lxml reportlab

## Usage
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/sdlxliff-comment-stripper.git
   cd sdlxliff-comment-stripper
   ```

2. **Run the Script**:
   ```bash
   python stripComments.py
   ```
   - When prompted, enter the full path to your `.sdlproj` file (e.g., `C:\Users\[USERNAME]\OneDrive\Documents\Studio 2024\Projects\PS001_Package\PS_001.sdlproj`).

3. **What Happens**:
   
   - The script locates all `.sdlxliff` files in the `de-DE` subfolder.
   - Backups are created (e.g., `file.sdlxliff.bak`).
   - Comments are removed from each file.
   - A PDF log is generated in the same folder as the `.sdlproj` file.
   
4. **Output**:
   - **Modified Files**: SDLXLIFF files in `de-DE` with comments stripped.
   - **Backup Files**: Original files saved with `.bak` extension in `de-DE`.
   - **PDF Log**: e.g., `C:\path\to\project\comments_removed_log_20250321_123456.pdf`, containing a table with columns:
     - `Filename`
     - `Segment Number` (or "N/A" for file-level comments)
     - `Comment` (wrapped text)
     - `User`

## Example Terminal Output
```
Backup created: c:\Users\paul\...\de-DE\butterlowy.txt.sdlxliff.bak
Processing c:\Users\paul\...\de-DE\butterlowy.txt.sdlxliff
Root tag: {urn:oasis:names:tc:xliff:document:1.2}xliff
Found file-level comment in header: <sdl:cmt ... id="d84bb395-..."/>
Found 22 <target> tags
Found segment-level comment in target: <mrk ... sdl:cid="c0ad6bc3-...">Deutschen </mrk>...
Total comments removed from c:\Users\paul\...\de-DE\butterlowy.txt.sdlxliff: 6
Comments removed, original file updated: c:\Users\paul\...\de-DE\butterlowy.txt.sdlxliff
...
Attempting to generate PDF: c:\Users\paul\...\PS001_Package\comments_removed_log_20250321_123456.pdf
All removed comments logged to: c:\Users\paul\...\PS001_Package\comments_removed_log_20250321_123456.pdf
PDF file confirmed at: c:\Users\paul\...\PS001_Package\comments_removed_log_20250321_123456.pdf
Processing complete.
To reinstate originals, rename the .bak files back to .sdlxliff (e.g., remove the .bak extension).
```

## PDF Log Example
| Filename                | Segment Number | Comment                                   | User |
| ----------------------- | -------------- | ----------------------------------------- | ---- |
| butterlowy.txt.sdlxliff | N/A            | whole file                                | paul |
| butterlowy.txt.sdlxliff | 3              | Deutschen                                 | paul |
| gypsyking.txt.sdlxliff  | 9              | „Es gibt also einen Typen, der wichtig... | paul |

## Notes
- **Restoring Originals**: Rename `.bak` files back to `.sdlxliff` to revert changes.
- **Target Folder**: Hardcoded to `de-DE`. Modify `target_folder` in the script for other languages.
- **Error Handling**: Checks for `reportlab` installation and validates the `.sdlproj` path.
- **Dependencies**: Ensure `reportlab` and `lxml` are installed, or the script will exit with an error message.

## Contributing
Feel free to fork this repository, submit issues, or send pull requests for enhancements (e.g., support for multiple language folders, custom output formats).

## Acknowledgments
Built with help from Grok (xAI) for Trados Studio users needing a clean way to strip and log comments.