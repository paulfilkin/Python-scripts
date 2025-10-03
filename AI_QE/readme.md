# XLIFF Quality Report Generator

A Python tool for analyzing translation quality evaluation data from SDLXLIFF files that have been through a "Smart Review" (requires an AI Essentials subscription) and generating comprehensive PDF reports with statistics, visualizations, and detailed segment breakdowns.

## Features

- **Batch Processing**: Analyze multiple XLIFF files in a single run
- **Comprehensive Reports**: Generate consolidated PDF reports with:
  - Executive summary with batch-level statistics
  - Individual file analysis with detailed metrics
  - Visual score distribution charts (pie/bar charts)
  - Issue categorization and breakdown
  - Segment-level details for quality issues
- **Smart Categorization**: Automatically categorizes quality issues (Accuracy, Grammar, Style, Terminology, Omission, etc.)
- **Flexible Output**: Customizable output folder location
- **Professional Layout**: Clean, color-coded PDF reports with tables and charts

## Requirements

```bash
pip install reportlab matplotlib
```

The script requires Python 3.6+ and the following libraries:

- `reportlab` - PDF generation
- `matplotlib` - Chart visualization
- Standard library: `xml.etree.ElementTree`, `pathlib`, `statistics`, `datetime`

## Usage

### Command Line

```bash
# Basic usage - will prompt for folder path
python xliff_quality_report.py

# With folder path argument
python xliff_quality_report.py /path/to/xliff/files

# With custom output folder
python xliff_quality_report.py /path/to/xliff/files custom_reports
```

### Interactive Mode

Run without arguments to use interactive prompts:

```bash
python xliff_quality_report.py
```

You'll be prompted to enter:

1. Path to folder containing XLIFF files
2. Output folder name (optional, defaults to 'reports')

## Input Requirements

- Files must have `.sdlxliff` extension
- Files must contain quality evaluation data with:
  - `tqe-score-1` values (typically 10 or 100)
  - `tqe-description-1` for issue descriptions (optional)
  - `tqe-model-1` for evaluation model info (optional)

## Output

The tool generates a `reports` folder (or custom named folder) containing:

- `quality_report.pdf` - Consolidated report with:
  - **Cover page** with generation date and file count
  - **Batch summary** with overall statistics across all files
  - **Individual file reports** with detailed analysis
  - **Charts** showing score distributions
  - **Category breakdowns** for quality issues
- Temporary chart images (`.png` files) used in the report

## Report Contents

### Batch Summary

- Overall totals across all files
- Best and worst performing files
- Weighted average scores
- Issue category breakdown
- Overall quality distribution chart

### Individual File Reports

Each file includes:

- File metadata (language pair, original filename)
- Summary statistics (total segments, score distribution)
- Issue category breakdown
- Score distribution visualization
- Detailed tables of segments requiring attention
- Sample of high-quality segments

## Quality Score Interpretation

The tool handles binary scoring systems:

- **100**: Good Quality
- **10**: Requires Attention

For non-binary systems, it provides full statistical analysis including mean, median, and standard deviation.

## Issue Categories

Automatically categorizes issues based on description keywords:

- **Accuracy**: Mistranslations, meaning errors
- **Grammar**: Case, agreement, syntax errors
- **Style**: Tone, register issues
- **Terminology**: Incorrect term usage
- **Omission**: Missing content
- **Other**: Unclassified issues

### Example (see the attached fr-FR folder)

View the [sample quality report PDF](./fr-FR/reports/quality_report.pdf) generated from the example files.

Given a folder structure like this:

```
fr-FR/
├── bees_EN.txt.sdlxliff
├── butterflowy_EN.txt.sdlxliff
└── dogs_EN.txt.sdlxliff
```

Run the script:

```bash
python xliff_quality_report.py fr-FR
```

The tool will process all `.sdlxliff` files and generate:

```
fr-FR/
├── bees_EN.txt.sdlxliff
├── butterflowy_EN.txt.sdlxliff
├── dogs_EN.txt.sdlxliff
└── reports/
    ├── quality_report.pdf          # Main consolidated report
    ├── chart_0.png                 # Distribution chart for file 1
    ├── chart_1.png                 # Distribution chart for file 2
    ├── chart_2.png                 # Distribution chart for file 3
    └── overall_distribution.png    # Batch-level distribution chart
```

## Error Handling

- Skips files with no quality data
- Continues processing if individual files fail
- Provides informative error messages
- Validates input paths

## Customization

Key functions that can be modified:

- `categorise_issue()`: Adjust issue categorization logic
- `make_score_distribution_chart()`: Customize chart appearance
- `create_consolidated_report()`: Modify report layout and styling

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.
