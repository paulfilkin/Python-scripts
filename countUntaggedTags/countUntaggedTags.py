import xml.etree.ElementTree as ET
import re
import sys
import html
from collections import Counter

def extract_tags_and_placeholders(text):
    """Extract HTML tags and placeholders from text, return detailed breakdown"""
    if not text:
        return [], [], []
    
    # Decode HTML entities like &lt; &gt; etc.
    decoded_text = html.unescape(text)
    
    # Find HTML/XML tags
    html_tag_pattern = r'<[^>]+>'
    html_tags = re.findall(html_tag_pattern, decoded_text)
    
    # Find single-brace placeholders {something}
    single_brace_pattern = r'\{[^}]+\}'
    single_placeholders = re.findall(single_brace_pattern, decoded_text)
    
    # Find double-brace placeholders {{something}}
    double_brace_pattern = r'\{\{[^}]+\}\}'
    double_placeholders = re.findall(double_brace_pattern, decoded_text)
    
    return html_tags, single_placeholders, double_placeholders

def compare_elements(source_elements, target_elements, element_type):
    """Compare source and target elements, return missing and extra items"""
    source_counter = Counter(source_elements)
    target_counter = Counter(target_elements)
    
    missing = []
    extra = []
    
    # Find missing elements (in source but not in target, or fewer in target)
    for element, source_count in source_counter.items():
        target_count = target_counter.get(element, 0)
        if target_count < source_count:
            missing.extend([element] * (source_count - target_count))
    
    # Find extra elements (in target but not in source, or more in target)
    for element, target_count in target_counter.items():
        source_count = source_counter.get(element, 0)
        if target_count > source_count:
            extra.extend([element] * (target_count - source_count))
    
    return missing, extra

def analyze_xliff_file(file_path):
    """Analyze XLIFF file and generate detailed tag/placeholder report"""
    try:
        # Parse the XML file
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Define namespaces
        ns = {
            'xliff': 'urn:oasis:names:tc:xliff:document:1.2',
            'sdl': 'http://sdl.com/FileTypes/SdlXliff/1.0'
        }
        
        # Find all trans-unit elements
        trans_units = root.findall('.//xliff:trans-unit', ns)
        
        # Prepare data for both console and markdown output
        report_data = []
        
        print("XLIFF Tag and Placeholder Analysis Report")
        print("=" * 80)
        print(f"{'Segment ID':<12} {'HTML':<8} {'HTML':<8} {'{}':<6} {'{}':<6} {'{{}}':<8} {'{{}}':<8} {'Issues':<12}")
        print(f"{'':12} {'Src':<8} {'Tgt':<8} {'Src':<6} {'Tgt':<6} {'Src':<8} {'Tgt':<8}")
        print("-" * 80)
        
        total_source_html = 0
        total_target_html = 0
        total_source_single = 0
        total_target_single = 0
        total_source_double = 0
        total_target_double = 0
        
        segment_count = 0
        problem_segments = 0
        
        for trans_unit in trans_units:
            segment_count += 1
            
            # Get SDL segment ID if available
            seg_def = trans_unit.find('.//sdl:seg-defs/sdl:seg', ns)
            if seg_def is not None:
                seg_id = seg_def.get('id', segment_count)
            else:
                seg_id = segment_count
            
            # Get source text directly from <source> element
            source_elem = trans_unit.find('xliff:source', ns)
            source_text = ''
            if source_elem is not None:
                source_text = source_elem.text or ''
            
            # Get target text from <target><mrk> element
            target_elem = trans_unit.find('.//xliff:target//xliff:mrk', ns)
            target_text = ''
            if target_elem is not None:
                target_text = target_elem.text or ''
            
            # Extract all elements
            src_html, src_single, src_double = extract_tags_and_placeholders(source_text)
            tgt_html, tgt_single, tgt_double = extract_tags_and_placeholders(target_text)
            
            # Count elements
            src_html_count = len(src_html)
            tgt_html_count = len(tgt_html)
            src_single_count = len(src_single)
            tgt_single_count = len(tgt_single)
            src_double_count = len(src_double)
            tgt_double_count = len(tgt_double)
            
            # Check for issues
            issues = []
            if src_html_count != tgt_html_count:
                issues.append("HTML")
            if src_single_count != tgt_single_count:
                issues.append("{}")
            if src_double_count != tgt_double_count:
                issues.append("{{}}")
            
            issue_text = ",".join(issues) if issues else "✓"
            if issues:
                problem_segments += 1
            
            # Collect detailed issue information
            detailed_issues = {}
            if issues:
                if "HTML" in issues:
                    missing_html, extra_html = compare_elements(src_html, tgt_html, "HTML")
                    detailed_issues["Missing HTML tags"] = missing_html
                    detailed_issues["Extra HTML tags"] = extra_html
                
                if "{}" in issues:
                    missing_single, extra_single = compare_elements(src_single, tgt_single, "Single-brace")
                    detailed_issues["Missing {} placeholders"] = missing_single
                    detailed_issues["Extra {} placeholders"] = extra_single
                
                if "{{}}" in issues:
                    missing_double, extra_double = compare_elements(src_double, tgt_double, "Double-brace")
                    detailed_issues["Missing {{}} placeholders"] = missing_double
                    detailed_issues["Extra {{}} placeholders"] = extra_double
            
            # Store data for markdown report
            segment_data = {
                'seg_id': seg_id,
                'source_text': source_text,
                'target_text': target_text,
                'src_html_count': src_html_count,
                'tgt_html_count': tgt_html_count,
                'src_single_count': src_single_count,
                'tgt_single_count': tgt_single_count,
                'src_double_count': src_double_count,
                'tgt_double_count': tgt_double_count,
                'issues': issues,
                'issue_text': issue_text,
                'detailed_issues': detailed_issues
            }
            report_data.append(segment_data)
            
            # Display segment info using SDL segment ID
            print(f"Segment {seg_id:<8} {src_html_count:<8} {tgt_html_count:<8} {src_single_count:<6} {tgt_single_count:<6} {src_double_count:<8} {tgt_double_count:<8} {issue_text:<12}")
            
            # Show detailed issues if any
            if issues:
                print(f"{'':12} Source: {source_text[:60]}{'...' if len(source_text) > 60 else ''}")
                print(f"{'':12} Target: {target_text[:60]}{'...' if len(target_text) > 60 else ''}")
                
                for issue_type, items in detailed_issues.items():
                    if items:
                        print(f"{'':12} {issue_type}: {', '.join(items)}")
                
                print()  # Empty line for readability
            
            # Add to totals
            total_source_html += src_html_count
            total_target_html += tgt_html_count
            total_source_single += src_single_count
            total_target_single += tgt_single_count
            total_source_double += src_double_count
            total_target_double += tgt_double_count
        
        # Print summary
        print("-" * 80)
        print(f"{'TOTALS':<12} {total_source_html:<8} {total_target_html:<8} {total_source_single:<6} {total_target_single:<6} {total_source_double:<8} {total_target_double:<8}")
        print("=" * 80)
        print(f"Total segments analyzed: {segment_count}")
        print(f"Segments with issues: {problem_segments}")
        print(f"Accuracy rate: {((segment_count - problem_segments) / segment_count * 100):.1f}%")
        
        if problem_segments > 0:
            print(f"\n⚠️  Warning: {problem_segments} segment(s) have missing or malformed tags/placeholders!")
        else:
            print(f"\n✅ All segments have perfect tag/placeholder consistency!")
        
        # Generate markdown report
        generate_markdown_report(file_path, report_data, {
            'total_segments': segment_count,
            'problem_segments': problem_segments,
            'accuracy_rate': ((segment_count - problem_segments) / segment_count * 100),
            'total_source_html': total_source_html,
            'total_target_html': total_target_html,
            'total_source_single': total_source_single,
            'total_target_single': total_target_single,
            'total_source_double': total_source_double,
            'total_target_double': total_target_double
        })
            
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def generate_markdown_report(file_path, report_data, summary):
    """Generate a markdown report file"""
    import os
    from datetime import datetime
    
    # Create output filename
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = f"{base_name}_tag_analysis_report.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# XLIFF Tag and Placeholder Analysis Report\n\n")
        f.write(f"**File:** `{os.path.basename(file_path)}`  \n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n\n")
        
        # Summary section
        f.write("## Summary\n\n")
        f.write(f"- **Total segments:** {summary['total_segments']}\n")
        f.write(f"- **Segments with issues:** {summary['problem_segments']}\n")
        f.write(f"- **Accuracy rate:** {summary['accuracy_rate']:.1f}%\n\n")
        
        if summary['problem_segments'] > 0:
            f.write("⚠️ **Warning:** Issues found in translation!\n\n")
        else:
            f.write("✅ **All segments have perfect tag/placeholder consistency!**\n\n")
        
        # Detailed results table
        f.write("## Detailed Results\n\n")
        f.write("| Segment | HTML Tags | Single Braces `{}` | Double Braces `{{}}` | Issues |\n")
        f.write("|---------|-----------|-------------------|---------------------|--------|\n")
        f.write("| ID | Src → Tgt | Src → Tgt | Src → Tgt | Status |\n")
        
        for data in report_data:
            f.write(f"| {data['seg_id']} | {data['src_html_count']} → {data['tgt_html_count']} | "
                   f"{data['src_single_count']} → {data['tgt_single_count']} | "
                   f"{data['src_double_count']} → {data['tgt_double_count']} | "
                   f"{data['issue_text']} |\n")
        
        # Totals
        f.write(f"| **TOTAL** | **{summary['total_source_html']} → {summary['total_target_html']}** | "
               f"**{summary['total_source_single']} → {summary['total_target_single']}** | "
               f"**{summary['total_source_double']} → {summary['total_target_double']}** | |\n\n")
        
        # Problem segments details
        problem_segments = [data for data in report_data if data['issues']]
        if problem_segments:
            f.write("## Problem Segments\n\n")
            for data in problem_segments:
                f.write(f"### Segment {data['seg_id']}\n\n")
                f.write(f"**Source:** `{data['source_text']}`  \n")
                f.write(f"**Target:** `{data['target_text']}`  \n\n")
                
                f.write("**Issues found:**\n")
                for issue_type, items in data['detailed_issues'].items():
                    if items:
                        f.write(f"- **{issue_type}:** {', '.join(f'`{item}`' for item in items)}\n")
                f.write("\n")
    
    print(f"\n📄 Markdown report saved as: {output_file}")
    return output_file

if __name__ == "__main__":
    # Check if file path is provided as command line argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # If no argument provided, prompt for file path
        file_path = input("Enter the path to your XLIFF file: ").strip().strip('"')
    
    analyze_xliff_file(file_path)