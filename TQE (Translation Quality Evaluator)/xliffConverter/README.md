1. # XLIFF 2.0 Converter

   Convert aligned multilingual text files to XLIFF 2.0 format with reference translations, and populate target languages from translation files.

   ## Features

   - Auto-detect languages with MS LCID format (en-GB, de-DE, fr-FR, etc.)
   - Convert aligned text to XLIFF 2.0
   - Store reference translations as metadata
   - Populate target elements from translation text files
   - Batch processing support
   - User-friendly Streamlit interface

   ## Installation

   ```bash
   pip install -r requirements.txt
   ```

   ## Usage

   ```bash
   streamlit run app.py
   ```

   ## Tab 1: Text to XLIFF

   Convert aligned multilingual text files into XLIFF 2.0 format.

   ### Input Format

   Text files with aligned translations separated by blank lines:

   ```
   My first sentence is this.
   Meine erste Satz lautet so.
   Ma première phrase est celle-ci.
   
   My second sentence looks like this.
   Mein zweiter Satz sieht so aus.
   Ma deuxième phrase ressemble à ceci.
   ```

   Or prefixed format:

   ```
   EN: My first sentence is this.
   DE: Meine erste Satz lautet so.
   FR: Ma première phrase est celle-ci.
   
   EN: My second sentence looks like this.
   DE: Mein zweiter Satz sieht so aus.
   FR: Ma deuxième phrase ressemble à ceci.
   ```

   ### Output Format

   XLIFF 2.0 files with:

   - Source language in `<source>` elements
   - Other languages as reference translations in metadata (`<mda:meta>`)
   - Ready for translation workflow

   ### Workflow

   1. Upload text file(s)
   2. Review detected languages
   3. Confirm/edit language codes (MS LCID format)
   4. Select source language
   5. Select target language
   6. Choose output options
   7. Convert to XLIFF 2.0

   ## Tab 2: Populate Targets

   Add translations from text files into existing XLIFF target elements. Supports batch processing with multiple translation files.

   ### Input

   - 1 XLIFF file (from converter, with source and reference translations)
   - 1 or more TXT files with translations (one translation per line, matching XLIFF segment order)

   ### Workflow

   1. Upload XLIFF file
   2. Upload translation text file(s)
   3. Enter target language code (MS LCID format, e.g., tr-TR)
   4. Review validation (segment counts must match line counts)
   5. Set output filename suffix
   6. Click "Populate All Targets"

   ### Output

   One populated XLIFF file per translation file:

   - Target language (`trgLang`) attribute updated
   - `<target>` elements inserted with translations
   - All reference translations preserved

   ### Example

   Upload:

   - `source_en-ja-pl.xlf` (500 segments)
   - `turkish_human.txt` (500 lines)
   - `turkish_machine.txt` (500 lines)

   Set target language: `tr-TR`

   Output:

   - `turkish_human_populated.xlf` (trgLang="tr-TR", 500 targets)
   - `turkish_machine_populated.xlf` (trgLang="tr-TR", 500 targets)

   ## Project Structure

   ```
   xliffConverter/
   ├── core/
   │   ├── text_parser.py        # Text file parsing (grouped/prefixed formats)
   │   ├── xliff_generator.py    # XLIFF 2.2 generation
   │   └── target_populator.py   # Target element population
   ├── app.py                    # Streamlit UI
   ├── requirements.txt
   └── README.md
   ```

   ## Licence

   This repository is released under **The Unlicense**, placing the contents in the public domain.
