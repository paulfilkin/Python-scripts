"""
Async LLM Provider for concurrent segment evaluation.
Replaces synchronous OpenAI calls with async implementation.
"""

import asyncio
import json
import random
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI, RateLimitError, APIError


class AsyncOpenAIProvider:
    """Async OpenAI API provider with controlled concurrency."""
    
    def __init__(self, api_key: str, model: str = "gpt-5-mini", max_concurrent: int = 50):
        """
        Initialize async OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-5-mini, gpt-5, gpt-4o, etc.)
            max_concurrent: Maximum concurrent requests (default: 50)
        """
        self.api_key = api_key
        self.model = model
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Initialize async client
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def validate_credentials(self) -> bool:
        """Test API connection with a minimal request."""
        try:
            token_param = self._get_token_param_name()
            
            api_params = {
                'model': self.model,
                'messages': [{"role": "user", "content": "test"}],
                token_param: 5
            }
            
            await self.client.chat.completions.create(**api_params)
            return True
        except Exception as e:
            error_msg = str(e)
            if '401' in error_msg or '403' in error_msg or 'Incorrect API key' in error_msg:
                print(f"API authentication failed: Check your API key")
            else:
                print(f"API validation failed: {e}")
            return False
    
    async def evaluate_segments_batch(self,
                                     segments_with_context: List[Dict[str, Any]],
                                     prompt_template: str,
                                     config: dict) -> List[Dict[str, Any]]:
        """
        Evaluate multiple segments concurrently.
        
        Args:
            segments_with_context: List of dicts containing segment data and context
            prompt_template: Prompt template for evaluation
            config: Configuration dictionary
        
        Returns:
            List of evaluation results in same order as input
        """
        tasks = []
        for item in segments_with_context:
            task = self._evaluate_single_segment(
                item['source'],
                item['target'],
                item['context_before'],
                item['context_after'],
                item['segment_id'],
                item['segment_index'],
                prompt_template,
                config
            )
            tasks.append(task)
        
        # Execute all tasks concurrently with progress tracking
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                # Create error evaluation
                item = segments_with_context[idx]
                processed_results.append({
                    'segment_id': item['segment_id'],
                    'segment_index': item['segment_index'],
                    'source': item['source'],
                    'target': item['target'],
                    'error': str(result),
                    'overall_score': None,
                    'dimensions': {},
                    'issues': [],
                    'explanation': f"Evaluation failed: {str(result)}",
                    'confidence': 0
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _evaluate_single_segment(self,
                                      source: str,
                                      target: str,
                                      context_before: List[Dict],
                                      context_after: List[Dict],
                                      segment_id: str,
                                      segment_index: int,
                                      prompt_template: str,
                                      config: dict) -> Dict[str, Any]:
        """Evaluate a single segment with semaphore control."""
        async with self.semaphore:
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
            evaluation = await self._call_api_with_retry(messages, config)
            
            # Add metadata
            evaluation['segment_id'] = segment_id
            evaluation['segment_index'] = segment_index
            evaluation['source'] = source
            evaluation['target'] = target
            
            # Add context note
            if context_before or context_after:
                start_id = context_before[0]['id'] if context_before else segment_id
                end_id = context_after[-1]['id'] if context_after else segment_id
                evaluation['context_note'] = f"cross-segment (analyzed {start_id}-{end_id})"
            else:
                evaluation['context_note'] = "segment-only"
            
            # Add model info
            evaluation['model'] = f"openai:{self.model}"
            
            return evaluation
    
    async def _call_api_with_retry(self, messages: List[Dict], config: dict,
                                   max_retries: int = 5) -> Dict[str, Any]:
        """Call API with exponential backoff and jitter."""
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Extract source length from messages for adaptive token limits
                source_length = len(messages[-1]['content']) if messages else 0
                api_params = self._build_api_params(messages, config, source_length)
                response = await self.client.chat.completions.create(**api_params)
                
                # Parse response
                result_text = response.choices[0].message.content
                evaluation = self._parse_response(result_text)
                
                return evaluation
                
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    raise
                
                # Extract retry_after if available
                retry_after = getattr(e, 'retry_after', None)
                if retry_after:
                    delay = float(retry_after)
                else:
                    # Exponential backoff with jitter
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                
                # Cap at 60 seconds
                delay = min(delay, 60.0)
                await asyncio.sleep(delay)
                
            except APIError as e:
                error_msg = str(e)
                
                # Don't retry on 400 bad request
                if '400' in error_msg:
                    return self._error_evaluation(f"API request error: {e}")
                
                # Retry on server errors (5xx)
                if any(code in error_msg for code in ['500', '502', '503', '504']):
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        await asyncio.sleep(min(delay, 60.0))
                        continue
                
                # Don't retry other errors
                return self._error_evaluation(f"API error: {e}")
            
            except Exception as e:
                return self._error_evaluation(f"Unexpected error: {e}")
        
        return self._error_evaluation("Max retries exceeded")
    
    def _get_token_param_name(self) -> str:
        """Get correct token parameter name for model."""
        if self.model.startswith('gpt-5') or self.model.startswith('gpt-4.1'):
            return 'max_completion_tokens'
        return 'max_tokens'
    
    def _get_token_limit(self, config: dict, source_length: int = 0) -> int:
        """Get token limit with adaptive sizing based on segment complexity."""
        # Check if explicitly set in config
        token_limit = (config['llm_provider'].get('max_completion_tokens') or 
                      config['llm_provider'].get('max_output_tokens') or 
                      config['llm_provider'].get('max_tokens'))
        
        if token_limit:
            return int(token_limit)
        
        # Adaptive limit based on source segment length
        # Short segments need less explanation
        if source_length < 50:
            return 250  # Minimal response
        elif source_length < 150:
            return 350  # Standard response
        else:
            return 500  # Complex segment, more explanation needed
    
    def _build_api_params(self, messages: List[Dict], config: dict, source_length: int = 0) -> Dict[str, Any]:
        """Build API parameters with correct token parameter name."""
        token_limit = self._get_token_limit(config, source_length)
        token_param = self._get_token_param_name()
        
        api_params = {
            'model': self.model,
            'messages': messages,
            token_param: token_limit
        }
        
        # Only add temperature for models that support custom values
        if not self.model.startswith('gpt-5-mini'):
            temperature = config['llm_provider'].get('temperature')
            if temperature is not None:
                api_params['temperature'] = float(temperature)
        
        return api_params
    
    def _build_prompt(self, source: str, target: str,
                     context_before: List[Dict], context_after: List[Dict],
                     template: str, config: dict) -> str:
        """Build the evaluation prompt with optimized context."""
        
        # Get optimization settings from config
        opt = config.get('context_optimization', {})
        MAX_CONTEXT_CHARS = opt.get('max_chars_per_segment', 200)
        MAX_NEIGHBORS = opt.get('max_neighbors_per_side', 4)
        MIN_LENGTH = opt.get('min_segment_length', 3)
        
        # Format context - SOURCE ONLY, truncated
        context_before_text = ""
        if context_before:
            # Take only the most recent N segments
            relevant_before = context_before[-min(len(context_before), MAX_NEIGHBORS):]
            
            context_parts = []
            for seg in relevant_before:
                source_text = seg['source'].strip()
                
                # Skip empty or very short segments (low signal)
                if len(source_text) < 3:
                    continue
                
                # Truncate to character limit
                if len(source_text) > MAX_CONTEXT_CHARS:
                    source_text = source_text[:MAX_CONTEXT_CHARS] + "..."
                
                context_parts.append(f"  [{seg['id']}] {source_text}")
            
            if context_parts:
                context_before_text = "Previous segments (for reference):\n" + "\n".join(context_parts)
        
        context_after_text = ""
        if context_after:
            # Take only the first N segments
            relevant_after = context_after[:min(len(context_after), MAX_NEIGHBORS)]
            
            context_parts = []
            for seg in relevant_after:
                source_text = seg['source'].strip()
                
                # Skip empty or very short segments
                if len(source_text) < 3:
                    continue
                
                # Truncate to character limit
                if len(source_text) > MAX_CONTEXT_CHARS:
                    source_text = source_text[:MAX_CONTEXT_CHARS] + "..."
                
                context_parts.append(f"  [{seg['id']}] {source_text}")
            
            if context_parts:
                context_after_text = "Following segments (for reference):\n" + "\n".join(context_parts)
        
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
        """Parse LLM response into structured evaluation."""
        try:
            # Extract JSON from response
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
            
        except json.JSONDecodeError:
            return self._error_evaluation(f"Response parsing failed: {response_text[:200]}")
    
    def _error_evaluation(self, error_msg: str) -> Dict[str, Any]:
        """Create error evaluation result."""
        return {
            'error': error_msg,
            'overall_score': None,
            'dimensions': {
                'accuracy': 50,
                'fluency': 50,
                'style': 50,
                'context_coherence': 50
            },
            'issues': [{
                'type': 'evaluation_error',
                'severity': 'major',
                'description': error_msg
            }],
            'explanation': error_msg,
            'confidence': 0
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