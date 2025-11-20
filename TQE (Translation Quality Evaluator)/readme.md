# XLIFF 2.0 Translation Tools

Two complementary tools for working with XLIFF 2.0 translation files.

## Projects

### 1. XLIFF 2.0 Converter

Convert aligned multilingual text files to valid XLIFF 2.0 format.

**Key features:**

- Manual language code entry (MS LCID format)
- Batch processing
- Reference translations stored as metadata
- Compatible with Trados Studio

### 2. XLIFF 2.0 Translation Quality Evaluation System

LLM-powered quality evaluation and translation tool for XLIFF 2.0 files.

**Key features:**

- Three operation modes: translate (no context), translate (with context), evaluate
- 4-dimensional quality scoring (Accuracy, Fluency, Style, Context Coherence)
- Professional PDF reports
- Batch processing with async API calls

## Workflow

1. Use the **Converter** to create XLIFF 2.0 files from aligned text with reference translations
2. Use the **Evaluation System** to generate or assess translations with comprehensive quality analysis

## Requirements

Both projects require Python 3.8+ and their respective dependencies (see individual project directories).

## Licence

Public domain (The Unlicense)
