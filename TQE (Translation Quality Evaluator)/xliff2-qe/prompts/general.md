You are reviewing a translation from {source_lang} to {target_lang}.

{reference_translations}

{context_before}

Current segment to evaluate:
Source: {source_text}
Target: {target_text}

{context_after}

Evaluate the target translation across these dimensions:

1. ACCURACY (Weight: {accuracy_weight}%)
   - Semantic fidelity to source
   - No omissions or unwarranted additions
   - Meaning preservation
   - Use reference translations to verify correct interpretation

2. FLUENCY (Weight: {fluency_weight}%)
   - Native-speaker naturalness
   - Grammar and syntax
   - Readability

3. STYLE (Weight: {style_weight}%)
   - Appropriate register and tone
   - Consistent terminology (compare with references)
   - Cultural appropriateness

4. CONTEXT COHERENCE (Weight: {context_weight}%)
   - Consistency with surrounding segments
   - Proper reference resolution
   - Logical flow

Provide your evaluation in the following JSON format:
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
      "type": "accuracy|fluency|style|grammar|context_coherence|terminology",
      "severity": "critical|major|minor",
      "description": "Clear explanation of the issue"
    }}
  ],
  "confidence": 0-100,
  "explanation": "Overall assessment and key points"
}}

Be strict but fair. Use reference translations to understand intended meaning and verify terminology. Consider context when evaluating consistency.