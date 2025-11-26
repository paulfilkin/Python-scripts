You are reviewing technical documentation translated from {source_lang} to {target_lang}.

{reference_translations}

{context_before}

Current segment to evaluate:
Source: {source_text}
Target: {target_text}

{context_after}

Evaluate the target translation for technical content:

1. ACCURACY (Weight: {accuracy_weight}%)
   - Technical correctness
   - No omissions of critical information
   - Precise terminology (verify against references)
   - Meaning preservation

2. FLUENCY (Weight: {fluency_weight}%)
   - Native-speaker naturalness
   - Clear, unambiguous phrasing
   - Appropriate for technical audience

3. STYLE (Weight: {style_weight}%)
   - Consistent with technical writing conventions
   - Appropriate register (formal, instructional)
   - Terminology consistency (check references)
   - Professional tone

4. CONTEXT COHERENCE (Weight: {context_weight}%)
   - Consistency with surrounding segments
   - Proper cross-references
   - Logical flow
   - Procedural clarity maintained

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
      "type": "accuracy|fluency|style|terminology|context_coherence",
      "severity": "critical|major|minor",
      "description": "Clear explanation of the issue"
    }}
  ],
  "confidence": 0-100,
  "explanation": "Overall assessment"
}}

For technical content, accuracy and clarity are paramount. Use references to verify terminology. Be strict about terminology consistency.