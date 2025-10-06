# Another way to use an LLM to review your files!

LLM-Powered Translation Quality Analysis for SDLXLIFF files

## Overview

This LLM Review uses Large Language Models (OpenAI's GPT models) to perform intelligent, context-aware quality evaluation of translated content. Unlike traditional rule-based QA tools, it understands context, detects semantic issues, evaluates naturalness, and identifies problems that only become apparent when analyzing multiple segments together.

### Key Features

- **High-Performance Processing**: 50 concurrent API requests for fast analysis of large batches
- **Context-Aware Analysis**: Analyzes segments with surrounding context for better accuracy
- **Multi-Dimensional Scoring**: Evaluates Accuracy, Fluency, Style, and Context Coherence
- **Structured Comments**: Injects filterable comments directly into XLIFF files for Trados Studio
- **Comprehensive Reports**: Generates detailed PDF reports with visualizations
- **Content Type Templates**: Specialized prompts for technical, marketing, legal, and UI content
- **Batch Processing**: Process entire folders of SDLXLIFF files efficiently
- **Cost Optimized**: Smart token management reduces API costs by ~80%

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### Setup

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install openai lxml reportlab matplotlib numpy python-dotenv
```

**Important:** The `lxml` package is required for proper XLIFF namespace handling.

### Project Structure

```text
really-smart-review/
├── really_smart_review.py
├── .env
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── xliff_handler.py
│   ├── async_llm_provider.py
│   ├── api_cache.py
│   └── analyzer.py
├── prompts/
│   ├── __init__.py
│   └── templates.py
└── reports/
    ├── __init__.py
    └── enhanced_report.py
```

### Configure API Key

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

## Usage

### Interactive Mode

```bash
python really_smart_review.py
```

### Command Line Mode

```bash
python really_smart_review.py /path/to/xliff/folder
python really_smart_review.py /path/to/xliff/folder config.json
```

### Review Profiles

**Quick Scan**: Segment-only analysis, fastest processing

**Context Review** (Default): Analyzes with ±5 segments of context, balanced speed and quality

**Deep Analysis**: Analyzes with ±10 segments of context, best for high-stakes content

### Content Types

- **General**: Mixed content, balanced evaluation
- **Technical Documentation**: Emphasis on accuracy and terminology
- **Marketing/UX**: Focus on tone, engagement, cultural adaptation
- **Legal/Compliance**: Strict accuracy, no interpretation allowed
- **UI Strings**: Clarity, brevity, consistency

### Model Selection

| Model          | Speed   | Cost   | Quality   | Best For                             |
| -------------- | ------- | ------ | --------- | ------------------------------------ |
| **gpt-5-mini** | Fastest | Lowest | Good      | High-volume, cost-sensitive projects |
| **gpt-5**      | Fast    | Medium | Excellent | High-quality analysis, balanced cost |
| **gpt-4o**     | Medium  | Higher | Excellent | Premium quality results              |

## Performance

### Processing Speed

- 250 segments: ~30-60 seconds
- 1,000 segments: ~2-4 minutes
- 5,000 segments: ~10-20 minutes

### Cost Estimates

With gpt-5-mini: approximately $0.50-$2.00 per 1,000 segments

## Output

Results are saved in `smart_review_results/` folder:

**Annotated XLIFF Files**: Original files with structured QE comments injected, ready to open in Trados Studio

**PDF Report**: Executive summary, score distributions, quality dimensions, file-by-file analysis, segments requiring attention

**Analysis Data**: Complete evaluation data in JSON format for further processing

## Filtering Comments in Trados Studio

Comments include structured metadata for filtering:

| Search Pattern                | What it finds                        |
| ----------------------------- | ------------------------------------ |
| `QE Severity: Critical`       | Only segments with critical errors   |
| `QE Severity: Major`          | Segments with significant problems   |
| `QE Band: 50-60`              | Segments scoring 50-59               |
| `QE Category: accuracy`       | Segments with accuracy problems      |
| `QE Context: cross-segment`   | Issues detected via context analysis |
| `QE Model: openai:gpt-5-mini` | Filter by evaluation model           |

## Configuration

Default settings use gpt-5-mini with 5-segment context windows and 50 concurrent requests. Customize by saving a JSON configuration file:

```json
{
  "review_profile": "context_review",
  "content_type": "technical_documentation",
  "context_window": 7,
  "comment_generation": {
    "add_comments_for": "issues_only",
    "score_threshold": 85
  },
  "llm_provider": {
    "model": "gpt-4o",
    "temperature": 0.3
  }
}
```

## Understanding Scores

**Overall Score (0-100):**

- 90-100: Excellent quality
- 80-89: Good quality, minor issues
- 70-79: Acceptable, needs review
- 60-69: Poor quality, significant issues
- 0-59: Critical problems

**Dimensions:**

- **Accuracy**: Semantic fidelity, no omissions/additions
- **Fluency**: Natural grammar, readability
- **Style**: Appropriate tone, register, terminology
- **Context Coherence**: Consistency across segments

## System Requirements

- Python 3.8+
- 2GB RAM minimum (4GB+ for large batches)
- Internet connection for API access
- OpenAI API account with sufficient credits

------

**LLM Powered Review** - Translation QE powered by AI, designed for humans.
