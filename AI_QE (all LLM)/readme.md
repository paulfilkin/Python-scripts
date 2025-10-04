# Another way to use an LLM to review your files!

LLM-Powered Translation Quality Analysis for SDLXLIFF files

## Overview

This LLM Review uses Large Language Models (specifically OpenAI's GPT models) to perform intelligent, context-aware quality evaluation of translated content. Unlike traditional rule-based QA tools, it understands context, detects semantic issues, evaluates naturalness, and identifies problems that only become apparent when analyzing multiple segments together.

### Key Features

- **Context-Aware Analysis**: Analyzes segments with surrounding context (configurable window)
- **Intelligent Quality Scoring**: Multi-dimensional evaluation (Accuracy, Fluency, Style, Context Coherence)
- **Structured Comments**: Injects filterable comments into XLIFF files for Trados Studio
- **Comprehensive Reports**: Generates detailed PDF reports with visualizations
- **Content Type Templates**: Specialized prompts for technical, marketing, legal, and UI content
- **Batch Processing**: Process entire folders of SDLXLIFF files
- **Multiple Review Profiles**: Quick Scan, Context Review, and Deep Analysis modes
- **Multiple Model Support**: Choose between gpt-5-mini, gpt-5, and gpt-4o

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### Setup

1. **Install Dependencies**
```bash
pip install openai reportlab matplotlib numpy python-dotenv
```
### Project Structure

<details>
<summary>Tree view (click to view)</summary>

```text
really-smart-review/
├── really_smart_review.py
├── .env
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── xliff_handler.py
│   ├── llm_provider.py
│   └── analyzer.py
├── prompts/
│   ├── __init__.py
│   └── templates.py
└── reports/
    ├── __init__.py
    └── enhanced_report.py
```
</details>
**Configure API Key**

Create a `.env` file in the project root directory (same folder as `really_smart_review.py`). This file stores your API key securely and is automatically loaded by the application. 

Edit the `.env` file and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```



## Usage

### Interactive Mode

```bash
python really_smart_review.py
```

The script will guide you through:

1. Automatically loading your API key from `.env`
2. Selecting the folder containing SDLXLIFF files
3. Choosing a review profile
4. Selecting content type
5. Choosing which model to use (gpt-5-mini, gpt-5, or gpt-4o)
6. Optionally saving the configuration for future use

### Command Line Mode

```bash
# Uses API key from .env file automatically
python really_smart_review.py C:\path\to\xliff\folder

# With saved configuration
python really_smart_review.py C:\path\to\xliff\folder config.json
```

### Review Profiles

**1. Quick Scan**

- No context analysis (segment-only)
- Fastest processing
- Best for: High-volume content, initial assessment

**2. Context Review** (Default, Recommended)

- Analyzes with ±5 segments of context
- Balanced speed and quality
- Best for: Standard professional translation review

**3. Deep Analysis**

- Analyzes with ±10 segments of context
- Document-level pattern detection enabled
- Best for: High-stakes content (legal, medical, marketing campaigns)

### Content Types

- **General**: Mixed content, balanced evaluation
- **Technical Documentation**: Emphasis on accuracy and terminology
- **Marketing/UX**: Focus on tone, engagement, cultural adaptation
- **Legal/Compliance**: Strict accuracy, no interpretation allowed
- **UI Strings**: Clarity, brevity, consistency

### Model Selection

The system supports multiple OpenAI models with different characteristics (according to OpenAI):

| Model          | Speed   | Cost   | Quality   | Temperature Support | Best For                             |
| -------------- | ------- | ------ | --------- | ------------------- | ------------------------------------ |
| **gpt-5-mini** | Fastest | Lowest | Good      | No (fixed at 1.0)   | High-volume, cost-sensitive projects |
| **gpt-5**      | Fast    | Medium | Excellent | Limited             | High-quality analysis, balanced cost |
| **gpt-4o**     | Medium  | Higher | Excellent | Yes (0.0-2.0)       | Customizable, predictable results    |

**Parameter Differences:**

- **gpt-5-mini**: Uses `max_completion_tokens`, no temperature control
- **gpt-5**: Uses `max_completion_tokens`, limited temperature support
- **gpt-4o**: Uses `max_tokens`, full temperature control (default: 0.3)

The system automatically handles these differences.

## Output

This LLM Review generates three types of output in the `smart_review_results/` folder:

1. **Annotated XLIFF Files**: `[filename].sdlxliff`
   - Original files with structured comments injected
   - Comments link to specific segments via unique IDs
   - Filterable in Trados Studio using comment metadata
2. **Comprehensive PDF Report**: `smart_review_report.pdf`
   - Executive summary with overall statistics
   - Score distribution histograms
   - Quality dimension radar charts (Accuracy, Fluency, Style, Context)
   - File-by-file detailed analysis
   - Segments requiring attention with explanations
   - Sample high-quality segments
3. **Analysis Data**: `analysis_data.json`
   - Complete raw data in JSON format
   - All segment evaluations, scores, and issues
   - Useful for further processing or custom reporting



## Filtering Comments in Trados Studio

The structured comments include metadata that allows powerful filtering:

| Filter Goal     | Search Pattern                | Description                          |
| --------------- | ----------------------------- | ------------------------------------ |
| Critical issues | `QE Severity: Critical`       | Only segments with critical errors   |
| Major issues    | `QE Severity: Major`          | Segments with significant problems   |
| Low scores      | `QE Band: 50-60`              | Segments scoring 50-59               |
| Very low scores | `QE Band: 30-40`              | Segments scoring 30-39               |
| Accuracy issues | `QE Category: accuracy`       | Segments with accuracy problems      |
| Context issues  | `QE Context: cross-segment`   | Issues detected via context analysis |
| Low confidence  | `QE Confidence: [0-6]`        | Evaluations with 0-69% confidence    |
| Specific model  | `QE Model: openai:gpt-5-mini` | Filter by evaluation model           |

**Comment Structure Example:**

```
QE Score: 45
QE Band: 40-50
QE Category: context_coherence, accuracy, fluency
QE Severity: Major
QE Dimensions: Accuracy:40|Fluency:50|Style:60|Context_Coherence:30
QE Confidence: 80%
QE Context: cross-segment (analyzed 1-10)
QE Model: openai:gpt-5-mini
QE Comment: [Natural language explanation of the issue]
```



## Configuration

### Default Settings

The system uses what seems like sensible defaults:

- Model: `gpt-5-mini` (fastest and most cost-effective according to OpenAI - although it seemed slower when comparing!)
- Context window: 5 segments (±5)
- Score threshold for comments: 80 (comments added below this score)

### Creating Custom Configurations

Save a configuration for reuse:

```json
{
  "profile_name": "my-technical-config",
  "review_profile": "context_review",
  "content_type": "technical_documentation",
  "context_window": 7,
  "analysis_dimensions": {
    "accuracy": {
      "enabled": true,
      "weight": 45,
      "threshold": 75
    },
    "fluency": {
      "enabled": true,
      "weight": 25,
      "threshold": 70
    },
    "style": {
      "enabled": true,
      "weight": 20,
      "threshold": 65
    },
    "context_coherence": {
      "enabled": true,
      "weight": 10,
      "threshold": 70
    }
  },
  "comment_generation": {
    "add_comments_for": "issues_only",
    "score_threshold": 85
  },
  "llm_provider": {
    "type": "openai",
    "model": "gpt-4o",
    "temperature": 0.3,
    "max_tokens": 2000
  }
}
```

Save as `my-config.json` and use: `python really_smart_review.py C:\path\to\folder my-config.json`

**Note:** For gpt-5-mini, omit the `temperature` parameter as it only supports the default value.



## Troubleshooting

### API Key Issues

**Problem:** "API validation failed" or authentication errors

**Solution:**

1. Verify your `.env` file exists in the project root
2. Check your API key starts with `sk-` and has no extra spaces
3. Test your key:

```bash
python -c "from openai import OpenAI; import os; from dotenv import load_dotenv; load_dotenv(); print(OpenAI(api_key=os.getenv('OPENAI_API_KEY')).models.list())"
```

### Model Compatibility Issues

**Problem:** "Unsupported parameter" or "Unsupported value" errors

**Solution:** The system automatically handles different model requirements. If you encounter these errors:

1. Ensure you're using the latest version of the code
2. Check that you haven't manually edited config files with incompatible parameters
3. For gpt-5-mini, do not include `temperature` in custom configs

### Module Not Found Errors

**Problem:** `ModuleNotFoundError: No module named 'core'`

**Solution:** Ensure all `__init__.py` files exist:

```powershell
# Windows
Get-ChildItem -Recurse __init__.py

# Should show:
# core\__init__.py
# prompts\__init__.py
# reports\__init__.py
```

### Missing Dependencies

**Problem:** Import errors for openai, reportlab, matplotlib, etc.

**Solution:**

```bash
pip install openai reportlab matplotlib numpy python-dotenv
```

### Rate Limit Errors

The system only retries on rate limits (429) and server errors (5xx). For persistent rate limits:

- Process smaller batches of files
- Reduce context window size
- Check your OpenAI usage limits at https://platform.openai.com/usage



## Customizing Quality Thresholds and Comment Behavior

The system currently adds comments only to segments scoring below 80. You can customize when and what types of comments are added.

### Location: `core/config.py`

Find the `comment_generation` section in the `get_default_config()` function (around line 45):

```python
"comment_generation": {
    "add_comments_for": "issues_only",  # all, issues_only, critical_only
    "score_threshold": 80,  # Only comment if score below this
    # ... format options
}
```

### Customization Options

**1. Add Comments to High-Quality Segments**

To add positive feedback comments to excellent translations, change:

- `"add_comments_for": "all"` - Comments on ALL segments
- Modify `core/xliff_handler.py` `create_comment()` to add score-specific messages

**2. Separate Thresholds for Different Quality Levels**

Add to config:

```python
"positive_threshold": 90,  # Comment on excellent segments
"critical_threshold": 60,   # Comment on poor segments
```

Then modify `core/analyzer.py` `_should_add_comment()` method to use these thresholds.

**3. Alternative: Generate Excellence Reports**

Instead of commenting excellent segments, generate separate reports highlighting best translations for TM/style guide reuse.

### Filtering for Excellence in Trados

After customizing to add positive comments, filter for:

- Excellent segments: `QE Band: 90-100`
- Good segments: `QE Band: 80-90`

## Understanding the Scores

**Overall Score (0-100):**

- 90-100: Excellent quality
- 80-89: Good quality, minor issues
- 70-79: Acceptable, needs review
- 60-69: Poor quality, significant issues
- 0-59: Critical problems

**Dimension Scores:**

- **Accuracy**: Semantic fidelity, no omissions/additions
- **Fluency**: Natural grammar, readability
- **Style**: Appropriate tone, register, terminology
- **Context Coherence**: Consistency across segments

## Limitations

- **API Dependency**: Requires internet connection and active OpenAI account
- **Cost**: Large batches incur API costs (monitor at platform.openai.com/usage)
- **Processing Time**: ~1-2 seconds per segment (not real-time)
- **Complementary Tool**: Designed to work alongside, not replace, Trados QA
- **Data Privacy**: Source/target text is sent to OpenAI servers (consider for sensitive content)
- **Language Support**: Works best for well-supported language pairs; quality may vary
- **Model-Specific Limitations**: gpt-5-mini has fixed temperature and may produce less nuanced evaluations



------

**This LLM Review** - Translation QA powered by AI, designed for humans.
