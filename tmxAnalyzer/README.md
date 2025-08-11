# tmxAnalyzer

A rough guide of a Python tool for analysing TMX (Translation Memory eXchange) files to identify auto-translatable content, exact duplicates, and data quality issues.

## Purpose

This tool helps translation professionals and project managers understand the composition of their TMX files by identifying:

- Content that CAT tools like Trados Studio would consider auto-translatable
- Exact duplicate translation units that waste storage space
- Missing or empty target translations that need attention
- Overall translation memory quality metrics

## Features

### 📊 Content Analysis

- **Auto-translatable detection**: Identifies numbers, URLs, emails, proper names, codes, and other content
- **Duplicate identification**: Finds exact duplicate TU pairs (same source + same target)
- **Quality control**: Detects missing targets, empty segments, and malformed TUs
- **Language pair detection**: Automatically identifies source and target languages

### User Experience

- **Interactive file selection**: GUI file picker for easy TMX selection
- **Progress tracking**: Real-time progress updates for large files
- **Smart reporting**: Auto-saves reports with descriptive names in TMX directory
- **Universal compatibility**: Works with any bilingual TMX file from any CAT tool

### Detailed Reporting

- **Summary statistics**: High-level overview of file composition
- **Category breakdown**: Detailed examples for each auto-translatable type
- **Duplicate analysis**: Lists most frequent duplicates with TU numbers
- **Space savings calculation**: Shows potential file size reduction

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- tkinter (usually included with Python)
- No external dependencies required!

### Installation

1. Download the `tmx_analyzer.py` script
2. Place it in your desired directory
3. That's it! No pip installs needed.

### Usage

Simply run the script:

```bash
python tmx_analyzer.py
```

Then:

1. 📁 Select your TMX file using the file picker
2. ⏳ Wait for analysis to complete (progress shown)
3. 📄 Find your report automatically saved next to the TMX file

## 📊 Analysis Categories

### Auto-Translatable Content

- **Numbers Only**: `123`, `(1.32)`, `25-30%`
- **Mixed Alphanumeric Codes**: `HTML`, `PRE-WORK`, `MINDSET`
- **URLs**: `www.example.com`, `https://site.org`
- **Email Addresses**: `user@domain.com`
- **Proper Name Matches**: `John Smith` → `John Smith`
- **Dates**: `10/19/2016`, `March 15, 2023`
- **Currency**: `$100`, `€50`, `¥1000`
- **Measurements**: `15%`, `25kg`, `10cm`
- **Version Numbers**: `v2.1.3`, `360-degree`
- **Simple Punctuation**: `>>`, `...`, `!`

### Quality Issues

- **Missing Target TUV**: No target language section
- **Missing Segments**: Missing `<seg>` elements
- **Empty Content**: Blank source or target text
- **Exact Duplicates**: Identical source+target pairs

## 📈 Sample Report Output

```
================================================================================
TMX CONTENT ANALYSIS REPORT
================================================================================
TMX File: MyTranslations.tmx
Analysis Date: 2025-08-11 14:30:15
Language Pair: en-us → es-es

SUMMARY:
--------------------
Auto-Translatable TUs Found: 3,242
Exact Duplicate TU Pairs: 6,953
Total Duplicate Instances: 15,752
Missing/Empty Target Issues: 0

AUTO-TRANSLATABLE CONTENT BY CATEGORY:
---------------------------------------------
Mixed Alphanumeric Codes :  1,769 TUs
Proper Name Match        :    624 TUs
Url                      :    558 TUs
Numbers Only             :    160 TUs
[...]

DUPLICATE ANALYSIS INSIGHTS:
------------------------------
Total TUs analyzed: 159,429
Total redundant TU entries: 8,799
Space savings potential: 5.5% (8,799 TUs could be removed)
These exact duplicates can be safely removed to optimize TMX size.
Recommendation: Import into Trados Studio for automatic deduplication.
```

## Technical Details

### Supported TMX Formats

- ✅ Aiming for any bilingual TMX file
- ✅ TMX 1.4 specification
- ✅ Various CAT tool exports (Trados, memoQ, Déjà Vu, etc.)
- ✅ Different encodings (UTF-8, UTF-16, etc.)
- ✅ Large files (hopefully... only tested with 300k+ TUs)

### Language Support

- Auto-detects language pairs from TMX headers and TUV elements
- Handles various language code formats (`en-us`, `en_US`, `en`, etc.)
- Works with any language combination

### Performance

- Processes ~10,000 TUs per second on typical hardware
- Memory efficient for large files
- Progress updates every 10,000 TUs

## Report Files

Reports are automatically saved with descriptive names:

```
[TMX_FILENAME]_analysis_report_[TIMESTAMP].txt
```

Example: `MyTranslations_analysis_report_20250811_143052.txt`

## Use Cases

### For Translation Project Managers

- **Quality assessment**: Understand TMX composition before project start
- **Resource planning**: Estimate auto-translatable vs. human translation work
- **TMX optimization**: Identify cleanup opportunities
- **Sanity Checking**: explain where the missing TUs went in a Trados Studio import!

### For Translation Memory Managers

- **Deduplication planning**: Find redundant entries before import
- **Quality control**: Identify incomplete or problematic TUs
- **Storage optimization**: Calculate potential space savings

## Contributing

This tool is designed to be a practical utility for the translation industry. Contributions welcome for:

- Additional auto-translatable content patterns
- Support for multilingual TMX files
- Performance optimizations
- UI improvements

### File Requirements

- Valid TMX XML format - bilingual TMX only
- At least two TUV elements per TU
- Readable file encoding

## 🔗 Related Tools

This tool complements:

- **Trados Studio**: For actual auto-translation and deduplication
- **TMX editors**: For manual cleanup based on analysis results