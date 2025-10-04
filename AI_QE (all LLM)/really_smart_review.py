#!/usr/bin/env python3
"""
Really Smart Review - LLM-Powered Translation Quality Analysis
Main entry point for folder-based batch processing of SDLXLIFF files.
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Import core modules (these will be separate files)
from core.config import load_config, get_default_config, save_config
from core.xliff_handler import XLIFFHandler
from core.llm_provider import OpenAIProvider
from core.analyzer import SmartReviewAnalyzer
from reports.enhanced_report import create_enhanced_report

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


def print_banner():
    """Print welcome banner."""
    print("=" * 70)
    print("Really Smart Review :-)")
    print("LLM-Powered Translation Quality Analysis")
    print("=" * 70)
    print()


def validate_api_key(api_key):
    """Quick validation that API key looks reasonable."""
    if not api_key:
        return False
    if not api_key.startswith('sk-'):
        print("Warning: OpenAI API keys typically start with 'sk-'")
    if len(api_key) < 20:
        return False
    return True


def process_folder(folder_path, config):
    """Process all SDLXLIFF files in a folder."""
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Error: Folder not found: {folder_path}")
        return
    
    # Find all SDLXLIFF files
    xliff_files = list(folder.glob('*.sdlxliff'))
    
    if not xliff_files:
        print(f"No .sdlxliff files found in {folder_path}")
        return
    
    print(f"Found {len(xliff_files)} SDLXLIFF file(s) to process")
    print()
    
    # Create output folder
    output_path = folder / config.get('output_folder', 'smart_review_results')
    output_path.mkdir(exist_ok=True)
    
    # Initialize LLM provider
    try:
        provider = OpenAIProvider(
            api_key=config['llm_provider']['api_key'],
            model=config['llm_provider']['model'],
            temperature=config['llm_provider'].get('temperature', 0.3)
        )
        
        # Test connection
        print("Testing OpenAI API connection...")
        if not provider.validate_credentials():
            print("Error: Failed to connect to OpenAI API. Check your API key.")
            return
        print("✓ API connection successful")
        print()
        
    except Exception as e:
        print(f"Error initializing OpenAI provider: {e}")
        return
    
    # Initialize analyzer
    analyzer = SmartReviewAnalyzer(provider, config)
    
    # Process each file
    all_results = []
    
    for idx, xliff_file in enumerate(xliff_files, 1):
        print(f"[{idx}/{len(xliff_files)}] Processing: {xliff_file.name}")
        print("-" * 70)
        
        try:
            # Analyze the file
            result = analyzer.analyze_file(xliff_file)
            
            if result:
                all_results.append(result)
                
                # Save annotated XLIFF
                output_xliff = output_path / xliff_file.name
                XLIFFHandler.save_annotated_xliff(
                    xliff_file, 
                    output_xliff, 
                    result['evaluations']
                )
                print(f"✓ Saved annotated XLIFF: {output_xliff.name}")
            
            print()
            
        except Exception as e:
            print(f"Error processing {xliff_file.name}: {e}")
            print()
            continue
    
    # Generate consolidated report
    if all_results:
        print("=" * 70)
        print("Generating comprehensive quality report...")
        print()
        
        report_path = output_path / 'smart_review_report.pdf'
        create_enhanced_report(all_results, report_path, config)
        
        # Save analysis data as JSON for further processing
        json_path = output_path / 'analysis_data.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved analysis data: {json_path.name}")
        
        print()
        print("=" * 70)
        print(f"Processing complete!")
        print(f"Results saved to: {output_path.absolute()}")
        print("=" * 70)
    else:
        print("No files were successfully processed.")


def interactive_setup():
    """Interactive configuration setup."""
    print("Let's set up Really Smart Review")
    print()
    
    # API Key - check environment first
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print("Step 1: OpenAI API Key")
        print(f"✓ Using API key from environment: {api_key[:8]}...")
        print()
    else:
        print("Step 1: OpenAI API Key")
        print("You can find your API key at: https://platform.openai.com/api-keys")
        api_key = input("Enter your OpenAI API key: ").strip()
        
        if not validate_api_key(api_key):
            print("Error: Invalid API key format")
            return None
        print()
    
    # Folder path
    print("Step 2: Source Folder")
    folder_path = input("Enter path to folder containing SDLXLIFF files: ").strip()
    folder_path = folder_path.strip('"').strip("'")
    
    if not Path(folder_path).exists():
        print(f"Error: Folder not found: {folder_path}")
        return None
    
    print()
    
    # Review profile
    print("Step 3: Review Profile")
    print("  1. Quick Scan (fast, segment-only analysis)")
    print("  2. Context Review (recommended - analyzes with surrounding context)")
    print("  3. Deep Analysis (thorough, slower, best quality)")
    
    profile_choice = input("Select profile [1-3] (default: 2): ").strip() or "2"
    
    profile_map = {
        "1": "quick_scan",
        "2": "context_review",
        "3": "deep_analysis"
    }
    
    profile = profile_map.get(profile_choice, "context_review")
    
    print()
    
    # Content type
    print("Step 4: Content Type")
    print("  1. General/Mixed")
    print("  2. Technical Documentation")
    print("  3. Marketing/UX Copy")
    print("  4. Legal/Compliance")
    print("  5. UI Strings")
    
    content_choice = input("Select content type [1-5] (default: 1): ").strip() or "1"
    
    content_map = {
        "1": "general",
        "2": "technical_documentation",
        "3": "marketing",
        "4": "legal",
        "5": "ui_strings"
    }
    
    content_type = content_map.get(content_choice, "general")
    
    print()

    # Model selection
    print("Step 5: Model Selection")
    print("  1. gpt-5-mini (fastest, most cost-effective, fixed temperature)")
    print("  2. gpt-5 (highest quality, more expensive)")
    print("  3. gpt-4o (previous generation, well-tested, customizable)")
    
    model_choice = input("Select model [1-3] (default: 1): ").strip() or "1"
    
    model_map = {
        "1": "gpt-5-mini",
        "2": "gpt-5",
        "3": "gpt-4o"
    }
    
    selected_model = model_map.get(model_choice, "gpt-5-mini")
    
    print()
    
    # Build configuration
    config = get_default_config()
    config['llm_provider']['api_key'] = api_key
    config['llm_provider']['model'] = selected_model
    
    # Add temperature back for models that support it
    if not selected_model.startswith('gpt-5-mini'):
        config['llm_provider']['temperature'] = 0.3
    
    config['review_profile'] = profile
    config['content_type'] = content_type
    
    # Build configuration
    config = get_default_config()
    config['llm_provider']['api_key'] = api_key
    config['review_profile'] = profile
    config['content_type'] = content_type
    
    # Apply profile settings
    if profile == "quick_scan":
        config['context_window'] = 0
    elif profile == "context_review":
        config['context_window'] = 5
    elif profile == "deep_analysis":
        config['context_window'] = 10
        config['enable_document_analysis'] = True
    
    return folder_path, config


def main():
    """Main entry point."""
    print_banner()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
        
        # Try to load config from file or use default
        config_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        
        if config_path and config_path.exists():
            print(f"Loading configuration from: {config_path}")
            config = load_config(config_path)
        else:
            print("Using default configuration")
            print("(Run without arguments for interactive setup)")
            print()
            config = get_default_config()
            
            # Check for API key in environment
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("Error: OPENAI_API_KEY environment variable not set")
                print("Please set it or run without arguments for interactive setup")
                return
            config['llm_provider']['api_key'] = api_key
        
        process_folder(folder_path, config)
    
    else:
        # Interactive mode
        result = interactive_setup()
        
        if result:
            folder_path, config = result
            
            # Ask if user wants to save config
            save_choice = input("\nSave this configuration for future use? [y/N]: ").strip().lower()
            if save_choice == 'y':
                config_name = input("Configuration name (e.g., 'my_project'): ").strip()
                if config_name:
                    config_path = Path.home() / '.smart_review' / f'{config_name}.json'
                    config_path.parent.mkdir(exist_ok=True)
                    save_config(config, config_path)
                    print(f"Configuration saved to: {config_path}")
            
            print()
            print("Starting analysis...")
            print()
            
            process_folder(folder_path, config)


if __name__ == "__main__":
    main()