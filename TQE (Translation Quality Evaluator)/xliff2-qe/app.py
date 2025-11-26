"""
XLIFF 2.0 Quality Evaluation - Streamlit Interface
"""

import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
import json
from datetime import datetime

from core.xliff2_handler import XLIFF2Handler
from core.config import get_default_config
from core.async_llm_provider import AsyncOpenAIProvider
from core.sampling import (
    SAMPLING_STRATEGIES, 
    get_strategy_names, 
    get_strategy_by_name,
    sample_segments,
    format_sampling_summary
)
from prompts.templates import PromptTemplateManager
from reports.enhanced_report import create_evaluation_report
from reports.cross_language_report import load_evaluation_json, extract_statistics, create_cross_language_report


def get_strategy_key(strategy_name: str) -> str:
    """Get strategy key from display name."""
    for key, strategy in SAMPLING_STRATEGIES.items():
        if strategy.name == strategy_name:
            return key
    return 'none'

# Ensure outputs directory exists
Path("./outputs").mkdir(exist_ok=True)

# Load environment variables
load_dotenv()

# Load prompt templates
template_manager = PromptTemplateManager()

st.set_page_config(
    page_title="XLIFF 2.0 Quality Evaluation",
    page_icon="🔍",
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

st.title("🔍 XLIFF 2.0 Translation Quality Evaluation")
st.markdown("---")

# Sidebar - Configuration
with st.sidebar:
    st.header("Configuration")
    
    # Reset button at top
    if st.button("🔄 Clear All & Start Fresh", use_container_width=True):
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.markdown("---")
    
    # API Key - only show if not in env
    env_api_key = os.getenv('OPENAI_API_KEY', '')
    if env_api_key:
        api_key = env_api_key
        st.success("✓ Using API key from environment")
    else:
        api_key = st.text_input(
            "OpenAI API Key",
            value='',
            type="password",
            help="Enter your OpenAI API key"
        )
    
    # Model selection
    model = st.selectbox(
        "Model",
        ["gpt-5-mini", "gpt-5", "gpt-4o"],
        help="gpt-5-mini is fastest and most cost-effective"
    )
    
    # Content type (loaded from prompts/*.md files)
    available_templates = template_manager.list_templates()
    content_type = st.selectbox(
        "Content Type",
        available_templates if available_templates else ["general"],
        help="Add/remove .md files in prompts/ folder to change options"
    )
    
    # Context window
    context_window = st.slider(
        "Context Window",
        min_value=0,
        max_value=10,
        value=0,
        help="Number of surrounding segments for context (0 for software strings, higher for flowing text)"
    )
    
    st.markdown("---")
    st.subheader("API Rate Limiting")
    
    requests_per_second = st.slider(
        "Requests per second",
        min_value=1.0,
        max_value=50.0,
        value=10.0,
        step=1.0,
        help="Limit API calls to prevent rate limiting (lower = more reliable)"
    )
    
    max_concurrent = st.slider(
        "Max concurrent requests",
        min_value=5,
        max_value=50,
        value=25,
        step=5,
        help="Maximum simultaneous API calls (lower = more reliable)"
    )
    
    st.markdown("---")
    st.subheader("Report Settings")
    
    attention_threshold = st.slider(
        "Attention threshold",
        min_value=0,
        max_value=100,
        value=70,
        step=5,
        help="Segments scoring below this threshold will appear in 'Segments Requiring Attention' section of PDF report"
    )
    
    st.markdown("---")
    st.subheader("Sampling")
    
    sampling_strategy = st.selectbox(
        "Sampling strategy",
        get_strategy_names(),
        index=0,
        help="Select sampling approach based on project size and risk"
    )
    
    # Show description for selected strategy
    selected_strategy = get_strategy_by_name(sampling_strategy)
    if selected_strategy:
        st.caption(selected_strategy.description)
    
    # Custom percentage input
    custom_percentage = 15
    if sampling_strategy == "Custom":
        custom_percentage = st.slider(
            "Custom percentage",
            min_value=5,
            max_value=50,
            value=15,
            step=5,
            help="Percentage of segments to sample"
        )
    
    # Minimum sample size
    min_sample_size = st.number_input(
        "Minimum sample size",
        min_value=10,
        max_value=100,
        value=30,
        step=10,
        help="Minimum segments to include regardless of percentage"
    )
    
    # Random seed for reproducibility
    use_fixed_seed = st.checkbox(
        "Use fixed seed (reproducible)",
        value=False,
        help="Use a fixed random seed so the same segments are selected each time"
    )
    
    sampling_seed = None
    if use_fixed_seed:
        sampling_seed = st.number_input(
            "Random seed",
            min_value=0,
            max_value=99999,
            value=42,
            help="Seed value for reproducible sampling"
        )

# Main tabs
main_tab, cross_lang_tab, inspector_tab = st.tabs(["📄 Processing", "🌐 Cross-Language Analysis", "🔬 API Inspector"])

with main_tab:
    # Main area - File upload
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Upload XLIFF Files")
        uploaded_files = st.file_uploader(
            "Choose XLIFF 2.0 files",
            type=['xlf', 'xliff'],
            accept_multiple_files=True,
            help="Upload one or more XLIFF 2.0 files"
        )
    
    with col2:
        st.header("Operation")
        operation = st.radio(
            "Select operation:",
            ["Translate (no context)", "Translate (with context)", "Evaluate"],
            help="Choose what to do with the files"
        )
    
    # Process files
    if uploaded_files:
        st.markdown("---")
        st.subheader(f"File Analysis ({len(uploaded_files)} file(s))")
        
        # For evaluation: add option for consolidated report and file labels
        file_labels = {}
        translation_sources = {}
        consolidate_report = False
        
        if operation == "Evaluate" and len(uploaded_files) > 1:
            st.info("💡 **Tip**: You're evaluating multiple files. Add labels to create a consolidated comparison report.")
            consolidate_report = st.checkbox(
                "Create consolidated comparison report",
                value=True,
                help="Combine all files into one report with comparative analysis"
            )
            
            if consolidate_report:
                st.markdown("**File Labels** (describe how each file was translated):")
                for uploaded_file in uploaded_files:
                    col_label, col_source = st.columns([2, 1])
                    
                    with col_label:
                        default_label = ""
                        if "context" in uploaded_file.name.lower():
                            default_label = "Translated with reference context"
                        elif "translated" in uploaded_file.name.lower():
                            default_label = "Translated without context"
                        
                        file_labels[uploaded_file.name] = st.text_input(
                            f"Label for {uploaded_file.name}",
                            value=default_label,
                            key=f"label_{uploaded_file.name}",
                            help="Brief description of translation method"
                        )
                    
                    with col_source:
                        # Auto-detect source type from filename
                        default_source = ''
                        name_upper = uploaded_file.name.upper()
                        if '-HT' in name_upper or '_HT' in name_upper:
                            default_source = 'HT'
                        elif '-MT' in name_upper or '_MT' in name_upper:
                            default_source = 'MT'
                        elif '-AI' in name_upper or '_AI' in name_upper or 'GPT' in name_upper:
                            default_source = 'AI'
                        elif '-MLT' in name_upper or '_MLT' in name_upper:
                            default_source = 'MLT'
                        
                        translation_sources[uploaded_file.name] = st.selectbox(
                            "Source type",
                            options=['', 'MT', 'AI', 'HT', 'MLT', 'Other'],
                            index=['', 'MT', 'AI', 'HT', 'MLT', 'Other'].index(default_source) if default_source in ['', 'MT', 'AI', 'HT', 'MLT', 'Other'] else 0,
                            key=f"source_{uploaded_file.name}",
                            help="MT=Machine, AI=LLM, HT=Human"
                        )
        
        # Show summary of all files
        for uploaded_file in uploaded_files:
            temp_path = Path(f"/tmp/{uploaded_file.name}")
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            try:
                data = XLIFF2Handler.parse_file(temp_path)
                segments = data['segments']
                metadata = data['metadata']
                
                with st.expander(f"📄 {uploaded_file.name}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Source", metadata['source_language'])
                    with col2:
                        st.metric("Target", metadata['target_language'])
                    with col3:
                        st.metric("Segments", len(segments))
                    
                    # Show first segment
                    if segments:
                        st.text(f"First segment: {segments[0]['source'][:80]}...")
            except Exception as e:
                st.error(f"❌ {uploaded_file.name}: {e}")
        
        st.markdown("---")
        
        # Action button
        if st.button("🚀 Start Processing All Files", type="primary"):
            if not api_key:
                st.error("Please enter your OpenAI API key in the sidebar.")
            else:
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.container()
                
                total_files = len(uploaded_files)
                provider = None
                config = None
                
                # For consolidated reports: collect all evaluation results
                consolidated_evaluations = [] if (operation == "Evaluate" and consolidate_report) else None
                
                for file_idx, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processing {file_idx + 1}/{total_files}: {uploaded_file.name}")
                    
                    # Save uploaded file temporarily
                    temp_path = Path(f"/tmp/{uploaded_file.name}")
                    with open(temp_path, 'wb') as f:
                        f.write(uploaded_file.getvalue())
                    
                    # Parse XLIFF
                    try:
                        data = XLIFF2Handler.parse_file(temp_path)
                        segments = data['segments']
                        metadata = data['metadata']
                        
                        # Initialize provider once
                        if provider is None:
                            provider = AsyncOpenAIProvider(
                                api_key=api_key, 
                                model=model, 
                                max_concurrent=max_concurrent,
                                requests_per_second=requests_per_second
                            )
                            # Clear any previous captured calls
                            provider.clear_captured_calls()
                            config = get_default_config()
                            config['context_window_size'] = context_window
                        
                        # Update config for this file's language pair
                        config['language_pair']['source'] = metadata['source_language']
                        config['language_pair']['target'] = metadata['target_language']
                        
                        # Apply sampling
                        strategy_key = get_strategy_key(sampling_strategy)
                        sampled_segments, sampling_info = sample_segments(
                            segments,
                            strategy_key=strategy_key,
                            custom_percentage=custom_percentage,
                            min_sample_size=min_sample_size,
                            seed=sampling_seed
                        )
                        
                        # Show sampling info for translation operations only
                        # (Evaluation shows its own sampling info after filtering valid segments)
                        if sampling_info['sampled'] and operation != "Evaluate":
                            with results_container:
                                st.info(f"📊 {format_sampling_summary(sampling_info)}")
                        
                        if operation == "Translate (no context)":
                            # Translation without references
                            async def translate_no_context():
                                return await provider.translate_segments_batch(
                                    sampled_segments,
                                    metadata['source_language'],
                                    metadata['target_language'],
                                    use_references=False
                                )
                            
                            results = asyncio.run(translate_no_context())
                            
                            # Inject translations into XLIFF
                            translations = [
                                {'segment_id': r['segment_id'], 'translation': r['translation']}
                                for r in results
                            ]
                            XLIFF2Handler.inject_targets(data['tree'], data['root'], translations)
                            
                            # Save modified XLIFF
                            output_filename = f"{Path(uploaded_file.name).stem}_translated.xlf"
                            output_path = Path(f"./outputs/{output_filename}")
                            XLIFF2Handler.save_xliff(data['tree'], output_path)
                            
                            with results_container:
                                st.success(f"✅ {uploaded_file.name}: Translated {len(sampled_segments)} segments → {output_path.name}")
                        
                        elif operation == "Translate (with context)":
                            # Translation with reference translations
                            async def translate_with_context():
                                return await provider.translate_segments_batch(
                                    sampled_segments,
                                    metadata['source_language'],
                                    metadata['target_language'],
                                    use_references=True
                                )
                            
                            results = asyncio.run(translate_with_context())
                            
                            # Inject translations into XLIFF
                            translations = [
                                {'segment_id': r['segment_id'], 'translation': r['translation']}
                                for r in results
                            ]
                            XLIFF2Handler.inject_targets(data['tree'], data['root'], translations)
                            
                            # Save modified XLIFF
                            output_filename = f"{Path(uploaded_file.name).stem}_translated_context.xlf"
                            output_path = Path(f"./outputs/{output_filename}")
                            XLIFF2Handler.save_xliff(data['tree'], output_path)
                            
                            with results_container:
                                st.success(f"✅ {uploaded_file.name}: Translated {len(sampled_segments)} segments with context → {output_path.name}")
                        
                        elif operation == "Evaluate":
                            # Evaluation
                            # Build segments with context, excluding failed translations
                            # Note: For evaluation, we first collect all valid segments, then sample
                            all_valid_segments = []
                            skipped_count = 0
                            
                            for i, segment in enumerate(segments):
                                # Skip segments with failed translations
                                if segment['target'] == '[Translation failed]' or '[Translation failed' in segment['target']:
                                    skipped_count += 1
                                    continue
                                
                                # Skip segments with empty targets
                                if not segment['target'] or segment['target'].strip() == '':
                                    skipped_count += 1
                                    continue
                                
                                # Get context before and after (from all segments for proper context)
                                context_before = segments[max(0, i - context_window):i]
                                context_after = segments[i + 1:min(len(segments), i + 1 + context_window)]
                                
                                all_valid_segments.append({
                                    'segment_id': segment['id'],
                                    'segment_index': i,
                                    'source': segment['source'],
                                    'target': segment['target'],
                                    'references': segment.get('references', {}),
                                    'context_before': context_before,
                                    'context_after': context_after
                                })
                            
                            # Show warning if segments were skipped
                            if skipped_count > 0:
                                with results_container:
                                    st.warning(f"⚠️ Skipped {skipped_count} segment(s) with failed/missing translations")
                            
                            # Only evaluate if we have valid segments
                            if not all_valid_segments:
                                with results_container:
                                    st.error(f"❌ {uploaded_file.name}: No valid translations to evaluate")
                                continue
                            
                            # Apply sampling to valid segments for evaluation
                            segments_with_context, eval_sampling_info = sample_segments(
                                all_valid_segments,
                                strategy_key=strategy_key,
                                custom_percentage=custom_percentage,
                                min_sample_size=min_sample_size,
                                seed=sampling_seed
                            )
                            
                            # Show sampling info for evaluation
                            if eval_sampling_info['sampled']:
                                with results_container:
                                    st.info(f"📊 Evaluation: {format_sampling_summary(eval_sampling_info)}")
                            
                            # Get appropriate prompt template
                            prompt_template = template_manager.get_template(content_type)
                            
                            # Run evaluation
                            async def evaluate():
                                return await provider.evaluate_segments_batch(
                                    segments_with_context,
                                    prompt_template,
                                    config
                                )
                            
                            results = asyncio.run(evaluate())
                            
                            # Save JSON results with metadata and sampling info
                            json_filename = f"{Path(uploaded_file.name).stem}_evaluation.json"
                            json_path = Path(f"./outputs/{json_filename}")
                            
                            # Include metadata and sampling info in output
                            output_data = {
                                'metadata': {
                                    'source_language': metadata['source_language'],
                                    'target_language': metadata['target_language'],
                                    'source_file': uploaded_file.name,
                                    'evaluated_at': datetime.now().isoformat(),
                                    'model': model,
                                    'content_type': content_type,
                                    'translation_source': translation_sources.get(uploaded_file.name, ''),
                                    'label': file_labels.get(uploaded_file.name, '')
                                },
                                'sampling': {
                                    'strategy': eval_sampling_info['strategy'],
                                    'sampled': eval_sampling_info['sampled'],
                                    'total_valid_segments': eval_sampling_info['total_segments'],
                                    'evaluated_segments': eval_sampling_info['sampled_segments'],
                                    'percentage': eval_sampling_info['percentage'],
                                    'seed': eval_sampling_info.get('seed')
                                },
                                'results': results
                            }
                            
                            with open(json_path, 'w', encoding='utf-8') as f:
                                json.dump(output_data, f, indent=2, ensure_ascii=False)
                            
                            # If consolidating, collect results
                            if consolidated_evaluations is not None:
                                file_label = file_labels.get(uploaded_file.name, uploaded_file.name)
                                consolidated_evaluations.append({
                                    'filename': uploaded_file.name,
                                    'label': file_label,
                                    'results': results,
                                    'metadata': metadata,
                                    'sampling_info': eval_sampling_info
                                })
                            else:
                                # Generate individual PDF report
                                pdf_filename = f"{Path(uploaded_file.name).stem}_evaluation.pdf"
                                pdf_path = Path(f"./outputs/{pdf_filename}")
                                
                                # Add content_type, attention_threshold, and sampling to config for report
                                report_config = config.copy()
                                report_config['content_type'] = content_type
                                report_config['attention_threshold'] = attention_threshold
                                report_config['sampling_info'] = eval_sampling_info
                                
                                create_evaluation_report(results, pdf_path, report_config, metadata)
                            
                            # Calculate summary statistics
                            valid_scores = [r['overall_score'] for r in results if r['overall_score'] is not None]
                            avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
                            
                            with results_container:
                                if consolidated_evaluations is not None:
                                    st.success(f"✅ {uploaded_file.name}: Evaluated {len(segments_with_context)} segments (avg: {avg_score:.1f}/100) → {json_path.name}")
                                else:
                                    st.success(f"✅ {uploaded_file.name}: Evaluated {len(segments_with_context)} segments (avg: {avg_score:.1f}/100) → {json_path.name}, {pdf_filename}")
                    
                    except Exception as e:
                        with results_container:
                            st.error(f"❌ {uploaded_file.name}: {e}")
                    
                    # Update progress
                    progress_bar.progress((file_idx + 1) / total_files)
                
                # Generate consolidated report if requested
                if consolidated_evaluations is not None and len(consolidated_evaluations) > 0:
                    status_text.text("Generating consolidated comparison report...")
                    
                    # Prepare config for consolidated report
                    report_config = config.copy()
                    report_config['content_type'] = content_type
                    report_config['attention_threshold'] = attention_threshold
                    
                    # Generate consolidated PDF
                    consolidated_pdf_path = Path("./outputs/consolidated_comparison_report.pdf")
                    
                    from reports.consolidated_report import create_consolidated_report
                    create_consolidated_report(consolidated_evaluations, consolidated_pdf_path, report_config)
                    
                    with results_container:
                        st.success(f"📊 Consolidated comparison report → {consolidated_pdf_path.name}")
                
                # Store provider in session state for inspector tab
                if provider is not None:
                    st.session_state['captured_calls'] = {
                        'translate_no_context': provider.get_captured_call('translate_no_context'),
                        'translate_with_context': provider.get_captured_call('translate_with_context'),
                        'evaluate': provider.get_captured_call('evaluate')
                    }
                
                status_text.text(f"✅ Completed {total_files} file(s)")
                st.balloons()
    
    else:
        st.info("👆 Upload XLIFF 2.0 files to get started")
        
        # Show example structure
        with st.expander("Expected XLIFF 2.0 Format"):
            st.code("""<?xml version='1.0' encoding='utf-8'?>
<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" 
       xmlns:mda="urn:oasis:names:tc:xliff:metadata:2.0" 
       version="2.0" srcLang="en-GB" trgLang="ro-RO">
  <file id="..." original="...">
    <unit id="1">
      <mda:metadata>
        <mda:metaGroup category="reference-translations">
          <mda:meta type="ref-de-DE">German translation</mda:meta>
          <mda:meta type="ref-fr-FR">French translation</mda:meta>
        </mda:metaGroup>
      </mda:metadata>
      <segment id="1">
        <source>Source text</source>
        <target>Target text (optional)</target>
      </segment>
    </unit>
  </file>
</xliff>""", language="xml")

# Cross-Language Analysis Tab
with cross_lang_tab:
    st.header("🌐 Cross-Language Analysis")
    st.markdown("Upload multiple evaluation JSON files to create comparative reports across languages and translation sources.")
    
    st.markdown("---")
    
    # File upload
    json_files = st.file_uploader(
        "Upload evaluation JSON files",
        type=['json'],
        accept_multiple_files=True,
        help="Upload JSON files from previous evaluations",
        key="cross_lang_upload"
    )
    
    if json_files:
        st.subheader(f"Loaded {len(json_files)} file(s)")
        
        # Process and display each file
        evaluations = []
        
        for json_file in json_files:
            try:
                data = json.loads(json_file.read().decode('utf-8'))
                json_file.seek(0)  # Reset for potential re-read
                
                stats = extract_statistics(data)
                if stats is None:
                    st.warning(f"⚠️ {json_file.name}: No valid evaluation results")
                    continue
                
                # Extract metadata if present
                file_metadata = data.get('metadata', {})
                
                with st.expander(f"📄 {json_file.name}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    # Allow user to set/override metadata
                    with col1:
                        default_lang = file_metadata.get('target_language', '')
                        # Try to extract from filename if not in metadata
                        if not default_lang:
                            name_lower = json_file.name.lower()
                            lang_hints = {
                                'turkish': 'tr-TR', 'german': 'de-DE', 'french': 'fr-FR',
                                'spanish': 'es-ES', 'italian': 'it-IT', 'portuguese': 'pt-PT',
                                'dutch': 'nl-NL', 'polish': 'pl-PL', 'russian': 'ru-RU',
                                'chinese': 'zh-CN', 'japanese': 'ja-JP', 'korean': 'ko-KR',
                                'arabic': 'ar-SA', 'hebrew': 'he-IL', 'greek': 'el-GR',
                                'hungarian': 'hu-HU', 'romanian': 'ro-RO', 'finnish': 'fi-FI',
                                'norwegian': 'nb-NO', 'swedish': 'sv-SE', 'danish': 'da-DK',
                            }
                            for hint, code in lang_hints.items():
                                if hint in name_lower:
                                    default_lang = code
                                    break
                        
                        language = st.text_input(
                            "Target language",
                            value=default_lang,
                            key=f"lang_{json_file.name}",
                            help="e.g., tr-TR, de-DE, fr-FR"
                        )
                    
                    with col2:
                        default_source = file_metadata.get('translation_source', '')
                        # Try to extract from filename
                        if not default_source:
                            name_upper = json_file.name.upper()
                            if '-HT' in name_upper or '_HT' in name_upper:
                                default_source = 'HT'
                            elif '-MT' in name_upper or '_MT' in name_upper:
                                default_source = 'MT'
                            elif '-AI' in name_upper or '_AI' in name_upper or 'GPT' in name_upper:
                                default_source = 'AI'
                            elif '-MLT' in name_upper or '_MLT' in name_upper:
                                default_source = 'MLT'
                        
                        source_type = st.selectbox(
                            "Translation source",
                            options=['', 'MT', 'AI', 'HT', 'MLT', 'Other'],
                            index=['', 'MT', 'AI', 'HT', 'MLT', 'Other'].index(default_source) if default_source in ['', 'MT', 'AI', 'HT', 'MLT', 'Other'] else 0,
                            key=f"source_{json_file.name}",
                            help="MT=Machine Translation, AI=LLM, HT=Human, MLT=Multi-engine"
                        )
                    
                    with col3:
                        default_label = file_metadata.get('label', '')
                        if not default_label:
                            # Generate from language and source
                            parts = []
                            if language:
                                # Extract language name from code
                                lang_names = {
                                    'tr-TR': 'Turkish', 'de-DE': 'German', 'fr-FR': 'French',
                                    'es-ES': 'Spanish', 'it-IT': 'Italian', 'ro-RO': 'Romanian',
                                    'hu-HU': 'Hungarian', 'el-GR': 'Greek', 'fi-FI': 'Finnish',
                                    'nb-NO': 'Norwegian', 'sv-SE': 'Swedish',
                                }
                                parts.append(lang_names.get(language, language))
                            if source_type:
                                parts.append(source_type)
                            default_label = ' - '.join(parts) if parts else json_file.name
                        
                        label = st.text_input(
                            "Display label",
                            value=default_label,
                            key=f"label_{json_file.name}",
                            help="Label shown in charts"
                        )
                    
                    # Show stats preview
                    st.markdown("**Quick stats:**")
                    metric_cols = st.columns(4)
                    with metric_cols[0]:
                        st.metric("Average", f"{stats['avg_score']:.1f}")
                    with metric_cols[1]:
                        st.metric("Median", f"{stats['median_score']:.1f}")
                    with metric_cols[2]:
                        st.metric("Segments", stats['evaluated_segments'])
                    with metric_cols[3]:
                        st.metric("Need Review", f"{stats['needing_review_pct']:.1f}%")
                
                evaluations.append({
                    'filename': json_file.name,
                    'label': label,
                    'language': language,
                    'source_type': source_type,
                    'data': data,
                    'stats': stats
                })
                
            except Exception as e:
                st.error(f"❌ {json_file.name}: {e}")
        
        if evaluations:
            st.markdown("---")
            
            # Report options
            col1, col2 = st.columns([2, 1])
            with col1:
                report_title = st.text_input(
                    "Report title",
                    value="Cross-Language Quality Analysis",
                    help="Title for the PDF report"
                )
            
            # Generate button
            if st.button("📊 Generate Comparative Report", type="primary", use_container_width=True):
                with st.spinner("Generating charts and report..."):
                    try:
                        output_dir = Path("./outputs")
                        pdf_path, chart_paths = create_cross_language_report(
                            evaluations,
                            output_dir,
                            report_title
                        )
                        
                        st.success(f"✅ Report generated: {pdf_path.name}")
                        
                        # Show charts
                        st.subheader("Generated Charts")
                        
                        for chart_path in chart_paths:
                            if chart_path.exists():
                                st.image(str(chart_path), use_container_width=True)
                                st.caption(chart_path.name)
                        
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"Error generating report: {e}")
                        import traceback
                        st.code(traceback.format_exc())
    
    else:
        st.info("👆 Upload evaluation JSON files to get started")
        
        with st.expander("ℹ️ How to use"):
            st.markdown("""
            1. **Run evaluations** in the Processing tab for different languages/translation sources
            2. **Collect the JSON files** from the `outputs` folder
            3. **Upload them here** to create comparative analysis
            4. **Tag each file** with language and source type (MT, AI, HT, etc.)
            5. **Generate report** to get PDF and chart images
            
            **Tip:** The system tries to auto-detect language and source type from filenames.
            Use naming like `Turkish-MT.json` or `German_AI_evaluation.json` for best results.
            """)

with inspector_tab:
    st.header("🔬 API Inspector")
    st.markdown("View a sample API request and response from the last processing run.")
    
    if 'captured_calls' not in st.session_state:
        st.info("No API calls captured yet. Process some files first.")
    else:
        captured = st.session_state['captured_calls']
        
        # Sub-tabs for each operation type
        op_tabs = st.tabs([
            "Translate (no context)", 
            "Translate (with context)", 
            "Evaluate"
        ])
        
        operation_keys = ['translate_no_context', 'translate_with_context', 'evaluate']
        operation_names = ['Translate (no context)', 'Translate (with context)', 'Evaluate']
        
        for tab, key, name in zip(op_tabs, operation_keys, operation_names):
            with tab:
                call_data = captured.get(key)
                
                if call_data is None:
                    st.info(f"No '{name}' calls captured in the last run.")
                else:
                    st.success(f"✓ Captured one '{name}' API call")
                    
                    # Request section
                    st.subheader("📤 Request")
                    
                    req = call_data['request']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Model:** `{req.get('model', 'N/A')}`")
                    with col2:
                        st.markdown(f"**Token limit:** `{req.get('token_limit', 'N/A')}` ({req.get('token_param', '')})")
                    
                    st.markdown("**Messages:**")
                    for i, msg in enumerate(req.get('messages', [])):
                        with st.expander(f"{msg['role'].capitalize()} message", expanded=(i == len(req.get('messages', [])) - 1)):
                            st.code(msg['content'], language=None)
                    
                    st.markdown("---")
                    
                    # Response section
                    st.subheader("📥 Response")
                    
                    resp = call_data['response']
                    
                    # Usage stats
                    usage = resp.get('usage', {})
                    if any(usage.values()):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Prompt tokens", usage.get('prompt_tokens', 'N/A'))
                        with col2:
                            st.metric("Completion tokens", usage.get('completion_tokens', 'N/A'))
                        with col3:
                            st.metric("Total tokens", usage.get('total_tokens', 'N/A'))
                    
                    # Show response content based on operation type
                    if key in ['translate_no_context', 'translate_with_context']:
                        st.markdown("**Translation:**")
                        st.info(resp.get('translation', 'N/A'))
                        st.markdown(f"**Segment ID:** `{resp.get('segment_id', 'N/A')}`")
                    else:
                        # Evaluation response
                        st.markdown("**Raw response:**")
                        with st.expander("View raw API response", expanded=False):
                            st.code(resp.get('raw_text', 'N/A'), language=None)
                        
                        st.markdown("**Parsed evaluation:**")
                        parsed = resp.get('parsed', {})
                        if parsed:
                            st.json(parsed)
