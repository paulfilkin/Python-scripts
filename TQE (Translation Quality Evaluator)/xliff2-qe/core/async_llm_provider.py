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
    
    def __init__(self, api_key: str, model: str = "gpt-5-mini", max_concurrent: int = 50, 
                 requests_per_second: float = 10.0, batch_delay: float = 0.5):
        """
        Initialize async OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-5-mini, gpt-5, gpt-4o, etc.)
            max_concurrent: Maximum concurrent requests (default: 50)
            requests_per_second: Rate limit for API calls (default: 10/sec)
            batch_delay: Delay between processing batches in seconds (default: 0.5)
        """
        self.api_key = api_key
        self.model = model
        self.max_concurrent = max_concurrent
        self.requests_per_second = requests_per_second
        self.batch_delay = batch_delay
        
        # Rate limiting - don't create lock here, create it lazily
        self.min_request_interval = 1.0 / requests_per_second if requests_per_second > 0 else 0
        self.last_request_time = 0
        self._rate_limit_lock = None  # Create lazily in event loop
        self._semaphore = None  # Create lazily in event loop
        self._current_loop_id = None  # Track which event loop owns our locks
        
        # Initialize async client
        self.client = AsyncOpenAI(api_key=api_key)
        
        # API call capture for transparency
        self._captured_calls = {
            'translate_no_context': None,
            'translate_with_context': None,
            'evaluate': None
        }
        self._capture_lock = None
    
    def _get_or_create_capture_lock(self):
        """Get or create capture lock in current event loop."""
        self._reset_for_new_loop()
        if self._capture_lock is None:
            self._capture_lock = asyncio.Lock()
        return self._capture_lock
    
    def get_captured_call(self, operation: str) -> Optional[Dict[str, Any]]:
        """Get captured API call for an operation."""
        return self._captured_calls.get(operation)
    
    def clear_captured_calls(self):
        """Clear all captured calls."""
        self._captured_calls = {
            'translate_no_context': None,
            'translate_with_context': None,
            'evaluate': None
        }
    
    async def _capture_call(self, operation: str, request: Dict[str, Any], response: Dict[str, Any]):
        """Capture the first successful call for an operation."""
        lock = self._get_or_create_capture_lock()
        async with lock:
            if self._captured_calls.get(operation) is None:
                self._captured_calls[operation] = {
                    'request': request,
                    'response': response
                }
    
    def _reset_for_new_loop(self):
        """Reset locks when we detect a new event loop."""
        try:
            current_loop = id(asyncio.get_event_loop())
            if self._current_loop_id != current_loop:
                self._rate_limit_lock = None
                self._semaphore = None
                self._capture_lock = None
                self._current_loop_id = current_loop
        except RuntimeError:
            pass
    
    def _get_or_create_lock(self):
        """Get or create rate limit lock in current event loop."""
        self._reset_for_new_loop()
        if self._rate_limit_lock is None:
            self._rate_limit_lock = asyncio.Lock()
        return self._rate_limit_lock
    
    def _get_or_create_semaphore(self):
        """Get or create semaphore in current event loop."""
        self._reset_for_new_loop()
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self._semaphore
    
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
                print("API authentication failed: Check your API key")
            else:
                print(f"API validation failed: {e}")
            return False
    
    async def _rate_limit(self):
        """Enforce rate limiting between requests."""
        if self.min_request_interval <= 0:
            return
        
        lock = self._get_or_create_lock()
        async with lock:
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - time_since_last)
            
            self.last_request_time = asyncio.get_event_loop().time()
    
    def _validate_response(self, response_text: str, expected_type: str = "translation") -> bool:
        """
        Validate API response has actual content.
        
        Args:
            response_text: The response text from API
            expected_type: Type of response ("translation" or "evaluation")
        
        Returns:
            True if response is valid, False otherwise
        """
        if not response_text or not response_text.strip():
            return False
        
        # Check for error indicators
        error_indicators = ['[Translation failed', '[ERROR]', 'API error', 'Max retries']
        if any(indicator in response_text for indicator in error_indicators):
            return False
        
        # For evaluations, verify JSON structure
        if expected_type == "evaluation":
            try:
                if "```json" in response_text or "```" in response_text or "{" in response_text:
                    return True
                return False
            except Exception:
                return False
        
        # For translations, check minimum length
        if expected_type == "translation":
            return len(response_text.strip()) >= 1
        
        return True
    
    async def translate_segments_batch(self,
                                      segments: List[Dict[str, Any]],
                                      source_lang: str,
                                      target_lang: str,
                                      use_references: bool = False,
                                      max_batch_retries: int = 2) -> List[Dict[str, Any]]:
        """
        Translate multiple segments concurrently with automatic retry of failures.
        
        Args:
            segments: List of segment dicts with 'id', 'source', and optionally 'references'
            source_lang: Source language code
            target_lang: Target language code
            use_references: Whether to use reference translations as context
            max_batch_retries: Number of times to retry failed segments (default: 2)
        
        Returns:
            List of translation results with 'segment_id' and 'translation'
        """
        # Determine operation type for capture
        operation = 'translate_with_context' if use_references else 'translate_no_context'
        
        all_results = {}  # Use dict to track by segment_id - prevents duplicates on retry
        remaining_segments = segments.copy()
        
        for retry_attempt in range(max_batch_retries + 1):
            if not remaining_segments:
                break
            
            # Show retry status
            if retry_attempt > 0:
                print(f"  Retrying {len(remaining_segments)} failed segments (attempt {retry_attempt + 1}/{max_batch_retries + 1})...")
            
            # Create tasks for current batch
            tasks = []
            for segment in remaining_segments:
                task = self._translate_single_segment(
                    segment['source'],
                    segment['id'],
                    source_lang,
                    target_lang,
                    segment.get('references', {}) if use_references else {},
                    operation
                )
                tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and identify failures
            failed_segments = []
            for idx, result in enumerate(results):
                segment = remaining_segments[idx]
                segment_id = segment['id']
                
                if isinstance(result, Exception):
                    all_results[segment_id] = {
                        'segment_id': segment_id,
                        'translation': '[Translation failed]',
                        'error': str(result)
                    }
                    failed_segments.append(segment)
                else:
                    # Check if translation actually failed
                    if '[Translation failed]' in result.get('translation', ''):
                        all_results[segment_id] = result
                        failed_segments.append(segment)
                    else:
                        # Success - update result (replaces any previous failure)
                        all_results[segment_id] = result
            
            # Prepare for next retry
            if retry_attempt < max_batch_retries:
                remaining_segments = failed_segments
                # Wait a bit before retrying
                if failed_segments:
                    await asyncio.sleep(2.0)
            else:
                # Final attempt - no more retries
                remaining_segments = []
        
        # Convert dict back to list in original order
        final_results = []
        for segment in segments:
            if segment['id'] in all_results:
                final_results.append(all_results[segment['id']])
        
        return final_results
    
    async def evaluate_segments_batch(self,
                                     segments_with_context: List[Dict[str, Any]],
                                     prompt_template: str,
                                     config: dict,
                                     max_batch_retries: int = 2) -> List[Dict[str, Any]]:
        """
        Evaluate multiple segments concurrently with automatic retry of failures.
        
        Args:
            segments_with_context: List of dicts containing segment data and context
            prompt_template: Prompt template for evaluation
            config: Configuration dictionary
            max_batch_retries: Number of times to retry failed segments (default: 2)
        
        Returns:
            List of evaluation results in same order as input
        """
        all_results = {}  # Use dict to track by segment_id - prevents duplicates on retry
        remaining_items = segments_with_context.copy()
        
        for retry_attempt in range(max_batch_retries + 1):
            if not remaining_items:
                break
            
            # Show retry status
            if retry_attempt > 0:
                print(f"  Retrying {len(remaining_items)} failed evaluations (attempt {retry_attempt + 1}/{max_batch_retries + 1})...")
            
            # Create tasks for current batch
            tasks = []
            for item in remaining_items:
                task = self._evaluate_single_segment(
                    item['source'],
                    item['target'],
                    item.get('references', {}),
                    item['context_before'],
                    item['context_after'],
                    item['segment_id'],
                    item['segment_index'],
                    prompt_template,
                    config
                )
                tasks.append(task)
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and identify failures
            failed_items = []
            for idx, result in enumerate(results):
                item = remaining_items[idx]
                segment_id = item['segment_id']
                
                if isinstance(result, Exception):
                    # Create error evaluation
                    all_results[segment_id] = {
                        'segment_id': segment_id,
                        'segment_index': item['segment_index'],
                        'source': item['source'],
                        'target': item['target'],
                        'error': str(result),
                        'overall_score': None,
                        'dimensions': {},
                        'issues': [],
                        'explanation': f"Evaluation failed: {str(result)}",
                        'confidence': 0
                    }
                    failed_items.append(item)
                else:
                    # Check if evaluation actually failed
                    if result.get('overall_score') is None and 'error' in result:
                        all_results[segment_id] = result
                        failed_items.append(item)
                    else:
                        # Success - update result (replaces any previous failure)
                        all_results[segment_id] = result
            
            # Prepare for next retry
            if retry_attempt < max_batch_retries:
                remaining_items = failed_items
                # Wait a bit before retrying
                if failed_items:
                    await asyncio.sleep(2.0)
            else:
                # Final attempt - no more retries
                remaining_items = []
        
        # Convert dict back to list in original order
        final_results = []
        for item in segments_with_context:
            if item['segment_id'] in all_results:
                final_results.append(all_results[item['segment_id']])
        
        return final_results
    
    async def _translate_single_segment(self,
                                       source_text: str,
                                       segment_id: str,
                                       source_lang: str,
                                       target_lang: str,
                                       references: Dict[str, str],
                                       operation: str = 'translate_no_context') -> Dict[str, Any]:
        """Translate a single segment with semaphore control and validation."""
        semaphore = self._get_or_create_semaphore()
        async with semaphore:
            # Apply rate limiting
            await self._rate_limit()
            
            # Build the translation prompt
            if references:
                # With context
                ref_text = "\n".join([f"- {lang}: {text}" for lang, text in references.items()])
                prompt = f"""Translate the following text from {source_lang} to {target_lang}.

For context, here are approved translations of this text in other languages:
{ref_text}

Source text:
{source_text}

Use these reference translations to understand the intended meaning and maintain consistency. Provide only the translation, no explanation."""
            else:
                # No context
                prompt = f"""Translate the following text from {source_lang} to {target_lang}:

{source_text}

Provide only the translation, no explanation."""
            
            # Build messages
            messages = [
                {"role": "system", "content": "You are an expert translator."},
                {"role": "user", "content": prompt}
            ]
            
            # Call API with retry logic and validation
            max_retries = 5  # Increased from 3
            for attempt in range(max_retries):
                try:
                    api_params = {
                        'model': self.model,
                        'messages': messages,
                        self._get_token_param_name(): 500
                    }
                    
                    response = await self.client.chat.completions.create(**api_params)
                    translation = response.choices[0].message.content
                    
                    # Check if we got actual content
                    if not translation:
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1.0 * (attempt + 1))
                            continue
                        else:
                            return {
                                'segment_id': segment_id,
                                'translation': '[Translation failed]',
                                'error': 'Empty response from API after retries'
                            }
                    
                    translation = translation.strip()
                    
                    # Validate response
                    if not self._validate_response(translation, "translation"):
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1.0 * (attempt + 1))
                            continue
                        else:
                            return {
                                'segment_id': segment_id,
                                'translation': '[Translation failed]',
                                'error': 'Invalid response format after retries'
                            }
                    
                    # Capture this successful call
                    await self._capture_call(operation, {
                        'model': self.model,
                        'messages': messages,
                        'token_param': self._get_token_param_name(),
                        'token_limit': 500
                    }, {
                        'translation': translation,
                        'segment_id': segment_id,
                        'usage': {
                            'prompt_tokens': response.usage.prompt_tokens if response.usage else None,
                            'completion_tokens': response.usage.completion_tokens if response.usage else None,
                            'total_tokens': response.usage.total_tokens if response.usage else None
                        }
                    })
                    
                    # Success
                    return {
                        'segment_id': segment_id,
                        'translation': translation
                    }
                
                except RateLimitError as e:
                    if attempt < max_retries - 1:
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        await asyncio.sleep(delay)
                        continue
                    return {
                        'segment_id': segment_id,
                        'translation': '[Translation failed]',
                        'error': f'Rate limit exceeded: {str(e)}'
                    }
                
                except APIError as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2.0 * (attempt + 1))
                        continue
                    return {
                        'segment_id': segment_id,
                        'translation': '[Translation failed]',
                        'error': f'API error: {str(e)}'
                    }
                
                except Exception as e:
                    return {
                        'segment_id': segment_id,
                        'translation': '[Translation failed]',
                        'error': f'Translation failed: {str(e)}'
                    }
            
            return {
                'segment_id': segment_id,
                'translation': '[Translation failed]',
                'error': 'Max retries exceeded'
            }
    
    async def _evaluate_single_segment(self,
                                      source: str,
                                      target: str,
                                      references: Dict[str, str],
                                      context_before: List[Dict],
                                      context_after: List[Dict],
                                      segment_id: str,
                                      segment_index: int,
                                      prompt_template: str,
                                      config: dict) -> Dict[str, Any]:
        """Evaluate a single segment with semaphore control."""
        semaphore = self._get_or_create_semaphore()
        async with semaphore:
            # Build the prompt
            prompt = self._build_prompt(
                source, target,
                references,
                context_before, context_after,
                prompt_template, config
            )
            
            # Build messages
            messages = [
                {"role": "system", "content": "You are an expert translation quality evaluator."},
                {"role": "user", "content": prompt}
            ]
            
            # Call API with retry logic
            evaluation, api_capture = await self._call_api_with_retry_and_capture(messages, config)
            
            # Capture the call if successful
            if api_capture and evaluation.get('overall_score') is not None:
                await self._capture_call('evaluate', api_capture['request'], api_capture['response'])
            
            # Add metadata
            evaluation['segment_id'] = segment_id
            evaluation['segment_index'] = segment_index
            evaluation['source'] = source
            evaluation['target'] = target
            
            # Add context note
            if context_before or context_after:
                start_id = context_before[0]['id'] if context_before else segment_id
                end_id = context_after[-1]['id'] if context_after else segment_id
                evaluation['context_note'] = f"cross-segment (analysed {start_id}-{end_id})"
            else:
                evaluation['context_note'] = "segment-only"
            
            # Add model info
            evaluation['model'] = f"openai:{self.model}"
            
            return evaluation
    
    async def _call_api_with_retry_and_capture(self, messages: List[Dict], config: dict,
                                               max_retries: int = 5) -> tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """Call API with exponential backoff, jitter, rate limiting, and response validation.
        Returns tuple of (evaluation_result, capture_data)."""
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Apply rate limiting
                await self._rate_limit()
                
                # Extract source length from messages for adaptive token limits
                source_length = len(messages[-1]['content']) if messages else 0
                api_params = self._build_api_params(messages, config, source_length)
                response = await self.client.chat.completions.create(**api_params)
                
                # Get response text
                result_text = response.choices[0].message.content
                
                # Validate response before parsing
                if not self._validate_response(result_text, "evaluation"):
                    if attempt < max_retries - 1:
                        # Retry with backoff
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    else:
                        return self._error_evaluation("Empty or invalid response from API"), None
                
                # Parse response
                evaluation = self._parse_response(result_text)
                
                # Validate parsed evaluation has required fields
                if evaluation.get('overall_score') is None and 'error' not in evaluation:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    else:
                        return self._error_evaluation("Parsed evaluation missing required fields"), None
                
                # Prepare capture data
                capture_data = {
                    'request': {
                        'model': self.model,
                        'messages': messages,
                        'token_param': self._get_token_param_name(),
                        'token_limit': api_params.get(self._get_token_param_name())
                    },
                    'response': {
                        'raw_text': result_text,
                        'parsed': evaluation,
                        'usage': {
                            'prompt_tokens': response.usage.prompt_tokens if response.usage else None,
                            'completion_tokens': response.usage.completion_tokens if response.usage else None,
                            'total_tokens': response.usage.total_tokens if response.usage else None
                        }
                    }
                }
                
                return evaluation, capture_data
                
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    return self._error_evaluation(f"Rate limit exceeded after {max_retries} attempts"), None
                
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
                    return self._error_evaluation(f"API request error: {e}"), None
                
                # Retry on server errors (5xx)
                if any(code in error_msg for code in ['500', '502', '503', '504']):
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        await asyncio.sleep(min(delay, 60.0))
                        continue
                
                # Don't retry other errors
                return self._error_evaluation(f"API error: {e}"), None
            
            except Exception as e:
                return self._error_evaluation(f"Unexpected error: {e}"), None
        
        return self._error_evaluation("Max retries exceeded"), None
    
    async def _call_api_with_retry(self, messages: List[Dict], config: dict,
                                   max_retries: int = 5) -> Dict[str, Any]:
        """Call API with exponential backoff, jitter, rate limiting, and response validation."""
        result, _ = await self._call_api_with_retry_and_capture(messages, config, max_retries)
        return result
    
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
                     references: Dict[str, str],
                     context_before: List[Dict], context_after: List[Dict],
                     template: str, config: dict) -> str:
        """Build the evaluation prompt with reference translations and optimised context."""
        
        # Get optimisation settings from config
        opt = config.get('context_optimization', {})
        MAX_CONTEXT_CHARS = opt.get('max_chars_per_segment', 200)
        MAX_NEIGHBORS = opt.get('max_neighbors_per_side', 4)
        
        # Format reference translations - MOST IMPORTANT CONTEXT
        reference_text = ""
        if references:
            ref_parts = []
            for lang, text in references.items():
                ref_parts.append(f"- {lang}: {text}")
            reference_text = "Approved reference translations:\n" + "\n".join(ref_parts)
        
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
            reference_translations=reference_text or "None",
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