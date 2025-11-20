"""
XLIFF 2.2 Converter - Convert aligned multilingual text files to XLIFF 2.2
Simplified version - manual language code entry
"""

import streamlit as st
from pathlib import Path
import sys
from typing import List, Dict, Tuple
import os

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core.text_parser import TextParser
from core.xliff_generator import XLIFFGenerator

st.set_page_config(
    page_title="XLIFF 2.2 Converter",
    page_icon="🔄",
    layout="wide"
)

def main():
    st.title("🔄 XLIFF 2.2 Converter")
    st.markdown("Convert aligned multilingual text files to XLIFF 2.2 format")
    
    # Initialize session state
    if 'files_processed' not in st.session_state:
        st.session_state.files_processed = []
    if 'parsed_data' not in st.session_state:
        st.session_state.parsed_data = None
    
    # File upload
    st.header("1. Select Files")
    uploaded_files = st.file_uploader(
        "Upload text files with aligned translations",
        type=['txt'],
        accept_multiple_files=True,
        help="Each file should contain aligned translations separated by blank lines"
    )
    
    if uploaded_files:
        st.success(f"✓ {len(uploaded_files)} file(s) selected")
        
        # Parse first file to determine number of languages
        if st.button("📝 Parse Files", type="primary"):
            parse_first_file(uploaded_files)
        
        # Show language configuration if parsed
        if st.session_state.parsed_data:
            show_language_config()
    
    # Show processing history
    if st.session_state.files_processed:
        st.header("Processing Results")
        for result in st.session_state.files_processed:
            with st.expander(f"{'✓' if result['status'] == 'Success' else '❌'} {result['filename']}", expanded=False):
                st.write(f"**Status:** {result['status']}")
                if result.get('output_path'):
                    st.write(f"**Output:** {result['output_path']}")
                if result.get('segments'):
                    st.write(f"**Segments:** {result['segments']}")
                if result.get('error'):
                    st.error(result['error'])


def parse_first_file(uploaded_files):
    """Parse first file to determine number of languages"""
    parser = TextParser()
    
    first_file = uploaded_files[0]
    content = first_file.read().decode('utf-8')
    first_file.seek(0)  # Reset for later processing
    
    try:
        groups = parser.parse_text(content)
        if not groups:
            st.error(f"❌ No aligned groups found in {first_file.name}")
            return
        
        # Validate alignment
        is_valid, error = parser.validate_alignment(groups)
        if not is_valid:
            st.error(f"❌ {error}")
            return
        
        num_languages = len(groups[0])
        
        st.session_state.parsed_data = {
            'files': uploaded_files,
            'num_languages': num_languages,
            'num_segments': len(groups)
        }
        
        st.success(f"✓ Parsed successfully: {num_languages} languages, {len(groups)} segments")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error parsing {first_file.name}: {str(e)}")


def show_language_config():
    """Display language configuration form"""
    data = st.session_state.parsed_data
    num_languages = data['num_languages']
    
    st.header("2. Configure Languages")
    
    st.info(f"Your files contain {num_languages} languages per segment group")
    
    # Input language codes
    st.subheader("Enter Language Codes")
    st.caption("Use MS LCID format: en-GB, de-DE, fr-FR, es-ES, etc.")
    
    language_codes = []
    cols = st.columns(min(num_languages, 3))
    
    for idx in range(num_languages):
        col_idx = idx % 3
        with cols[col_idx]:
            code = st.text_input(
                f"Language {idx + 1}",
                value="" if idx >= 3 else ["en-GB", "de-DE", "fr-FR"][idx] if idx < 3 else "",
                key=f"lang_code_{idx}",
                placeholder="e.g., en-GB"
            )
            language_codes.append(code)
    
    # Validate codes
    all_valid = all(validate_lcid_code(code) for code in language_codes if code)
    all_filled = all(code.strip() for code in language_codes)
    
    if not all_filled:
        st.warning("⚠️ Please enter all language codes")
        return
    
    if not all_valid:
        st.error("❌ Invalid language code format. Use format: xx-YY (e.g., en-GB, de-DE)")
        return
    
    # Source language selection
    st.subheader("3. Select Source Language")
    
    lang_options = [f"{code} (Language {idx + 1})" for idx, code in enumerate(language_codes)]
    source_idx = st.selectbox(
        "Which language is the source?",
        options=range(len(lang_options)),
        format_func=lambda x: lang_options[x],
        key="source_lang_select"
    )
    
    source_lang = language_codes[source_idx]
    
    # Target language selection
    st.subheader("4. Select Target Language")
    st.caption("Enter the primary target language code (e.g., de-DE, fr-FR)")
    
    target_lang = st.text_input(
        "Target language code",
        value="de-DE",
        key="target_lang_input",
        placeholder="e.g., de-DE"
    )
    
    # Validate target language format
    if not validate_lcid_code(target_lang):
        st.error("❌ Invalid target language code format. Use format: xx-YY (e.g., de-DE, fr-FR)")
        return
    
    # Output options
    st.header("5. Output Options")
    
    col1, col2 = st.columns(2)
    with col1:
        overwrite_option = st.radio(
            "If output file exists:",
            options=["Overwrite", "Rename", "Skip"],
            key="overwrite_option"
        )
    
    with col2:
        output_folder = st.text_input(
            "Output folder (leave empty for same folder)",
            value="",
            key="output_folder",
            placeholder="e.g., C:\\Output or leave empty"
        )
    
    # Convert button
    if st.button("✨ Convert to XLIFF 2.0", type="primary"):
        convert_files(
            data['files'],
            language_codes,
            source_lang,
            target_lang,
            overwrite_option,
            output_folder
        )


def validate_lcid_code(code: str) -> bool:
    """Validate LCID code format: xx-YY"""
    if not code or '-' not in code:
        return False
    
    parts = code.split('-')
    if len(parts) != 2:
        return False
    
    lang_code, region_code = parts
    
    if len(lang_code) != 2 or len(region_code) != 2:
        return False
    
    if not lang_code.islower() or not region_code.isupper():
        return False
    
    return True


def convert_files(uploaded_files, languages, source_lang, target_lang, overwrite_option, output_folder):
    """Convert all files to XLIFF 2.0"""
    parser = TextParser()
    generator = XLIFFGenerator()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    st.session_state.files_processed = []
    
    for idx, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Processing {uploaded_file.name}...")
        
        try:
            # Parse content
            content = uploaded_file.read().decode('utf-8')
            groups = parser.parse_text(content)
            
            if not groups:
                st.session_state.files_processed.append({
                    'filename': uploaded_file.name,
                    'status': 'Skipped',
                    'error': 'No aligned groups found'
                })
                continue
            
            # Validate alignment
            expected_count = len(languages)
            for group_idx, group in enumerate(groups):
                if len(group) != expected_count:
                    raise ValueError(
                        f"Alignment error: Group {group_idx + 1} has {len(group)} lines, "
                        f"expected {expected_count}"
                    )
            
            # Generate XLIFF
            xliff_content = generator.generate_xliff(
                groups=groups,
                languages=languages,
                source_lang=source_lang,
                target_lang=target_lang,
                filename=uploaded_file.name
            )
            
            # Determine output path
            if output_folder:
                output_dir = Path(output_folder)
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = Path(".")
            
            base_name = Path(uploaded_file.name).stem
            output_path = output_dir / f"{base_name}.xlf"
            
            # Handle existing file
            if output_path.exists():
                if overwrite_option == "Skip":
                    st.session_state.files_processed.append({
                        'filename': uploaded_file.name,
                        'status': 'Skipped',
                        'error': 'File already exists'
                    })
                    continue
                elif overwrite_option == "Rename":
                    counter = 1
                    while output_path.exists():
                        output_path = output_dir / f"{base_name}_{counter}.xlf"
                        counter += 1
            
            # Write XLIFF file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xliff_content)
            
            st.session_state.files_processed.append({
                'filename': uploaded_file.name,
                'status': 'Success',
                'output_path': str(output_path),
                'segments': len(groups)
            })
            
        except Exception as e:
            st.session_state.files_processed.append({
                'filename': uploaded_file.name,
                'status': 'Error',
                'error': str(e)
            })
        
        progress_bar.progress((idx + 1) / len(uploaded_files))
    
    status_text.text("✓ Processing complete!")
    st.rerun()


if __name__ == "__main__":
    main()