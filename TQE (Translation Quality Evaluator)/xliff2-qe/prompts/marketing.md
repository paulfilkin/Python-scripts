You are reviewing customer-facing marketing content translated from {source_lang} to {target_lang}.

{reference_translations}

{context_before}

Current segment to evaluate:
Source: {source_text}
Target: {target_text}

{context_after}

Evaluate the target translation for marketing content:

1. STYLE & TONE (Weight: {style_weight}%)
   - Brand voice consistency (compare with references)
   - Emotional resonance
   - Persuasiveness
   - Cultural appropriateness

2. ACCURACY (Weight: {accuracy_weight}%)
   - Core message preserved (verify with references)
   - Key selling points maintained
   - No factual errors

3. FLUENCY (Weight: {fluency_weight}%)
   - Native-speaker quality
   - Idiomatic usage
   - Natural, engaging language
   - Flow and rhythm

4. CONTEXT COHERENCE (Weight: {context_weight}%)
   - Consistent messaging across segments
   - Campaign/theme continuity
   - Call-to-action clarity

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
      "type": "style|fluency|accuracy|context_coherence|tone",
      "severity": "critical|major|minor",
      "description": "Clear explanation of the issue"
    }}
  ],
  "confidence": 0-100,
  "explanation": "Overall assessment"
}}

For marketing content, engagement and cultural adaptation matter most. Use references to understand tone and style. A translation that sounds native and compelling is better than a literal one.