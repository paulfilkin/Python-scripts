"""
Prompt templates for different content types.
Each template is optimized for specific translation contexts.
"""


class PromptTemplateManager:
    """Manage and retrieve prompt templates for different content types."""
    
    def __init__(self):
        self.templates = {
            'general': self._general_template(),
            'technical_documentation': self._technical_template(),
            'marketing': self._marketing_template(),
            'legal': self._legal_template(),
            'ui_strings': self._ui_strings_template()
        }
    
    def get_template(self, content_type: str) -> str:
        """Get prompt template for content type."""
        return self.templates.get(content_type, self.templates['general'])
    
    def _general_template(self) -> str:
        """General purpose evaluation template."""
        return """You are reviewing a translation from {source_lang} to {target_lang}.

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

2. FLUENCY (Weight: {fluency_weight}%)
   - Native-speaker naturalness
   - Grammar and syntax
   - Readability

3. STYLE (Weight: {style_weight}%)
   - Appropriate register and tone
   - Consistent terminology
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

Be strict but fair. Consider context when evaluating consistency. Distinguish between minor stylistic preferences and actual errors."""
    
    def _technical_template(self) -> str:
        """Technical documentation template."""
        return """You are reviewing technical documentation translated from {source_lang} to {target_lang}.

{context_before}

Current segment to evaluate:
Source: {source_text}
Target: {target_text}

{context_after}

Evaluate the target translation for technical content:

1. ACCURACY (Weight: {accuracy_weight}%)
   - Technical correctness
   - No omissions of critical information
   - Precise terminology
   - Meaning preservation

2. FLUENCY (Weight: {fluency_weight}%)
   - Native-speaker naturalness
   - Clear, unambiguous phrasing
   - Appropriate for technical audience

3. STYLE (Weight: {style_weight}%)
   - Consistent with technical writing conventions
   - Appropriate register (formal, instructional)
   - Terminology consistency
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

For technical content, accuracy and clarity are paramount. Be strict about terminology consistency."""
    
    def _marketing_template(self) -> str:
        """Marketing/UX copy template."""
        return """You are reviewing customer-facing marketing content translated from {source_lang} to {target_lang}.

{context_before}

Current segment to evaluate:
Source: {source_text}
Target: {target_text}

{context_after}

Evaluate the target translation for marketing content:

1. STYLE & TONE (Weight: {style_weight}%)
   - Brand voice consistency
   - Emotional resonance
   - Persuasiveness
   - Cultural appropriateness

2. ACCURACY (Weight: {accuracy_weight}%)
   - Core message preserved
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

For marketing content, engagement and cultural adaptation matter most. A translation that sounds native and compelling is better than a literal one."""
    
    def _legal_template(self) -> str:
        """Legal/compliance content template."""
        return """You are reviewing legal/compliance documentation translated from {source_lang} to {target_lang}.

CRITICAL: This is legal content. Accuracy is paramount.

{context_before}

Current segment to evaluate:
Source: {source_text}
Target: {target_text}

{context_after}

Evaluate the target translation for legal content:

1. ACCURACY (Weight: {accuracy_weight}%)
   - ABSOLUTE semantic equivalence
   - No interpretation or paraphrasing
   - All conditions, obligations, and rights preserved
   - Legal terminology precision
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
   - Term consistency
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

Be EXTREMELY strict. Any deviation from source meaning or omission is a critical issue in legal content."""
    
    def _ui_strings_template(self) -> str:
        """UI strings template."""
        return """You are reviewing user interface text translated from {source_lang} to {target_lang}.

Special considerations for UI:
- Brevity is crucial
- Clarity over creativity
- Consistency with UI patterns
- Action-oriented language

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
   - Correct meaning
   - Proper context for UI element
   - Function preserved

3. CONSISTENCY (Weight: {context_weight}%)
   - Matches established UI terminology
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

For UI strings, clarity and brevity are key. Consider if the translation fits typical UI space constraints."""