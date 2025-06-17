# XLIFF Tag and Placeholder Analyzer

A Python tool to analyse XLIFF translation files and verify tag/placeholder consistency between source and target segments. This tool is especially useful when translators haven't properly protected tags during translation, which can break applications when the translated files are deployed.

## Purpose

When translators work on XLIFF files without proper tag protection in their CAT tools, they often:
- Delete HTML/XML tags accidentally
- Modify tag names (e.g., `<button>` becomes `<Button>`)
- Leave placeholder variables incomplete (e.g., `{variable` missing the closing `}`)
- Add extra or incorrect tags

This tool quickly identifies these issues by comparing source and target segments for:
- **HTML/XML tags** (`<button>`, `</strong>`, `<link>`, etc.)
- **Single-brace placeholders** (`{query}`, `{renewalDate}`, etc.)
- **Double-brace placeholders** (`{{fileCount}}`, `{{totalSize}}`, etc.)

## Features

- **Accurate detection** of missing, malformed, or extra tags/placeholders
- **Detailed reporting** showing exactly what's wrong in each segment
- **Dual output**: Console display + formatted Markdown report
- **SDL Trados compatibility** using proper segment IDs
- **Professional reports** suitable for client delivery
- **Easy integration** into QA workflows

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/xliff-tag-analyzer.git
cd xliff-tag-analyzer
```

2. Make the script executable (optional):
```bash
chmod +x countUntaggedTags.py
```

## Usage

### Basic Usage

```bash
python countUntaggedTags.py your_file.sdlxliff
```

### Interactive Mode

If you run without arguments, the script will prompt for the file path:
```bash
python countUntaggedTags.py
# Enter the path to your XLIFF file: /path/to/your/file.sdlxliff
```

## Sample Output

### Console Output
```
XLIFF Tag and Placeholder Analysis Report
================================================================================
Segment ID   HTML     HTML     {}     {}     {{}}     {{}}     Issues
             Src      Tgt      Src    Tgt    Src      Tgt
--------------------------------------------------------------------------------
Segment 1        2        2        1      1      0        0        ✓
Segment 2        4        3        0      0      0        0        HTML
             Source: <button>Sign up to start earning</button> or <link>Login</li...
             Target: <Button Registriere dich</button> oder <lik>melde dich an</l...
             Missing HTML tags: <button>, <link>
             Extra HTML tags: <Button Registriere dich</button>, <lik>

Segment 4        2        2        1      0      0        0        {}
             Source: Renews <strong>{renewalDate}</strong>
             Target: Wird am <strong>{renewalDate</strong> verlängert
             Missing {} placeholders: {renewalDate}

--------------------------------------------------------------------------------
TOTALS       16       15       6      5      4        4
================================================================================
Total segments analyzed: 6
Segments with issues: 2
Accuracy rate: 66.7%
⚠️  Warning: 2 segment(s) have missing or malformed tags/placeholders!
```

### Markdown Report

The tool automatically generates a professional markdown report (`filename_tag_analysis_report.md`) with:
- Executive summary
- Detailed results table
- Problem segment breakdown
- Timestamp and file information

## What It Detects

### HTML/XML Tags
- Missing tags: `<button>` in source but not in target
- Malformed tags: `<button>` becomes `<Button` (wrong case, missing `>`)
- Extra tags: Additional tags not present in source
- Incomplete tags: `<strong>` without closing `</strong>`

### Single-Brace Placeholders `{}`
- Missing variables: `{query}` in source but not in target
- Incomplete variables: `{renewalDate` missing closing `}`
- Extra variables: Variables added in target that aren't in source

### Double-Brace Placeholders `{{}}`
- Framework variables: `{{fileCount}}`, `{{totalSize}}`, etc.
- Template placeholders used in many web frameworks
- Same validation as single-brace but for double-brace syntax

## Troubleshooting

### Common Issues

**"No segments found"**
- Ensure file is a valid XLIFF/SDLXLIFF format
- Check file encoding (should be UTF-8)

**"Tags not detected"**
- Verify the file hasn't been processed by a tool that strips tags
- Check that you're analyzing the correct version (unsaved changes in Trados Studio won't be reflected)

**"Namespace errors"**
- Some XLIFF variants use different namespaces
- The tool supports standard XLIFF 1.2 and SDL XLIFF formats

### Getting Help

1. Check that your XLIFF file is valid XML
2. Ensure you're using a supported XLIFF version (1.2)
3. Verify file permissions and encoding
4. Open an issue with sample data if problems persist

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

