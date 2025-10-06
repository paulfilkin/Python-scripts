"""
Smart Review Analysis Engine - Async Version.
Orchestrates concurrent evaluation of XLIFF segments using async LLM provider.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List
import statistics

from core.xliff_handler import XLIFFHandler
from core.async_llm_provider import AsyncOpenAIProvider
from prompts.templates import PromptTemplateManager


class SmartReviewAnalyzer:
    """Main analysis engine coordinating segment evaluation with concurrency."""
    
    def __init__(self, provider: AsyncOpenAIProvider, config: Dict[str, Any]):
        """
        Initialize analyzer.
        
        Args:
            provider: Async LLM provider instance
            config: Configuration dictionary
        """
        self.provider = provider
        self.config = config
        self.template_manager = PromptTemplateManager()
    
    def analyze_file(self, xliff_path: Path) -> Dict[str, Any]:
        """
        Analyze entire XLIFF file (sync wrapper for async implementation).
        
        Returns:
            Dictionary containing evaluations, statistics, and metadata
        """
        # Run async analysis in event loop
        return asyncio.run(self._analyze_file_async(xliff_path))
    
    async def _analyze_file_async(self, xliff_path: Path) -> Dict[str, Any]:
        """Async implementation of file analysis."""
        print(f"  Parsing XLIFF file...")
        
        # Parse XLIFF
        data = XLIFFHandler.parse_file(xliff_path)
        segments = data['segments']
        metadata = data['metadata']
        
        print(f"  Found {len(segments)} segments")
        
        # Update config with detected languages
        if self.config['language_pair']['source'] == 'auto':
            self.config['language_pair']['source'] = metadata['source_language']
        if self.config['language_pair']['target'] == 'auto':
            self.config['language_pair']['target'] = metadata['target_language']
        
        # Get prompt template for content type
        prompt_template = self.template_manager.get_template(
            self.config['content_type']
        )
        
        # Prepare all segments with their context
        context_window = self.config['context_window']
        
        print(f"  Analyzing {len(segments)} segments concurrently (context window: ±{context_window})...")
        print(f"  Max concurrent requests: {self.provider.max_concurrent}")
        
        segments_with_context = []
        for idx, segment in enumerate(segments):
            context_before = self._get_context(segments, idx, -context_window, 0)
            context_after = self._get_context(segments, idx, 1, context_window + 1)
            
            segments_with_context.append({
                'source': segment['source'],
                'target': segment['target'],
                'segment_id': segment['id'],
                'segment_index': idx,
                'context_before': context_before,
                'context_after': context_after
            })
        
        # Process all segments concurrently with progress updates
        evaluations = await self._evaluate_with_progress(
            segments_with_context,
            prompt_template
        )
        
        # Add comments where needed
        for evaluation in evaluations:
            should_comment = self._should_add_comment(evaluation)
            
            if should_comment:
                # Generate comment text
                comment = XLIFFHandler.create_comment(evaluation, self.config)
                evaluation['comment'] = comment
                
                # Map severity
                evaluation['trados_severity'] = self._map_severity(evaluation)
        
        print(f"  ✓ Analysis complete")
        
        # Calculate statistics
        stats = self._calculate_statistics(evaluations)
        
        return {
            'file_path': str(xliff_path),
            'file_name': xliff_path.name,
            'metadata': metadata,
            'evaluations': evaluations,
            'statistics': stats,
            'config_used': self.config,
            'parsed_tree': data['tree'],
            'parsed_root': data['root']
        }
    
    async def _evaluate_with_progress(self, segments_with_context: List[Dict],
                                     prompt_template: str) -> List[Dict[str, Any]]:
        """Evaluate segments with progress reporting."""
        total = len(segments_with_context)
        batch_size = 100  # Process in batches for progress updates
        
        all_evaluations = []
        
        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch = segments_with_context[batch_start:batch_end]
            
            print(f"  Processing batch {batch_start+1}-{batch_end}/{total}...", end='\r')
            
            # Evaluate batch concurrently
            batch_results = await self.provider.evaluate_segments_batch(
                batch,
                prompt_template,
                self.config
            )
            
            all_evaluations.extend(batch_results)
        
        print(f"  Processed all {total} segments                    ")
        
        return all_evaluations
    
    def _get_context(self, segments: List[Dict], current_idx: int, 
                    start_offset: int, end_offset: int) -> List[Dict]:
        """
        Get context segments around current segment.
        
        Args:
            segments: All segments
            current_idx: Index of current segment
            start_offset: Relative start position (negative for before)
            end_offset: Relative end position (positive for after)
        """
        start = max(0, current_idx + start_offset)
        end = min(len(segments), current_idx + end_offset)
        
        return segments[start:end]
    
    def _should_add_comment(self, evaluation: Dict[str, Any]) -> bool:
        """Determine if a comment should be added based on config."""
        comment_config = self.config['comment_generation']
        mode = comment_config['add_comments_for']
        
        if mode == 'all':
            return True
        
        score = evaluation.get('overall_score')
        if score is None:
            return True  # Add comment for errors
        
        threshold = comment_config['score_threshold']
        
        if mode == 'issues_only':
            return score < threshold
        
        if mode == 'critical_only':
            # Only add if there are critical issues
            issues = evaluation.get('issues', [])
            return any(i['severity'] == 'critical' for i in issues)
        
        return False
    
    def _map_severity(self, evaluation: Dict[str, Any]) -> str:
        """Map issue severity to Trados severity levels."""
        issues = evaluation.get('issues', [])
        if not issues:
            return 'Low'
        
        severity_map = self.config['comment_generation']['severity_mapping']
        
        # Get highest severity
        severities = [i['severity'] for i in issues]
        if 'critical' in severities:
            return severity_map['critical']
        elif 'major' in severities:
            return severity_map['major']
        else:
            return severity_map['minor']
    
    def _calculate_statistics(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate statistics from evaluations."""
        
        # Filter out error evaluations
        valid_evals = [e for e in evaluations if e.get('overall_score') is not None]
        
        if not valid_evals:
            return {
                'total_segments': len(evaluations),
                'evaluated_segments': 0,
                'error_segments': len(evaluations)
            }
        
        scores = [e['overall_score'] for e in valid_evals]
        
        # Score distribution
        score_ranges = {
            '90-100': 0,
            '80-89': 0,
            '70-79': 0,
            '60-69': 0,
            '50-59': 0,
            '0-49': 0
        }
        
        for score in scores:
            if score >= 90:
                score_ranges['90-100'] += 1
            elif score >= 80:
                score_ranges['80-89'] += 1
            elif score >= 70:
                score_ranges['70-79'] += 1
            elif score >= 60:
                score_ranges['60-69'] += 1
            elif score >= 50:
                score_ranges['50-59'] += 1
            else:
                score_ranges['0-49'] += 1
        
        # Issue categorization
        issue_categories = {}
        for eval in valid_evals:
            for issue in eval.get('issues', []):
                category = issue['type']
                issue_categories[category] = issue_categories.get(category, 0) + 1
        
        # Dimension averages
        dimension_avg = {}
        for dim in ['accuracy', 'fluency', 'style', 'context_coherence']:
            dim_scores = [e['dimensions'].get(dim, 0) for e in valid_evals 
                         if 'dimensions' in e]
            if dim_scores:
                dimension_avg[dim] = sum(dim_scores) / len(dim_scores)
        
        return {
            'total_segments': len(evaluations),
            'evaluated_segments': len(valid_evals),
            'error_segments': len(evaluations) - len(valid_evals),
            'average_score': statistics.mean(scores),
            'median_score': statistics.median(scores),
            'stdev_score': statistics.stdev(scores) if len(scores) > 1 else 0.0,
            'min_score': min(scores),
            'max_score': max(scores),
            'score_distribution': score_ranges,
            'issue_categories': issue_categories,
            'dimension_averages': dimension_avg,
            'segments_needing_review': sum(1 for s in scores if s < 80)
        }
