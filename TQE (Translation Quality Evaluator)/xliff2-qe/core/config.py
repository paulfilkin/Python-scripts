"""
Configuration management for XLIFF 2.0 QE system.
Handles loading, saving, and validation of configuration profiles.
"""

import json
from pathlib import Path
from typing import Dict, Any


def get_default_config() -> Dict[str, Any]:
    """Return default configuration settings."""
    return {
        "profile_name": "default",
        "content_type": "general",  # general, technical_documentation, marketing, legal, ui_strings
        
        "context_window": 5,  # Number of segments before/after for context
        
        "language_pair": {
            "source": "auto",  # Will be detected from XLIFF
            "target": "auto",
            "enable_language_specific_checks": True
        },

        "context_optimization": {
            "max_chars_per_segment": 200,
            "max_neighbors_per_side": 4,
            "min_segment_length": 3,
            "include_target_in_context": False
        },
        
        "analysis_dimensions": {
            "accuracy": {
                "enabled": True,
                "weight": 40,
                "threshold": 70
            },
            "fluency": {
                "enabled": True,
                "weight": 25,
                "threshold": 75
            },
            "style": {
                "enabled": True,
                "weight": 20,
                "threshold": 70
            },
            "context_coherence": {
                "enabled": True,
                "weight": 15,
                "threshold": 75
            }
        },
        
        "llm_provider": {
            "type": "openai",
            "model": "gpt-5-mini",
            "api_key": "",
            "max_completion_tokens": 2000
        },
        
        "output_folder": "qe_results",
        "generate_pdf_report": True,
        "generate_json_export": True
    }


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        user_config = json.load(f)
    
    # Merge with defaults (user config overrides defaults)
    config = get_default_config()
    config.update(user_config)
    
    return config


def save_config(config: Dict[str, Any], config_path: Path):
    """Save configuration to JSON file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Don't save API key to file for security
    config_to_save = config.copy()
    if 'llm_provider' in config_to_save:
        config_to_save['llm_provider'] = config_to_save['llm_provider'].copy()
        config_to_save['llm_provider']['api_key'] = ""
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_to_save, f, indent=2)


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration settings."""
    required_keys = ['llm_provider', 'context_window', 'analysis_dimensions']
    
    for key in required_keys:
        if key not in config:
            print(f"Error: Missing required config key: {key}")
            return False
    
    # Validate API key
    if not config['llm_provider'].get('api_key'):
        print("Error: OpenAI API key not configured")
        return False
    
    # Validate context window
    if not isinstance(config['context_window'], int) or config['context_window'] < 0:
        print("Error: context_window must be a non-negative integer")
        return False
    
    return True
