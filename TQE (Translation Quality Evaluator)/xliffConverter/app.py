"""
XLIFF 2.0 Converter - Convert aligned multilingual text files to XLIFF 2.0
Supports two input formats:
1. Grouped format: blank-line-separated alignment
2. Prefixed format: language codes at start of each line (EN:, JA:, PL:)
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
from core.target_populator import TargetPopulator

st.set_page_config(
    page_title="XLIFF 2.2 Converter",
    page_icon="📄",
    layout="wide"
)

# Mapping of common base codes to full LCID codes
COMMON_LCID_MAP = {
    'EN': 'en-GB',
    'DE': 'de-DE',
    'FR': 'fr-FR',
    'ES': 'es-ES',
    'IT': 'it-IT',
    'PT': 'pt-PT',
    'NL': 'nl-NL',
    'PL': 'pl-PL',
    'RU': 'ru-RU',
    'JA': 'ja-JP',
    'ZH': 'zh-CN',
    'KO': 'ko-KR',
    'AR': 'ar-SA',
    'TR': 'tr-TR',
    'SV': 'sv-SE',
    'DA': 'da-DK',
    'NO': 'nb-NO',
    'FI': 'fi-FI',
    'CS': 'cs-CZ',
    'HU': 'hu-HU',
    'RO': 'ro-RO',
    'UK': 'uk-UA',
    'EL': 'el-GR',
    'HE': 'he-IL',
    'TH': 'th-TH',
    'VI': 'vi-VN',
    'ID': 'id-ID',
    'MS': 'ms-MY',
    'HI': 'hi-IN',
}


def main():
    st.title("📄 XLIFF 2.2 Converter")
    st.markdown("Convert aligned multilingual text files to XLIFF 2.2 format")
    
    # Tabs for different operations
    tab1, tab2 = st.tabs(["📝 Text to XLIFF", "🎯 Populate Targets"])
    
    with tab1:
        show_converter_ui()
    
    with tab2:
        show_target_populator_ui()


def show_converter_ui():
    """Display the text-to-XLIFF converter UI"""
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
        help="Supports grouped format (blank-line separated) or prefixed format (EN:, JA:, etc.)"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) selected")
        
        # Parse first file to determine format and languages
        if st.button("🔍 Parse Files", type="primary"):
            parse_first_file(uploaded_files)
        
        # Show language configuration if parsed
        if st.session_state.parsed_data:
            show_language_config()
    
    # Show processing history
    if st.session_state.files_processed:
        st.header("Processing Results")
        for result in st.session_state.files_processed:
            with st.expander(f"{'✅' if result['status'] == 'Success' else '❌'} {result['filename']}", expanded=False):
                st.write(f"**Status:** {result['status']}")
                if result.get('output_path'):
                    st.write(f"**Output:** {result['output_path']}")
                if result.get('segments'):
                    st.write(f"**Segments:** {result['segments']}")
                if result.get('error'):
                    st.error(result['error'])


def parse_first_file(uploaded_files):
    """Parse first file to determine format and languages"""
    parser = TextParser()
    
    first_file = uploaded_files[0]
    content = first_file.read().decode('utf-8')
    first_file.seek(0)  # Reset for later processing
    
    try:
        # Detect format
        format_type = parser.detect_format(content)
        
        # Parse content
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
        
        # Extract base codes if prefixed format
        base_codes = None
        if format_type == 'prefixed':
            base_codes = parser.extract_language_codes(content)
            if len(base_codes) != num_languages:
                st.warning(f"⚠️ Detected {len(base_codes)} language codes but found {num_languages} languages per group")
        
        st.session_state.parsed_data = {
            'files': uploaded_files,
            'num_languages': num_languages,
            'num_segments': len(groups),
            'format_type': format_type,
            'base_codes': base_codes
        }
        
        format_display = "prefixed (EN:, JA:, etc.)" if format_type == 'prefixed' else "grouped (blank-line separated)"
        st.success(f"✅ Parsed successfully: {format_display}, {num_languages} languages, {len(groups)} segments")
        
        if base_codes:
            st.info(f"📋 Detected language codes: {', '.join(base_codes)}")
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error parsing {first_file.name}: {str(e)}")


def show_language_config():
    """Display language configuration form"""
    data = st.session_state.parsed_data
    num_languages = data['num_languages']
    format_type = data['format_type']
    base_codes = data.get('base_codes')
    
    st.header("2. Configure Languages")
    
    if format_type == 'prefixed' and base_codes:
        st.info(f"📋 Detected {num_languages} languages from prefixes: {', '.join(base_codes)}")
        st.caption("Please qualify each base code to full MS LCID format (e.g., EN → en-GB, JA → ja-JP)")
    else:
        st.info(f"Your files contain {num_languages} languages per segment group")
    
    # Input language codes
    st.subheader("Enter Full Language Codes")
    st.caption("Use MS LCID format: en-GB, de-DE, fr-FR, ja-JP, pl-PL, etc.")
    
    language_codes = []
    cols = st.columns(min(num_languages, 3))
    
    for idx in range(num_languages):
        col_idx = idx % 3
        with cols[col_idx]:
            # Determine default value
            if base_codes and idx < len(base_codes):
                base_code = base_codes[idx]
                default_value = COMMON_LCID_MAP.get(base_code, '')
                label = f"{base_code} → Full Code"
            else:
                default_value = ["en-GB", "de-DE", "fr-FR"][idx] if idx < 3 else ""
                label = f"Language {idx + 1}"
            
            code = st.text_input(
                label,
                value=default_value,
                key=f"lang_code_{idx}",
                placeholder="e.g., en-GB, ja-JP"
            )
            language_codes.append(code)
    
    # Validate codes
    all_valid = all(validate_lcid_code(code) for code in language_codes if code)
    all_filled = all(code.strip() for code in language_codes)
    
    if not all_filled:
        st.warning("⚠️ Please enter all language codes")
        return
    
    if not all_valid:
        st.error("❌ Invalid language code format. Use format: xx-YY (e.g., en-GB, ja-JP, pl-PL)")
        return
    
    # Source language selection
    st.subheader("3. Select Source Language")
    
    if base_codes:
        lang_options = [f"{language_codes[idx]} ({base_codes[idx]})" for idx in range(len(language_codes))]
    else:
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
    st.caption("Enter the primary target language code (e.g., de-DE, fr-FR, ja-JP)")
    
    target_lang = st.text_input(
        "Target language code",
        value="de-DE",
        key="target_lang_input",
        placeholder="e.g., de-DE, ja-JP"
    )
    
    # Validate target language format
    if not validate_lcid_code(target_lang):
        st.error("❌ Invalid target language code format. Use format: xx-YY (e.g., de-DE, ja-JP)")
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
    if st.button("✨ Convert to XLIFF 2.2", type="primary"):
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
    """Convert all files to XLIFF 2.2"""
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
    
    status_text.text("✅ Processing complete!")
    st.rerun()


def show_target_populator_ui():
    """Display the target population UI"""
    st.header("Populate Target Language")
    st.markdown("Add translations from text files into existing XLIFF target elements")
    
    # Initialize session state
    if 'populate_results' not in st.session_state:
        st.session_state.populate_results = []
    
    # File uploads
    st.subheader("1. Upload Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        xliff_file = st.file_uploader(
            "XLIFF file (from converter)",
            type=['xlf', 'xliff'],
            key="xliff_upload",
            help="XLIFF 2.0 file with source and reference translations"
        )
    
    with col2:
        translation_files = st.file_uploader(
            "Translation text file(s)",
            type=['txt'],
            accept_multiple_files=True,
            key="translation_upload",
            help="One or more TXT files with translations (one per line, matching XLIFF segment order)"
        )
    
    if xliff_file and translation_files:
        st.success(f"✅ 1 XLIFF + {len(translation_files)} translation file(s) selected")
        
        # Parse and validate
        st.subheader("2. Set Target Language")
        
        populator = TargetPopulator()
        
        try:
            # Read XLIFF
            xliff_content = xliff_file.read().decode('utf-8')
            xliff_file.seek(0)
            
            # Validate XLIFF
            is_valid, error = populator.validate_xliff_structure(xliff_content)
            if not is_valid:
                st.error(f"❌ Invalid XLIFF: {error}")
                return
            
            # Get XLIFF info
            xliff_info = populator.get_xliff_info(xliff_content)
            
            # Target language input
            col1, col2 = st.columns([2, 1])
            
            with col1:
                target_lang = st.text_input(
                    "Target language code (MS LCID format)",
                    value="tr-TR",
                    key="target_lang_code",
                    placeholder="e.g., tr-TR, de-DE, fr-FR",
                    help="This language code will be applied to all output XLIFF files"
                )
            
            with col2:
                st.metric("XLIFF Segments", xliff_info['total_segments'])
            
            # Validate language code
            if not validate_lcid_code(target_lang):
                st.error("❌ Invalid language code format. Use format: xx-YY (e.g., tr-TR, de-DE)")
                return
            
            # Show XLIFF details
            with st.expander("📋 XLIFF Details"):
                st.write(f"**Version:** {xliff_info.get('version', 'N/A')}")
                st.write(f"**Source Language:** {xliff_info.get('source_lang', 'N/A')}")
                st.write(f"**Current Target Language:** {xliff_info.get('target_lang', 'N/A')} → Will change to {target_lang}")
                st.write(f"**Total Segments:** {xliff_info.get('total_segments', 0)}")
            
            # Validate each translation file
            st.subheader("3. Validate Translation Files")
            
            all_valid = True
            translation_data = []
            
            for trans_file in translation_files:
                trans_content = trans_file.read().decode('utf-8')
                trans_file.seek(0)
                
                translations = populator.parse_translation_file(trans_content)
                
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.text(trans_file.name)
                
                with col2:
                    st.metric("Lines", len(translations))
                
                with col3:
                    if len(translations) == xliff_info['total_segments']:
                        st.success("✅ Match")
                        translation_data.append({
                            'file': trans_file,
                            'content': trans_content,
                            'translations': translations
                        })
                    else:
                        st.error("❌ Mismatch")
                        all_valid = False
            
            if not all_valid:
                st.error(
                    f"❌ Some translation files have incorrect line counts. "
                    f"Expected {xliff_info['total_segments']} lines per file."
                )
                return
            
            # Output options
            st.subheader("4. Output Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                output_suffix = st.text_input(
                    "Output filename suffix",
                    value="_populated",
                    key="output_suffix",
                    help="Will create: original_name[suffix].xlf for each translation file"
                )
            
            with col2:
                output_folder = st.text_input(
                    "Output folder (leave empty for current)",
                    value="",
                    key="populate_output_folder",
                    placeholder="e.g., C:\\Output or leave empty"
                )
            
            # Populate button
            if st.button("✨ Populate All Targets", type="primary"):
                populate_all_targets(
                    xliff_content,
                    translation_data,
                    target_lang,
                    xliff_file.name,
                    output_suffix,
                    output_folder
                )
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Show results
    if st.session_state.populate_results:
        st.subheader("Results")
        
        success_count = sum(1 for r in st.session_state.populate_results if r['status'] == 'Success')
        total_count = len(st.session_state.populate_results)
        
        st.info(f"✅ {success_count}/{total_count} files processed successfully")
        
        for result in st.session_state.populate_results:
            status_icon = "✅" if result['status'] == 'Success' else "❌"
            with st.expander(f"{status_icon} {result['filename']}", expanded=False):
                st.write(f"**Status:** {result['status']}")
                if result.get('output_path'):
                    st.success(f"**Output:** {result['output_path']}")
                if result.get('targets_added'):
                    st.info(f"**Targets Added:** {result['targets_added']}")
                if result.get('target_lang'):
                    st.info(f"**Target Language:** {result['target_lang']}")
                if result.get('error'):
                    st.error(result['error'])


def populate_all_targets(
    xliff_content: str,
    translation_data: List[dict],
    target_lang: str,
    xliff_filename: str,
    output_suffix: str,
    output_folder: str
):
    """Populate targets for multiple translation files and save XLIFF files"""
    populator = TargetPopulator()
    
    # Determine output directory
    if output_folder:
        output_dir = Path(output_folder)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = Path(".")
    
    results = []
    xliff_base = Path(xliff_filename).stem
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, trans_data in enumerate(translation_data):
        trans_file = trans_data['file']
        translations = trans_data['translations']
        
        status_text.text(f"Processing {trans_file.name}...")
        
        try:
            # Populate targets with target language
            modified_xliff, targets_added = populator.populate_targets(
                xliff_content, 
                translations,
                target_lang
            )
            
            # Generate output filename
            trans_base = Path(trans_file.name).stem
            output_filename = f"{trans_base}{output_suffix}.xlf"
            output_path = output_dir / output_filename
            
            # Write file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(modified_xliff)
            
            results.append({
                'filename': trans_file.name,
                'status': 'Success',
                'output_path': str(output_path),
                'targets_added': targets_added,
                'target_lang': target_lang
            })
            
        except Exception as e:
            results.append({
                'filename': trans_file.name,
                'status': 'Error',
                'error': str(e)
            })
        
        progress_bar.progress((idx + 1) / len(translation_data))
    
    status_text.text("✅ Processing complete!")
    st.session_state.populate_results = results
    st.rerun()


if __name__ == "__main__":
    main()
