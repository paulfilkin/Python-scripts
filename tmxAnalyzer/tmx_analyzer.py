#!/usr/bin/env python3
"""
TMX Auto-Translatable Content Analyzer - Enhanced Version

This script analyzes any bilingual TMX file and identifies Translation Units (TUs) that contain
content typically considered auto-translatable by CAT tools like Trados Studio.

Features:
- Interactive file selection
- Automatic report naming based on TMX filename
- Works with any bilingual TMX file
- Robust language detection
- Comprehensive content analysis

Categories identified:
- Numbers only
- Mixed alphanumeric/code content
- Dates
- Email addresses
- URLs
- Proper names (identical in source and target)
- Simple punctuation/symbols
- Version numbers
- Currency amounts
- Measurements
"""

import xml.etree.ElementTree as ET
import re
import os
from datetime import datetime
from typing import List, Dict, Tuple
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


class TMXAnalyzer:
    def __init__(self):
        # Regex patterns for different auto-translatable content types
        self.patterns = {
            'numbers_only': re.compile(r'^\s*[\d\s\.,\-\+\(\)%]+\s*$'),
            'mixed_alphanumeric_codes': re.compile(r'^\s*[A-Z0-9\s\-_]{2,}\s*$'),
            'dates': re.compile(r'^\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}|\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+\w+\s+\d{4})\s*$'),
            'email': re.compile(r'^\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\s*$'),
            'url': re.compile(r'^\s*(https?:\/\/|www\.)[^\s]+\s*$'),
            'simple_punctuation': re.compile(r'^\s*[^\w\s]*\s*$'),
            'version_numbers': re.compile(r'^\s*v?\d+(\.\d+)*(\-[a-zA-Z0-9]+)?\s*$'),
            'currency': re.compile(r'^\s*[$£€¥]\s*[\d\s\.,]+|[\d\s\.,]+\s*[$£€¥]\s*$'),
            'measurements': re.compile(r'^\s*\d+(\.\d+)?\s*(mm|cm|m|km|in|ft|kg|g|lb|oz|°C|°F|%)\s*$'),
        }
    
    def get_tmx_file_path(self) -> str:
        """
        Interactive file selection for TMX file
        """
        # Create a simple tkinter root window (hidden)
        root = tk.Tk()
        root.withdraw()
        
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select TMX File to Analyze",
            filetypes=[
                ("TMX files", "*.tmx"),
                ("All files", "*.*")
            ],
            initialdir=os.getcwd()
        )
        
        root.destroy()
        
        if not file_path:
            print("No file selected. Exiting.")
            exit()
        
        return file_path
    
    def detect_language_pair(self, root) -> Tuple[str, str]:
        """
        Detect source and target languages from TMX header and TUVs
        """
        # Try to get from header first
        header = root.find('.//header')
        if header is not None:
            src_lang = header.get('srclang', '').lower()
            if src_lang:
                print(f"Source language from header: {src_lang}")
        
        # Get languages from actual TUVs to be more robust
        tuvs = root.findall('.//tuv')
        languages = set()
        
        for tuv in tuvs[:10]:  # Check first 10 TUVs
            lang = tuv.get('{http://www.w3.org/XML/1998/namespace}lang')
            if not lang:
                lang = tuv.get('xml:lang')  # Alternative attribute name
            if not lang:
                lang = tuv.get('lang')  # Sometimes without namespace
            
            if lang:
                languages.add(lang.lower())
        
        languages = sorted(list(languages))
        
        if len(languages) >= 2:
            source_lang = languages[0]
            target_lang = languages[1]
            print(f"Detected language pair: {source_lang} → {target_lang}")
            return source_lang, target_lang
        elif len(languages) == 1:
            print(f"Warning: Only one language detected: {languages[0]}")
            return languages[0], "unknown"
        else:
            print("Warning: Could not detect languages from TMX")
            return "unknown", "unknown"
    
    def is_proper_name_match(self, source_text: str, target_text: str) -> bool:
        """
        Check if source and target are identical proper names
        (names that should remain unchanged in translation)
        """
        # Clean whitespace and compare
        source_clean = ' '.join(source_text.split())
        target_clean = ' '.join(target_text.split())
        
        if source_clean.lower() == target_clean.lower():
            # Check if it looks like a proper name (starts with capital letters)
            if re.match(r'^[A-Z][a-z]*(\s+[A-Z][a-z]*)*$', source_clean):
                return True
        return False
    
    def classify_content(self, text: str) -> List[str]:
        """
        Classify text content into auto-translatable categories
        """
        categories = []
        
        # Clean text for analysis
        clean_text = text.strip()
        
        if not clean_text:
            return ['empty']
        
        # Check each pattern
        for category, pattern in self.patterns.items():
            if pattern.match(clean_text):
                categories.append(category)
        
        return categories if categories else ['regular_text']
    
    def parse_tmx(self, tmx_file_path: str) -> Tuple[List[Dict], List[Dict], List[Dict], Tuple[str, str], int]:
        """
        Parse TMX file and extract translation units with analysis
        Returns: (auto_translatable_results, duplicate_results, missing_target_results, (source_lang, target_lang), total_valid_tus)
        """
        try:
            print(f"Parsing TMX file: {tmx_file_path}")
            tree = ET.parse(tmx_file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            raise Exception(f"Error parsing TMX file: {e}")
        except FileNotFoundError:
            raise Exception(f"TMX file not found: {tmx_file_path}")
        
        # Detect language pair
        source_lang, target_lang = self.detect_language_pair(root)
        
        auto_translatable_results = []
        all_tus = []
        missing_target_results = []
        tu_count = 0
        
        print("Analyzing translation units...")
        
        # Find all translation units
        for tu in root.findall('.//tu'):
            tu_count += 1
            
            if tu_count % 10000 == 0:
                print(f"Processed {tu_count} TUs...")
            
            # Extract source and target segments
            tuvs = tu.findall('tuv')
            if len(tuvs) < 2:
                # Missing target TUV entirely
                missing_target_results.append({
                    'tu_number': tu_count,
                    'issue_type': 'missing_target_tuv',
                    'source_text': '',
                    'target_text': '',
                    'creation_date': tu.get('creationdate', ''),
                    'change_date': tu.get('changedate', '')
                })
                continue
            
            # Get source and target TUVs (flexible order based on language detection)
            source_tuv = None
            target_tuv = None
            
            for tuv in tuvs:
                tuv_lang = (tuv.get('{http://www.w3.org/XML/1998/namespace}lang') or 
                           tuv.get('xml:lang') or 
                           tuv.get('lang') or '').lower()
                
                if tuv_lang == source_lang or (source_tuv is None and target_tuv is None):
                    source_tuv = tuv
                elif tuv_lang == target_lang or target_tuv is None:
                    target_tuv = tuv
            
            # Fallback: use first two TUVs if language detection failed
            if source_tuv is None:
                source_tuv = tuvs[0]
            if target_tuv is None:
                target_tuv = tuvs[1] if len(tuvs) > 1 else tuvs[0]
            
            source_seg = source_tuv.find('seg')
            target_seg = target_tuv.find('seg')
            
            # Check for missing segments
            if source_seg is None:
                missing_target_results.append({
                    'tu_number': tu_count,
                    'issue_type': 'missing_source_seg',
                    'source_text': '',
                    'target_text': ''.join(target_seg.itertext()).strip() if target_seg is not None else '',
                    'creation_date': tu.get('creationdate', ''),
                    'change_date': tu.get('changedate', '')
                })
                continue
                
            if target_seg is None:
                source_text = ''.join(source_seg.itertext()).strip()
                missing_target_results.append({
                    'tu_number': tu_count,
                    'issue_type': 'missing_target_seg',
                    'source_text': source_text,
                    'target_text': '',
                    'creation_date': tu.get('creationdate', ''),
                    'change_date': tu.get('changedate', '')
                })
                continue
            
            source_text = ''.join(source_seg.itertext()).strip()
            target_text = ''.join(target_seg.itertext()).strip()
            
            # Check for empty content
            if not source_text and not target_text:
                missing_target_results.append({
                    'tu_number': tu_count,
                    'issue_type': 'both_empty',
                    'source_text': source_text,
                    'target_text': target_text,
                    'creation_date': tu.get('creationdate', ''),
                    'change_date': tu.get('changedate', '')
                })
                continue
            elif not source_text:
                missing_target_results.append({
                    'tu_number': tu_count,
                    'issue_type': 'empty_source',
                    'source_text': source_text,
                    'target_text': target_text,
                    'creation_date': tu.get('creationdate', ''),
                    'change_date': tu.get('changedate', '')
                })
                continue
            elif not target_text:
                missing_target_results.append({
                    'tu_number': tu_count,
                    'issue_type': 'empty_target',
                    'source_text': source_text,
                    'target_text': target_text,
                    'creation_date': tu.get('creationdate', ''),
                    'change_date': tu.get('changedate', '')
                })
                continue
            
            # Get languages from TUVs
            tuv_source_lang = (source_tuv.get('{http://www.w3.org/XML/1998/namespace}lang') or 
                              source_tuv.get('xml:lang') or 
                              source_tuv.get('lang') or source_lang)
            tuv_target_lang = (target_tuv.get('{http://www.w3.org/XML/1998/namespace}lang') or 
                              target_tuv.get('xml:lang') or 
                              target_tuv.get('lang') or target_lang)
            
            # Classify source content
            source_categories = self.classify_content(source_text)
            
            # Check for proper name matches
            is_proper_name = self.is_proper_name_match(source_text, target_text)
            
            # Determine if this TU is auto-translatable
            auto_translatable_reasons = []
            
            # Check categories
            auto_translatable_categories = [
                'numbers_only', 'mixed_alphanumeric_codes', 'dates', 'email', 'url', 
                'simple_punctuation', 'version_numbers', 'currency', 'measurements'
            ]
            
            for category in source_categories:
                if category in auto_translatable_categories:
                    auto_translatable_reasons.append(category)
            
            if is_proper_name:
                auto_translatable_reasons.append('proper_name_match')
            
            # Store TU data
            tu_data = {
                'tu_number': tu_count,
                'source_lang': tuv_source_lang,
                'target_lang': tuv_target_lang,
                'source_text': source_text,
                'target_text': target_text,
                'auto_translatable_reasons': auto_translatable_reasons,
                'creation_date': tu.get('creationdate', ''),
                'change_date': tu.get('changedate', ''),
                'is_auto_translatable': bool(auto_translatable_reasons)
            }
            
            all_tus.append(tu_data)
            
            # Add to auto-translatable results if applicable
            if auto_translatable_reasons:
                auto_translatable_results.append(tu_data)
        
        print(f"Analysis complete. Processed {tu_count} TUs total.")
        print("Finding duplicate content...")
        
        # Find exact duplicates (same source AND target) among non-auto-translatable TUs
        duplicate_results = self.find_exact_duplicates(all_tus)
        
        print(f"Found {len(auto_translatable_results)} auto-translatable TUs")
        print(f"Found {len(duplicate_results)} exact duplicate TU pairs")
        print(f"Found {len(missing_target_results)} missing/empty target issues")
        
        return auto_translatable_results, duplicate_results, missing_target_results, (source_lang, target_lang), len(all_tus)
    
    def find_exact_duplicates(self, all_tus: List[Dict]) -> List[Dict]:
        """
        Find exact duplicate TUs (same source AND target) that are not auto-translatable
        """
        # Group TUs by normalized source+target combination
        pair_groups = {}
        
        for tu in all_tus:
            if tu['is_auto_translatable']:
                continue  # Skip auto-translatable TUs
            
            # Normalize both source and target text for comparison
            normalized_source = ' '.join(tu['source_text'].lower().split())
            normalized_target = ' '.join(tu['target_text'].lower().split())
            pair_key = f"{normalized_source}|||{normalized_target}"
            
            if pair_key not in pair_groups:
                pair_groups[pair_key] = []
            pair_groups[pair_key].append(tu)
        
        # Find groups with exact duplicates (MORE THAN 1 occurrence)
        duplicate_groups = []
        for pair_key, tus in pair_groups.items():
            if len(tus) > 1:  # Only groups with actual duplicates
                # Create duplicate group info
                duplicate_info = {
                    'source_text': tus[0]['source_text'],  # Use original casing
                    'target_text': tus[0]['target_text'],  # Use original casing
                    'occurrences': len(tus),
                    'tu_numbers': [tu['tu_number'] for tu in tus],
                    'creation_dates': [tu['creation_date'] for tu in tus],
                    'change_dates': [tu['change_date'] for tu in tus]
                }
                
                duplicate_groups.append(duplicate_info)
        
        # Sort by number of occurrences (descending)
        duplicate_groups.sort(key=lambda x: x['occurrences'], reverse=True)
        
        return duplicate_groups
    
    def generate_report(self, auto_translatable_results: List[Dict], duplicate_results: List[Dict], 
                       missing_target_results: List[Dict], language_pair: Tuple[str, str], 
                       total_valid_tus: int, tmx_file_path: str) -> str:
        """
        Generate a detailed report of auto-translatable content, duplicates, and missing targets
        """
        source_lang, target_lang = language_pair
        tmx_filename = Path(tmx_file_path).stem
        
        total_auto_translatable = len(auto_translatable_results)
        total_exact_duplicates = len(duplicate_results)
        total_duplicate_instances = sum(dup['occurrences'] for dup in duplicate_results)
        total_missing_targets = len(missing_target_results)
        
        # Count by category for auto-translatable
        category_counts = {}
        for result in auto_translatable_results:
            for reason in result['auto_translatable_reasons']:
                category_counts[reason] = category_counts.get(reason, 0) + 1
        
        # Count missing target issues by type
        missing_counts = {}
        for result in missing_target_results:
            issue_type = result['issue_type']
            missing_counts[issue_type] = missing_counts.get(issue_type, 0) + 1
        
        # Generate report
        report_lines = [
            "=" * 80,
            "TMX CONTENT ANALYSIS REPORT",
            "=" * 80,
            f"TMX File: {Path(tmx_file_path).name}",
            f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Language Pair: {source_lang} → {target_lang}",
            "",
            "SUMMARY:",
            "-" * 20,
            f"Auto-Translatable TUs Found: {total_auto_translatable:,}",
            f"Exact Duplicate TU Pairs: {total_exact_duplicates:,}",
            f"Total Duplicate Instances: {total_duplicate_instances:,}",
            f"Missing/Empty Target Issues: {total_missing_targets:,}",
            "",
            "AUTO-TRANSLATABLE CONTENT BY CATEGORY:",
            "-" * 45
        ]
        
        # Sort categories by count
        if category_counts:
            sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
            for category, count in sorted_categories:
                category_display = category.replace('_', ' ').title()
                report_lines.append(f"{category_display:<25}: {count:>6,} TUs")
        else:
            report_lines.append("No auto-translatable content found.")
        
        # Missing/Empty targets summary
        report_lines.extend([
            "",
            "MISSING/EMPTY TARGETS BY TYPE:",
            "-" * 35
        ])
        
        if missing_counts:
            issue_type_names = {
                'missing_target_tuv': 'Missing Target TUV',
                'missing_target_seg': 'Missing Target Segment', 
                'missing_source_seg': 'Missing Source Segment',
                'empty_target': 'Empty Target Text',
                'empty_source': 'Empty Source Text',
                'both_empty': 'Both Source & Target Empty'
            }
            
            for issue_type, count in sorted(missing_counts.items(), key=lambda x: x[1], reverse=True):
                display_name = issue_type_names.get(issue_type, issue_type.replace('_', ' ').title())
                report_lines.append(f"{display_name:<30}: {count:>6,} TUs")
        else:
            report_lines.append("No missing/empty target issues found.")
        
        # Exact duplicate content summary
        report_lines.extend([
            "",
            "EXACT DUPLICATE CONTENT SUMMARY:",
            "-" * 37
        ])
        
        if duplicate_results:
            # Show top duplicates summary
            report_lines.append(f"{'Source Text':<35} {'Target Text':<35} {'Count':<6} {'TU Numbers'}")
            report_lines.append("-" * 95)
            
            for dup in duplicate_results[:15]:  # Show top 15
                source_preview = dup['source_text'][:30] + "..." if len(dup['source_text']) > 30 else dup['source_text']
                target_preview = dup['target_text'][:30] + "..." if len(dup['target_text']) > 30 else dup['target_text']
                tu_numbers_str = ", ".join(map(str, dup['tu_numbers'][:5]))
                if len(dup['tu_numbers']) > 5:
                    tu_numbers_str += "..."
                
                report_lines.append(f"{source_preview:<35} {target_preview:<35} {dup['occurrences']:<6} {tu_numbers_str}")
            
            if len(duplicate_results) > 15:
                report_lines.append(f"\n... and {len(duplicate_results) - 15:,} more exact duplicate pairs")
        else:
            report_lines.append("No exact duplicate content found.")
        
        # Detailed missing/empty targets findings
        if missing_target_results:
            report_lines.extend([
                "",
                "",
                "DETAILED MISSING/EMPTY TARGET FINDINGS:",
                "-" * 65
            ])
            
            issue_type_names = {
                'missing_target_tuv': 'Missing Target TUV',
                'missing_target_seg': 'Missing Target Segment', 
                'missing_source_seg': 'Missing Source Segment',
                'empty_target': 'Empty Target Text',
                'empty_source': 'Empty Source Text',
                'both_empty': 'Both Source & Target Empty'
            }
            
            # Group by issue type
            for issue_type, count in sorted(missing_counts.items(), key=lambda x: x[1], reverse=True):
                display_name = issue_type_names.get(issue_type, issue_type.replace('_', ' ').title())
                report_lines.append(f"\n{display_name} ({count:,} TUs):")
                report_lines.append("=" * (len(display_name) + 15))
                
                issue_results = [r for r in missing_target_results if r['issue_type'] == issue_type]
                
                for i, result in enumerate(issue_results[:15], 1):  # Show first 15 examples
                    report_lines.append(f"{i:2d}. TU #{result['tu_number']}")
                    if result['source_text']:
                        report_lines.append(f"    Source: \"{result['source_text']}\"")
                    else:
                        report_lines.append(f"    Source: [EMPTY]")
                    
                    if result['target_text']:
                        report_lines.append(f"    Target: \"{result['target_text']}\"")
                    else:
                        report_lines.append(f"    Target: [EMPTY/MISSING]")
                    report_lines.append("")
                
                if len(issue_results) > 15:
                    report_lines.append(f"    ... and {len(issue_results) - 15:,} more TUs with this issue\n")
        
        # Detailed auto-translatable findings
        if auto_translatable_results:
            report_lines.extend([
                "",
                "",
                "DETAILED AUTO-TRANSLATABLE FINDINGS:",
                "-" * 60
            ])
            
            # Group results by category for detailed listing
            if category_counts:
                for category, count in sorted_categories:
                    category_display = category.replace('_', ' ').title()
                    report_lines.append(f"\n{category_display} ({count:,} TUs):")
                    report_lines.append("=" * (len(category_display) + 15))
                    
                    category_results = [r for r in auto_translatable_results if category in r['auto_translatable_reasons']]
                    
                    for i, result in enumerate(category_results[:10], 1):  # Show first 10 examples
                        report_lines.append(f"{i:2d}. TU #{result['tu_number']}")
                        report_lines.append(f"    Source: {result['source_text']}")
                        report_lines.append(f"    Target: {result['target_text']}")
                        if len(result['auto_translatable_reasons']) > 1:
                            other_reasons = [r for r in result['auto_translatable_reasons'] if r != category]
                            report_lines.append(f"    Also: {', '.join(other_reasons)}")
                        report_lines.append("")
                    
                    if len(category_results) > 10:
                        report_lines.append(f"    ... and {len(category_results) - 10:,} more TUs in this category\n")
        
        # Detailed exact duplicate findings
        if duplicate_results:
            report_lines.extend([
                "",
                "",
                "DETAILED EXACT DUPLICATE FINDINGS:",
                "-" * 55
            ])
            
            for i, dup in enumerate(duplicate_results[:25], 1):  # Show top 25 duplicates
                report_lines.append(f"\n{i}. EXACT DUPLICATE (appears {dup['occurrences']} times):")
                report_lines.append(f"   Source: \"{dup['source_text']}\"")
                report_lines.append(f"   Target: \"{dup['target_text']}\"")
                report_lines.append(f"   TU Numbers: {', '.join(map(str, dup['tu_numbers']))}")
                
                # Show creation dates if they vary
                unique_creation_dates = list(set(filter(None, dup['creation_dates'])))
                if len(unique_creation_dates) > 1:
                    report_lines.append(f"   Creation Dates: {', '.join(unique_creation_dates[:3])}")
            
            if len(duplicate_results) > 25:
                report_lines.append(f"\n... and {len(duplicate_results) - 25:,} more exact duplicate pairs")
        
        # Add insights and space savings analysis
        if duplicate_results:
            total_redundant = sum(dup['occurrences'] - 1 for dup in duplicate_results)
            total_tus_processed = total_valid_tus + len(missing_target_results)  # Include all TUs analyzed
            space_savings_percent = (total_redundant / total_tus_processed) * 100 if total_tus_processed > 0 else 0
            
            report_lines.extend([
                "",
                "DUPLICATE ANALYSIS INSIGHTS:",
                "-" * 30,
                f"Total TUs analyzed: {total_tus_processed:,}",
                f"Total redundant TU entries: {total_redundant:,}",
                f"Space savings potential: {space_savings_percent:.1f}% ({total_redundant:,} TUs could be removed)",
                "These exact duplicates can be safely removed to optimize TMX size.",
                "Recommendation: Import into Trados Studio for automatic deduplication."
            ])
        
        return "\n".join(report_lines)
    
    def save_report(self, report_text: str, tmx_file_path: str) -> str:
        """
        Save report to file in same directory as TMX with descriptive name
        """
        tmx_path = Path(tmx_file_path)
        tmx_directory = tmx_path.parent
        tmx_filename = tmx_path.stem
        
        # Create report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{tmx_filename}_analysis_report_{timestamp}.txt"
        report_path = tmx_directory / report_filename
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            return str(report_path)
        except Exception as e:
            # Fallback to current directory if TMX directory is not writable
            fallback_path = Path.cwd() / report_filename
            with open(fallback_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            return str(fallback_path)


def main():
    print("=" * 60)
    print("TMX Auto-Translatable Content Analyzer")
    print("=" * 60)
    print("This tool analyzes TMX files for auto-translatable content,")
    print("exact duplicates, and missing target translations.")
    print()
    
    try:
        analyzer = TMXAnalyzer()
        
        # Get TMX file path interactively
        tmx_file_path = analyzer.get_tmx_file_path()
        
        print(f"\nSelected file: {tmx_file_path}")
        print("Starting analysis...")
        
        # Parse TMX and analyze content
        results = analyzer.parse_tmx(tmx_file_path)
        auto_translatable_results, duplicate_results, missing_target_results, language_pair, total_valid_tus = results
        
        # Generate report
        print("Generating report...")
        report = analyzer.generate_report(
            auto_translatable_results, 
            duplicate_results, 
            missing_target_results, 
            language_pair,
            total_valid_tus,
            tmx_file_path
        )
        
        # Save report
        report_path = analyzer.save_report(report, tmx_file_path)
        
        print(f"\n✅ Analysis complete!")
        print(f"📄 Report saved to: {report_path}")
        print(f"\n📊 Summary:")
        print(f"   • Auto-translatable TUs: {len(auto_translatable_results):,}")
        print(f"   • Exact duplicate pairs: {len(duplicate_results):,}")
        print(f"   • Missing/empty targets: {len(missing_target_results):,}")
        
        # Show report in console
        response = input("\nWould you like to display the report in the console? (y/n): ").lower().strip()
        if response == 'y' or response == 'yes':
            print("\n" + "=" * 80)
            print(report)
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        print("Please ensure the TMX file is valid and not corrupted.")


if __name__ == "__main__":
    main()