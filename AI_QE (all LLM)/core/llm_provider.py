"""
LLM Provider abstraction and OpenAI implementation.
Handles communication with OpenAI API for segment evaluation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import time


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def evaluate_segment(self, 
                        source: str, 
                        target: str, 
                        context_before: List[Dict],
                        context_after: List[Dict],
                        prompt_template: str,
                        config: dict) -> Dict[str, Any]:
        """Evaluate a single segment with context."""
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Check if API credentials are valid."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-5-mini", **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-5-mini, gpt-4o, gpt-4o-mini, etc.)
            **kwargs: Additional parameters (ignored, for compatibility)
        """
        self.api_key = api_key
        self.model = model
        
        # Initialize client
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    def _get_token_limit(self, config: dict) -> int:
        """Get token limit from config, handling legacy keys and None values."""
        token_limit = (config['llm_provider'].get('max_completion_tokens') or 
                      config['llm_provider'].get('max_output_tokens') or 
                      config['llm_provider'].get('max_tokens') or 
                      2000)
        return int(token_limit)
    
    def _build_api_params(self, messages: List[Dict], config: dict) -> Dict[str, Any]:
        """Build API parameters with correct token parameter name and supported fields."""
        token_limit = self._get_token_limit(config)
        
        # GPT-5 and GPT-4.1 models use max_completion_tokens
        # Older models use max_tokens
        if self.model.startswith('gpt-5') or self.model.startswith('gpt-4.1'):
            token_param = 'max_completion_tokens'
        else:
            token_param = 'max_tokens'
        
        api_params = {
            'model': self.model,
            'messages': messages,
            token_param: token_limit
        }
        
        # Only add temperature for models that support custom values
        # gpt-5-mini only supports temperature=1 (default), so omit it
        if not self.model.startswith('gpt-5-mini'):
            temperature = config['llm_provider'].get('temperature')
            if temperature is not None:
                api_params['temperature'] = float(temperature)
        
        return api_params
    
    def validate_credentials(self) -> bool:
        """Test API connection with a minimal request."""
        try:
            # Use minimal parameters for test
            if self.model.startswith('gpt-5') or self.model.startswith('gpt-4.1'):
                token_param = 'max_completion_tokens'
            else:
                token_param = 'max_tokens'
            
            api_params = {
                'model': self.model,
                'messages': [{"role": "user", "content": "test"}],
                token_param: 5
            }
            
            response = self.client.chat.completions.create(**api_params)
            return True
        except Exception as e:
            error_msg = str(e)
            if '401' in error_msg or '403' in error_msg or 'Incorrect API key' in error_msg:
                print(f"API authentication failed: Check your API key")
            else:
                print(f"API validation failed: {e}")
            return False
    
    def evaluate_segment(self, 
                        source: str, 
                        target: str, 
                        context_before: List[Dict],
                        context_after: List[Dict],
                        prompt_template: str,
                        config: dict) -> Dict[str, Any]:
        """
        Evaluate a single segment using OpenAI API.
        
        Returns:
            Dictionary with evaluation results including scores, issues, and explanation
        """
        # Build the prompt
        prompt = self._build_prompt(
            source, target, 
            context_before, context_after, 
            prompt_template, config
        )
        
        # Build messages
        messages = [
            {"role": "system", "content": "You are an expert translation quality evaluator."},
            {"role": "user", "content": prompt}
        ]
        
        # Call API with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                api_params = self._build_api_params(messages, config)
                response = self.client.chat.completions.create(**api_params)
                
                # Parse response
                result_text = response.choices[0].message.content
                evaluation = self._parse_response(result_text)
                
                # Add model info
                evaluation['model'] = f"openai:{self.model}"
                
                return evaluation
                
            except Exception as e:
                error_msg = str(e)
                
                # Don't retry on 400 bad request errors
                if '400' in error_msg:
                    print(f"  API request error (check model compatibility): {e}")
                    return {
                        'error': str(e),
                        'overall_score': None,
                        'dimensions': {},
                        'issues': [],
                        'explanation': f"API request error: {str(e)}",
                        'confidence': 0
                    }
                
                # Retry on server errors (5xx) and rate limits (429)
                if any(code in error_msg for code in ['429', '500', '502', '503', '504']):
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"  API error, retrying in {wait_time}s... ({e})")
                        time.sleep(wait_time)
                        continue
                
                # Don't retry other errors
                return {
                    'error': str(e),
                    'overall_score': None,
                    'dimensions': {},
                    'issues': [],
                    'explanation': f"API error: {str(e)}",
                    'confidence': 0
                }
    
    def _build_prompt(self, source: str, target: str,
                     context_before: List[Dict], context_after: List[Dict],
                     template: str, config: dict) -> str:
        """Build the evaluation prompt with context."""
        
        # Format context
        context_before_text = ""
        if context_before:
            context_before_text = "Previous segments (for reference):\n"
            for seg in context_before:
                context_before_text += f"  [{seg['id']}] Source: {seg['source']}\n"
                context_before_text += f"       Target: {seg['target']}\n"
        
        context_after_text = ""
        if context_after:
            context_after_text = "Following segments (for reference):\n"
            for seg in context_after:
                context_after_text += f"  [{seg['id']}] Source: {seg['source']}\n"
                context_after_text += f"       Target: {seg['target']}\n"
        
        # Build full prompt
        prompt = template.format(
            source_lang=config['language_pair']['source'],
            target_lang=config['language_pair']['target'],
            context_before=context_before_text or "None",
            source_text=source,
            target_text=target,
            context_after=context_after_text or "None",
            accuracy_weight=config['analysis_dimensions']['accuracy']['weight'],
            fluency_weight=config['analysis_dimensions']['fluency']['weight'],
            style_weight=config['analysis_dimensions']['style']['weight'],
            context_weight=config['analysis_dimensions']['context_coherence']['weight']
        )
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured evaluation.
        Expects JSON format from the model.
        """
        try:
            # Try to extract JSON from response
            # Sometimes models wrap JSON in markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()
            
            evaluation = json.loads(json_text)
            
            # Validate structure
            required_keys = ['overall_score', 'dimensions', 'issues', 'explanation']
            for key in required_keys:
                if key not in evaluation:
                    evaluation[key] = self._get_default_value(key)
            
            return evaluation
            
        except json.JSONDecodeError as e:
            # Fallback: try to extract information from text
            return {
                'overall_score': 50,  # Default uncertain score
                'dimensions': {
                    'accuracy': 50,
                    'fluency': 50,
                    'style': 50,
                    'context_coherence': 50
                },
                'issues': [{
                    'type': 'parsing_error',
                    'severity': 'major',
                    'description': 'Could not parse LLM response'
                }],
                'explanation': f"Response parsing failed: {response_text[:200]}",
                'confidence': 30
            }
    
    def _get_default_value(self, key: str) -> Any:
        """Get default value for missing keys."""
        defaults = {
            'overall_score': 50,
            'dimensions': {
                'accuracy': 50,
                'fluency': 50,
                'style': 50,
                'context_coherence': 50
            },
            'issues': [],
            'explanation': 'No explanation provided',
            'confidence': 50
        }
        return defaults.get(key)