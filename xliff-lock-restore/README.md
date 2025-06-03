# XLIFF Lock & Restore Toolset

This repository contains two standalone Python scripts designed to help localisation engineers manage non-translatable content within `.xlf`/`.xliff` files when working with CAT tools like **Trados Studio**. The idea is to demonstrate the concept with a working example that could be used for many different types of pre/post XLIFF processing.

## Problem

When translating structured content (e.g. code blocks or auto-generated Confluence links), certain elements should not be modified by translators. Standard XLIFF 1.2 does not always allow fine-grained locking of inline content using default settings in Trados Studio.

Trados does not support locking content inside `<g>` tags directly using the native XLIFF filetype.

## Goal

These tools enable the safe transformation of XLIFF files **before and after translation**, so that non-translatable content is:
- **locked** using `<mrk mtype="protected">` before translation
- **restored** back to `<g>` tags after translation for round-tripping

This allows Trados to respect the protected content, improving consistency, reducing risk of accidental edits, and simplifying translator workflows.

---

## Workflow

### 1. `lock_xliff_lxml.py` – Pre-processing

This script:
- Traverses all `.xliff` and `.xlf` files in the specified folder (including subfolders)
- Backs up all files into a sibling folder named `<input_folder>_Backup`
- Replaces `<g>` elements with:
  - `ctype="x-code"`
  - `ctype="x-vsn-link"` **and** `ri:page-content-title` attribute
- …with `<mrk mtype="protected">` equivalents (preserving `id`, `ctype`, and `ri:*` attributes)

This locks content like:
```xml
<g ctype="x-code" id="g1">code</g>
```
into:
```xml
<mrk mtype="protected" ctype="x-code" id="g1">code</mrk>
```

---

### 2. `restore_xliff_lxml.py` – Post-processing

This script:
- Traverses the same folder structure **after translation**
- Finds all `<mrk mtype="protected">` elements in both `<source>` and `<target>` elements
- Converts them back into `<g>` tags
- Preserves all relevant attributes (`id`, `ctype`, `ri:*`)

This ensures compatibility with the consuming system after translation is complete.

---

## Example Use Case

Original:
```xml
<source>I am <g ctype="x-code" id="g2">code</g> text.</source>
```

➡ After locking:
```xml
<source>I am <mrk mtype="protected" ctype="x-code" id="g2">code</mrk> text.</source>
```

➡ After translation + restore:
```xml
<source>I am <g ctype="x-code" id="g2">code</g> text.</source>
<target>Ich bin <g ctype="x-code" id="g2">code</g> text.</target>
```

---

## Requirements

- Python 3.7+
- Install `lxml`:
  ```
  pip install lxml
  ```

---

## File Overview

| Script | Purpose |
|--------|---------|
| `lock_xliff_lxml.py` | Prepares XLIFF by locking inline code/links |
| `restore_xliff_lxml.py` | Reverts locked segments back into inline tags post-translation |
| `README.md` | You are here |

---

## 🛡️ Safety

- All original files are backed up before any changes are made
- Processing is non-destructive and retains attribute integrity

---

## Notes

- Works best with XLIFF 1.2 files
- Designed for compatibility with Trados Studio XLIFF parsing

