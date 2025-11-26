# XLIFF 2.0 Translation Quality Evaluation System

An LLM-powered quality evaluation tool for XLIFF 2.0 translation files with support for translation generation, comprehensive PDF reporting, and cross-language comparative analysis.

## Features

- **Three Operation Modes:**
  - **Translate (no context)**: Generate translations using source text only
  - **Translate (with context)**: Generate translations using reference translations from other languages as context
  - **Evaluate**: Comprehensive 4-dimensional quality assessment of existing translations
- **Cross-Language Analysis**: Compare evaluation results across multiple languages and translation sources (MT, AI, Human)
- **Batch Processing**: Upload and process multiple XLIFF files simultaneously
- **Sampling**: Configurable sampling strategies for cost-effective evaluation of large files
- **Advanced Evaluation**: 4-dimensional scoring (Accuracy, Fluency, Style, Context Coherence)
- **Professional Reports**: Detailed PDF reports with charts, issue analysis, and actionable recommendations
- **Comparative Reports**: Cross-language PDF reports with exportable chart images for presentations
- **API Inspector**: Transparency feature showing sample API requests and responses
- **CJK Support**: Full Chinese, Japanese, and Korean character support in PDF reports
- **Async Processing**: High-performance concurrent API calls with configurable rate limiting
- **Reliability Features**: Response validation, automatic retries, and clear failure markers
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

1. Create a `.env` file in the project root (if you don't the application will request one):

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

- JSON file with detailed segment-by-segment results (includes metadata and sampling info)
- Professional PDF report with charts, statistics, and recommendations

### Configuration

**Sidebar Options:**

- **Clear All & Start Fresh**: Reset button to clear all session state and start clean
- **Model**: Choose between gpt-5-mini (fastest), gpt-5, or gpt-4o
- **Content Type**: Select evaluation template (general, technical, marketing, legal, UI)
- **Context Window**: Number of surrounding segments to consider (0-10)
- **API Rate Limiting**:
  - **Requests per second** (1-50): Control API call rate to prevent rate limiting
  - **Max concurrent requests** (5-50): Limit simultaneous API calls for reliability
- **Report Settings**:
  - **Attention threshold**: Score below which segments appear in "Segments Requiring Attention"
- **Sampling**: Configure segment sampling for cost-effective processing (see Sampling section)

**Rate Limiting Recommendations:**

- **Maximum Reliability** (slower): 5-10 req/sec, 10-15 concurrent
- **Balanced** (recommended): 10-15 req/sec, 20-25 concurrent
- **Maximum Speed** (less reliable): 20-30 req/sec, 30-40 concurrent

### Sampling

For large files or when full evaluation isn't practical due to time or budget constraints, sampling allows evaluation of a representative subset of segments.

**Predefined Strategies:**

| Strategy          | Percentage   | Use Case                                        |
| ----------------- | ------------ | ----------------------------------------------- |
| None (100%)       | 100%         | Small files or when full evaluation is required |
| Quick check (10%) | 10%          | Large projects with known-quality vendor        |
| Standard (15%)    | 15%          | New vendor, new domain, or medium risk          |
| Thorough (20%)    | 20%          | High risk or unknown quality                    |
| Custom            | User-defined | Specific requirements                           |

**Additional Options:**

- **Minimum sample size** (default: 30): Ensures adequate sample even for small percentages
- **Fixed seed**: Enable reproducible sampling - same segments selected each run

**How Sampling Works:**

- For translation operations: Samples from all segments before processing
- For evaluation: Samples from valid segments only (after filtering failed/empty translations)
- Context for evaluation still uses full segment list (proper surrounding context preserved)
- Original segment order maintained in sample
- Sampling metadata included in JSON output

**Note**: For regulated or safety-critical content, full evaluation (None/100%) is recommended.

### Cross-Language Analysis

The **Cross-Language Analysis** tab allows comparison of evaluation results across multiple languages and translation sources. This is useful for comparing MT vs AI vs Human translation quality, or analysing quality variations across different target languages.

**Workflow:**

1. Run evaluations in the Processing tab for different languages/translation sources
2. Collect the JSON files from the `outputs` folder
3. Upload them to the Cross-Language Analysis tab
4. Tag each file with language code and source type (if not auto-detected)
5. Generate comparative report

**Auto-Detection:**

The system attempts to detect language and source type from filenames:

- Language hints: `turkish`, `german`, `french`, etc. → corresponding locale codes
- Source hints: `-HT`, `-MT`, `-AI`, `-MLT`, `GPT` → corresponding source types

**Recommended naming**: `Turkish-MT_evaluation.json`, `German_AI_evaluation.json`

**Generated Charts:**

1. **Overall Score Comparison**: Horizontal bar chart comparing average scores across all evaluations
2. **Clustered Comparison**: Grouped bar chart comparing source types (MT/AI/HT) per language
3. **Issue Category Breakdown**: Distribution of issue types by evaluation
4. **Quality Dimensions Radar**: Overlaid radar charts comparing all 4 dimensions
5. **Segments Needing Review**: Percentage of segments scoring below threshold

**Output:**

- PDF report (landscape A4) with summary table and all charts
- Individual PNG files for each chart (for use in presentations)

### API Inspector

The **API Inspector** tab provides transparency into the API calls being made during processing. After running any operation, switch to this tab to see:

- **Request details**: Model, token limits, system message, and full user prompt
- **Response details**: Token usage statistics, raw API response, and parsed evaluation
- **Per-operation capture**: Separate views for each operation type (Translate no context, Translate with context, Evaluate)

This feature helps with:

- Understanding how prompts are constructed
- Debugging unexpected evaluation results
- Verifying correct template usage
- Monitoring token consumption

### Output Files

All outputs are saved to the `./outputs/` directory:

- **Translations**: `filename_translated.xlf` or `filename_translated_context.xlf`
- **Evaluations**: `filename_evaluation.json` and `filename_evaluation.pdf`
- **Cross-Language Reports**: `cross_language_report_TIMESTAMP.pdf`
- **Chart Images**: `chart_scores_TIMESTAMP.png`, `chart_clustered_TIMESTAMP.png`, etc.

**JSON Output Structure** (for evaluations):

```json
{
  "metadata": {
    "source_language": "en-GB",
    "target_language": "tr-TR",
    "source_file": "Turkish-MT.xlf",
    "evaluated_at": "2025-05-20T14:30:00",
    "model": "gpt-5-mini",
    "content_type": "general",
    "translation_source": "MT",
    "label": "Turkish Machine Translation"
  },
  "sampling": {
    "strategy": "Standard (15%)",
    "sampled": true,
    "total_valid_segments": 200,
    "evaluated_segments": 30,
    "percentage": 15.0,
    "seed": null
  },
  "results": [
    {
      "segment_id": "1",
      "overall_score": 85,
      "dimensions": {...},
      "issues": [...],
      "explanation": "..."
    }
  ]
}
```

The `metadata` block enables automatic language and source detection when files are loaded into Cross-Language Analysis. For JSON files without metadata (from older evaluations), the UI allows manual tagging.

## Project Structure

```
xliff2-qe/
├── core/
│   ├── xliff2_handler.py      # XLIFF 2.0 parsing and manipulation
│   ├── async_llm_provider.py  # Async OpenAI integration with call capture
│   ├── sampling.py            # Sampling strategies and selection
│   ├── api_cache.py           # API credential caching
│   └── config.py              # Configuration management
├── prompts/
│   └── templates.py           # Content-specific evaluation templates
├── reports/
│   ├── enhanced_report.py     # PDF report generation
│   ├── consolidated_report.py # Multi-file comparison reports
│   └── cross_language_report.py # Cross-language comparative analysis
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

**Cross-Language Reports include:**

- **Summary Table**: All evaluations ranked by average score with key metrics
- **Overall Statistics**: Combined averages across all evaluations
- **Comparative Charts**: Visual comparison of scores, dimensions, and issues
- **Exportable Images**: Individual PNG files for presentation use

**Unicode & CJK Support**: Reports automatically detect and use appropriate fonts for Chinese, Japanese, Korean, and other non-Latin scripts. Supported fonts include Noto Sans CJK, WQY MicroHei, MS Gothic/YaHei, and PingFang.

## Performance

- **Concurrent Processing**: Configurable concurrent API requests (default: 25)
- **Rate Limiting**: User-configurable requests per second (default: 10/sec)
- **Response Validation**: Validates all API responses before acceptance
- **Automatic Retry**: Exponential backoff with up to 5 retry attempts
- **Error Handling**: Individual segment failures marked with `[Translation failed]`
- **Token Optimisation**: Adaptive token limits based on segment complexity
- **Expected Success Rate**: 95-98% with default settings

### Reliability Features

- **Response Validation**: Checks for empty/null responses before processing
- **Clear Failure Markers**: Failed segments marked as `[Translation failed]` for easy identification
- **Event Loop Safety**: Automatic detection and handling of Streamlit event loop changes
- **Graceful Degradation**: Processing continues even if individual segments fail
- **API Call Capture**: First successful call of each type captured for inspection

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

## Troubleshooting

### Translation Failures

If you see `[Translation failed]` in output files:

1. **Reduce rate limiting**: Lower "Requests per second" to 5-10
2. **Reduce concurrency**: Lower "Max concurrent requests" to 10-15
3. **Check connection**: Ensure stable internet connection
4. **Verify API key**: Confirm OpenAI API key is valid and has credits
5. **Manual fix**: Search for `[Translation failed]` and translate those segments manually

### PDF Display Issues

If Chinese/Japanese/Korean characters appear as boxes (☐):

1. **Linux**: Install fonts: `sudo apt-get install fonts-noto-cjk`
2. **Windows**: System should have MS Gothic/YaHei by default
3. **macOS**: System should have PingFang/Hiragino by default

### Session State Issues

If settings seem stuck or not updating:

1. Click **"Clear All & Start Fresh"** button in sidebar
2. Or refresh the browser page
3. Re-upload files and adjust settings

### Cross-Language Analysis Issues

If language/source type not detected:

1. Use recommended filename format: `Language-Source_evaluation.json`
2. Manually set values in the expandable file sections
3. Ensure JSON files contain valid evaluation results

## Contributing

This project is in the public domain. Feel free to use, modify, and distribute as you see fit.

## Support

For issues or questions, please open an issue on GitHub.

------

**Note**: This is a quality evaluation tool. It does not replace human translators or professional translation quality assurance, but rather serves as an automated first-pass analysis to identify potential issues and areas requiring attention.
