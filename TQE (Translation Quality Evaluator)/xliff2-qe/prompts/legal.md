You are reviewing legal/compliance documentation translated from {source_lang} to {target_lang}.

CRITICAL: This is legal content. Accuracy is paramount.

{reference_translations}

{context_before}

Current segment to evaluate:
Source: {source_text}
Target: {target_text}

{context_after}

Evaluate the target translation for legal content:

1. ACCURACY (Weight: {accuracy_weight}%)
   - ABSOLUTE semantic equivalence (verify with references)
   - No interpretation or paraphrasing
   - All conditions, obligations, and rights preserved
   - Legal terminology precision (compare with references)
   - No omissions or additions

2. COMPLETENESS (Weight: 20%)
   - Nothing omitted
   - Nothing added
   - All qualifiers and hedges preserved

3. FLUENCY (Weight: {fluency_weight}%)
   - Clear, unambiguous phrasing
   - Appropriate legal register
   - Grammar accuracy

4. CONSISTENCY (Weight: {context_weight}%)
   - Term consistency (check references)
   - Structural parallelism
   - Cross-reference accuracy

Provide your evaluation in JSON format:
{{
  "overall_score": 0-100,
  "dimensions": {{
    "accuracy": 0-100,
    "fluency": 0-100,
    "style": 0-100,
    "context_coherence": 0-100
  }},
  "issues": [
    {{
      "type": "accuracy|terminology|omission|addition|ambiguity",
      "severity": "critical|major|minor",
      "description": "Clear explanation of the issue"
    }}
  ],
  "confidence": 0-100,
  "explanation": "Overall assessment"
}}

Be EXTREMELY strict. Use references to verify terminology and meaning. Any deviation from source meaning or omission is a critical issue in legal content.