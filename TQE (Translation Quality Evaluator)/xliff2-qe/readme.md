# XLIFF 2.0 Translation Quality Evaluation System

An LLM-powered quality evaluation tool for XLIFF 2.0 translation files with support for translation generation and comprehensive PDF reporting.

## Features

- **Three Operation Modes:**
  - **Translate (no context)**: Generate translations using source text only
  - **Translate (with context)**: Generate translations using reference translations from other languages as context
  - **Evaluate**: Comprehensive 4-dimensional quality assessment of existing translations
- **Batch Processing**: Upload and process multiple XLIFF files simultaneously
- **Advanced Evaluation**: 4-dimensional scoring (Accuracy, Fluency, Style, Context Coherence)
- **Professional Reports**: Detailed PDF reports with charts, issue analysis, and actionable recommendations
- **Async Processing**: High-performance concurrent API calls (50+ simultaneous requests)
- **Context-Aware**: Evaluates translations within surrounding segment context
- **Multiple Content Types**: Specialised evaluation templates for general, technical, marketing, legal, and UI content

## Requirements

- Python 3.8+
- OpenAI API key
- Required packages (see `requirements.txt`)

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root (if you don't the application will request one):

```bash
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### XLIFF 2.0 File Format

The system expects XLIFF 2.0 files with the following structure:

```xml
<?xml version='1.0' encoding='utf-8'?>
<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" 
       xmlns:mda="urn:oasis:names:tc:xliff:metadata:2.0" 
       version="2.0" srcLang="en-GB" trgLang="ro-RO">
  <file id="..." original="...">
    <unit id="1">
      <mda:metadata>
        <mda:metaGroup category="reference-translations">
          <mda:meta type="ref-de-DE">German translation</mda:meta>
          <mda:meta type="ref-fr-FR">French translation</mda:meta>
        </mda:metaGroup>
      </mda:metadata>
      <segment id="1">
        <source>Source text</source>
        <target>Target text (required for evaluation)</target>
      </segment>
    </unit>
  </file>
</xliff>
```

- One source language
- One target language (may be empty for translation operations)
- Reference translations stored in metadata as `ref-XX-XX`

### Operations

#### 1. Translate (no context)

Generates translations using only the source text. Suitable for initial translations or when no reference translations are available.

**Output**: Modified XLIFF file with `<target>` elements populated

#### 2. Translate (with context)

Uses reference translations from other languages to improve translation quality and consistency. The LLM sees how the source text was translated into other languages to better understand intended meaning.

**Output**: Modified XLIFF file with context-aware `<target>` elements

#### 3. Evaluate

Performs comprehensive quality evaluation of existing target translations using a 4-dimensional scoring system:

- **Accuracy (40%)**: Semantic fidelity, no omissions/additions, meaning preservation
- **Fluency (25%)**: Native-speaker naturalness, grammar, readability
- **Style (20%)**: Register, tone, terminology consistency, cultural appropriateness
- **Context Coherence (15%)**: Consistency with surrounding segments, proper reference resolution

**Output**:

- JSON file with detailed segment-by-segment results
- Professional PDF report with charts, statistics, and recommendations

### Configuration

**Sidebar Options:**

- **Model**: Choose between gpt-5-mini (fastest) or gpt-4o
- **Content Type**: Select evaluation template (general, technical, marketing, legal, UI)
- **Context Window**: Number of surrounding segments to consider (0-10)

### Output Files

All outputs are saved to the `./outputs/` directory:

- **Translations**: `filename_translated.xlf` or `filename_translated_context.xlf`
- **Evaluations**: `filename_evaluation.json` and `filename_evaluation.pdf`

## Project Structure

```
xliff2-qe/
├── core/
│   ├── xliff2_handler.py      # XLIFF 2.0 parsing and manipulation
│   ├── async_llm_provider.py  # Async OpenAI integration
│   ├── api_cache.py           # API credential caching
│   └── config.py              # Configuration management
├── prompts/
│   └── templates.py           # Content-specific evaluation templates
├── reports/
│   └── enhanced_report.py     # PDF report generation
├── app.py                     # Streamlit UI
├── requirements.txt
├── .env.template
└── README.md
```

## PDF Reports

Evaluation reports include:

- **Executive Summary**: Overall statistics and quality assessment
- **Issue Distribution**: Breakdown of problem types and frequencies
- **Score Distribution**: Histogram showing quality spread
- **Quality Dimensions**: Radar chart of 4-dimensional scores
- **Detailed Results**:
  - Segments requiring attention (lowest scores with explanations)
  - Excellent quality samples (highest scores with source/target text)

## Performance

- **Concurrent Processing**: 50 simultaneous API requests by default
- **Rate Limiting**: Automatic retry with exponential backoff
- **Error Handling**: Individual segment failures don't stop batch processing
- **Token Optimisation**: Adaptive token limits based on segment complexity

## Data Privacy and Licensing

### About Streamlit and Data Handling

This project is built using the open-source **Streamlit** Python library (licensed under Apache 2.0). The application is **not** deployed on Streamlit Community Cloud. It runs entirely on the user's own machine using:

```bash
streamlit run app.py
```

#### Local Execution

When run locally, all data processed by the application (including files uploaded via the Streamlit interface) is handled entirely on the user's own machine. No data is sent to Streamlit or Snowflake, and the Streamlit Terms of Use do not apply to local execution of the library. The Streamlit software itself does not transmit uploaded content, text, or file data to any external service.

Only the user's own system is involved in processing, unless external APIs (e.g., OpenAI) are explicitly configured by the user.

#### UI Customisation

This application hides certain default Streamlit interface elements (such as the main menu and header) using Streamlit's documented configuration options and CSS. These changes affect only the appearance of the application and do not modify, redistribute, or interfere with the Streamlit Services or platform.

### Data Privacy Notice for Users

- When you run this app locally, all processing happens on your own computer
- No data is uploaded to Streamlit, Snowflake, or any other external service unless you configure and supply your own external API key (e.g., OpenAI API key)
- The developer of this application does not collect, receive, or have access to any data processed on your machine
- **OpenAI API**: If you use OpenAI's API, your data is subject to [OpenAI's API data usage policies](https://openai.com/policies/api-data-usage-policies)

### Licence

This repository is released under **The Unlicense**, placing the contents in the public domain. This licence applies only to the source code in this repository.

It does **not** apply to:

- the Streamlit software,
- its dependencies,
- or any third-party APIs or services used with this project, all of which remain subject to their own licences and terms.

## Contributing

This project is in the public domain. Feel free to use, modify, and distribute as you see fit.

## Support

For issues or questions, please open an issue on GitHub.

------

**Note**: This is a quality evaluation tool. It does not replace human translators or professional translation quality assurance, but rather serves as an automated first-pass analysis to identify potential issues and areas requiring attention.