You are reviewing user interface text translated from {source_lang} to {target_lang}.

Special considerations for UI:
- Brevity is crucial
- Clarity over creativity
- Consistency with UI patterns (verify with references)
- Action-oriented language

{reference_translations}

{context_before}

Current segment to evaluate:
Source: {source_text}
Target: {target_text}

{context_after}

Evaluate the target translation for UI strings:

1. CLARITY & CONCISENESS (Weight: {style_weight}%)
   - Message clear and unambiguous
   - Appropriately brief
   - Action verbs where applicable
   - User-friendly language

2. ACCURACY (Weight: {accuracy_weight}%)
   - Correct meaning (verify with references)
   - Proper context for UI element
   - Function preserved

3. CONSISTENCY (Weight: {context_weight}%)
   - Matches established UI terminology (compare with references)
   - Consistent tone across interface
   - Standard UI conventions

4. FLUENCY (Weight: {fluency_weight}%)
   - Natural for UI context
   - Grammatically correct
   - No awkward phrasing

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
      "type": "clarity|accuracy|consistency|length|tone",
      "severity": "critical|major|minor",
      "description": "Clear explanation of the issue"
    }}
  ],
  "confidence": 0-100,
  "explanation": "Overall assessment"
}}

For UI strings, clarity and brevity are key. Use references to ensure terminology consistency. Consider if the translation fits typical UI space constraints.