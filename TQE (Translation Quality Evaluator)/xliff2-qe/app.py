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
from core.api_cache import APICredentialCache
from prompts.templates import PromptTemplateManager
from reports.enhanced_report import create_evaluation_report

# Ensure outputs directory exists
Path("./outputs").mkdir(exist_ok=True)

# Load environment variables
load_dotenv()

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
    
    # Content type
    content_type = st.selectbox(
        "Content Type",
        ["general", "technical_documentation", "marketing", "legal", "ui_strings"]
    )
    
    # Context window
    context_window = st.slider(
        "Context Window",
        min_value=0,
        max_value=10,
        value=5,
        help="Number of segments before/after for context"
    )

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
                        provider = AsyncOpenAIProvider(api_key=api_key, model=model, max_concurrent=50)
                        config = get_default_config()
                        config['context_window_size'] = context_window
                    
                    # Update config for this file's language pair
                    config['language_pair']['source'] = metadata['source_language']
                    config['language_pair']['target'] = metadata['target_language']
                    
                    if operation == "Translate (no context)":
                        # Translation without references
                        async def translate_no_context():
                            return await provider.translate_segments_batch(
                                segments,
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
                            st.success(f"✅ {uploaded_file.name}: Translated {len(segments)} segments → {output_path.name}")
                    
                    elif operation == "Translate (with context)":
                        # Translation with reference translations
                        async def translate_with_context():
                            return await provider.translate_segments_batch(
                                segments,
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
                            st.success(f"✅ {uploaded_file.name}: Translated {len(segments)} segments with context → {output_path.name}")
                    
                    elif operation == "Evaluate":
                        # Evaluation
                        # Build segments with context
                        segments_with_context = []
                        for i, segment in enumerate(segments):
                            # Get context before and after
                            context_before = segments[max(0, i - context_window):i]
                            context_after = segments[i + 1:min(len(segments), i + 1 + context_window)]
                            
                            segments_with_context.append({
                                'segment_id': segment['id'],
                                'segment_index': i,
                                'source': segment['source'],
                                'target': segment['target'],
                                'context_before': context_before,
                                'context_after': context_after
                            })
                        
                        # Get appropriate prompt template
                        template_manager = PromptTemplateManager()
                        prompt_template = template_manager.get_template(content_type)
                        
                        # Run evaluation
                        async def evaluate():
                            return await provider.evaluate_segments_batch(
                                segments_with_context,
                                prompt_template,
                                config
                            )
                        
                        results = asyncio.run(evaluate())
                        
                        # Save JSON results
                        json_filename = f"{Path(uploaded_file.name).stem}_evaluation.json"
                        json_path = Path(f"./outputs/{json_filename}")
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(results, f, indent=2, ensure_ascii=False)
                        
                        # Generate PDF report
                        pdf_filename = f"{Path(uploaded_file.name).stem}_evaluation.pdf"
                        pdf_path = Path(f"./outputs/{pdf_filename}")
                        
                        # Add content_type to config for report
                        report_config = config.copy()
                        report_config['content_type'] = content_type
                        
                        create_evaluation_report(results, pdf_path, report_config, metadata)
                        
                        # Calculate summary statistics
                        valid_scores = [r['overall_score'] for r in results if r['overall_score'] is not None]
                        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
                        
                        with results_container:
                            st.success(f"✅ {uploaded_file.name}: Evaluated {len(segments)} segments (avg: {avg_score:.1f}/100) → {json_path.name}, {pdf_path.name}")
                
                except Exception as e:
                    with results_container:
                        st.error(f"❌ {uploaded_file.name}: {e}")
                
                # Update progress
                progress_bar.progress((file_idx + 1) / total_files)
            
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