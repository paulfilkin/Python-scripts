"""
Sampling module for Translation Quality Evaluation.

Provides percentage-based random sampling strategies for segment selection.
"""

import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SamplingStrategy:
    """Defines a sampling strategy."""
    name: str
    percentage: int
    description: str


# Predefined strategies based on SOP
SAMPLING_STRATEGIES = {
    'none': SamplingStrategy(
        name='None (100%)',
        percentage=100,
        description='Process all segments - use for small files or when full evaluation is required'
    ),
    'quick': SamplingStrategy(
        name='Quick check (10%)',
        percentage=10,
        description='Large projects with known-quality vendor'
    ),
    'standard': SamplingStrategy(
        name='Standard (15%)',
        percentage=15,
        description='New vendor, new domain, or medium risk'
    ),
    'thorough': SamplingStrategy(
        name='Thorough (20%)',
        percentage=20,
        description='High risk or unknown quality'
    ),
    'custom': SamplingStrategy(
        name='Custom',
        percentage=0,  # Set by user
        description='User-defined percentage'
    )
}


def get_strategy_names() -> List[str]:
    """Get list of strategy display names."""
    return [s.name for s in SAMPLING_STRATEGIES.values()]


def get_strategy_by_name(name: str) -> Optional[SamplingStrategy]:
    """Get strategy by display name."""
    for strategy in SAMPLING_STRATEGIES.values():
        if strategy.name == name:
            return strategy
    return None


def sample_segments(
    segments: List[Dict[str, Any]],
    strategy_key: str = 'none',
    custom_percentage: int = 15,
    min_sample_size: int = 30,
    seed: Optional[int] = None
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Sample segments based on the selected strategy.
    
    Args:
        segments: List of segment dictionaries
        strategy_key: Key from SAMPLING_STRATEGIES ('none', 'quick', 'standard', 'thorough', 'custom')
        custom_percentage: Percentage to use if strategy is 'custom'
        min_sample_size: Minimum number of segments to include (if available)
        seed: Random seed for reproducibility (None for random)
    
    Returns:
        Tuple of (sampled_segments, sampling_info)
        sampling_info contains metadata about the sampling for reporting
    """
    total_segments = len(segments)
    
    # Get strategy
    strategy = SAMPLING_STRATEGIES.get(strategy_key, SAMPLING_STRATEGIES['none'])
    percentage = custom_percentage if strategy_key == 'custom' else strategy.percentage
    
    # Calculate sample size
    if percentage >= 100:
        # No sampling - return all
        return segments, {
            'strategy': strategy.name,
            'percentage': 100,
            'total_segments': total_segments,
            'sampled_segments': total_segments,
            'seed': None,
            'sampled': False
        }
    
    # Calculate target sample size
    target_size = max(
        int(total_segments * percentage / 100),
        min(min_sample_size, total_segments)  # Don't exceed total
    )
    
    # Ensure we don't sample more than available
    target_size = min(target_size, total_segments)
    
    # Set seed for reproducibility
    if seed is not None:
        random.seed(seed)
    
    # Random sampling - maintain original order
    indices = sorted(random.sample(range(total_segments), target_size))
    sampled = [segments[i] for i in indices]
    
    # Calculate actual percentage
    actual_percentage = (target_size / total_segments * 100) if total_segments > 0 else 0
    
    sampling_info = {
        'strategy': strategy.name,
        'percentage': round(actual_percentage, 1),
        'target_percentage': percentage,
        'total_segments': total_segments,
        'sampled_segments': target_size,
        'seed': seed,
        'sampled': True,
        'segment_indices': indices
    }
    
    return sampled, sampling_info


def format_sampling_summary(sampling_info: Dict[str, Any]) -> str:
    """Format sampling info for display."""
    if not sampling_info.get('sampled', False):
        return f"All {sampling_info['total_segments']} segments processed"
    
    return (
        f"Sampled {sampling_info['sampled_segments']} of {sampling_info['total_segments']} "
        f"segments ({sampling_info['percentage']}%) using '{sampling_info['strategy']}'"
    )