# XLIFF 2.0 Converter

Convert aligned multilingual text files to XLIFF 2.0 format with reference translations stored as metadata.

## Features

- Manual language code entry (MS LCID format: en-GB, de-DE, fr-FR, etc.)
- Convert aligned text to valid XLIFF 2.0
- Store reference translations as metadata (not matches)
- Batch processing support
- User-friendly Streamlit interface
- Compatible with Trados Studio and XLIFF validators

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app_simple.py
```

## Input Format

Text files with aligned translations separated by blank lines:

```
My first sentence is this.
Meine erste Satz lautet so.
Ma première phrase est celle-ci.

My second sentence looks like this.
Mein zweiter Satz sieht so aus.
Ma deuxième phrase ressemble à ceci.
```

## Output Format

XLIFF 2.0 files with:

- Source language in `<source>` elements
- Reference translations stored as metadata (`<mda:metadata>`)
- Ready for translation workflow
- Validates against XLIFF 2.0 specification

Example structure:

```xml
<unit id="1">
  <mda:metadata>
    <mda:metaGroup category="reference-translations">
      <mda:meta type="ref-de-DE">Meine erste Satz lautet so.</mda:meta>
      <mda:meta type="ref-fr-FR">Ma première phrase est celle-ci.</mda:meta>
    </mda:metaGroup>
  </mda:metadata>
  <segment id="1">
    <source>My first sentence is this.</source>
  </segment>
</unit>
```

## Workflow

1. Upload text file(s)
2. Parse files to detect number of languages
3. Enter language codes manually (e.g., en-GB, de-DE, fr-FR)
4. Select source language
5. Enter target language code
6. Choose output options (overwrite/rename/skip)
7. Convert to XLIFF 2.0

## Project Structure

```
xliff_converter/
├── app_simple.py           # Streamlit UI (simplified, no language detection)
├── core/
│   ├── text_parser.py      # Parse aligned text files
│   └── xliff_generator.py  # Generate XLIFF 2.0 with metadata
├── xliff20_parser.py       # Parse XLIFF 2.0 files (for main system)
├── requirements.txt        # Python dependencies (streamlit, lxml)
└── README.md              # This file
```

## Requirements

- Python 3.x
- streamlit
- lxml

## Notes

- Language codes must follow MS LCID format: xx-YY (e.g., en-GB, de-DE)
- All files in a batch use the same language configuration
- Reference translations are stored as metadata for use in translation/evaluation workflows
- Output files validate against XLIFF 2.0 specification
- Compatible with Trados Studio and other XLIFF 2.0 tools
