import xml.etree.ElementTree as ET
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
from pathlib import Path
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def parse_xliff_quality_data(xliff_path):
    """Parse XLIFF file and extract quality evaluation data."""
    xliff_path = Path(xliff_path)
    tree = ET.parse(xliff_path)
    root = tree.getroot()
    
    namespaces = {
        'xliff': 'urn:oasis:names:tc:xliff:document:1.2',
        'sdl': 'http://sdl.com/FileTypes/SdlXliff/1.0'
    }
    
    # Extract metadata
    file_elem = root.find('.//xliff:file', namespaces)
    if file_elem is not None:
        source_lang = file_elem.get('source-language', 'Unknown')
        target_lang = file_elem.get('target-language', 'Unknown')
        original = file_elem.get('original', xliff_path.name)
    else:
        source_lang = target_lang = original = 'Unknown'
    
    metadata = {
        'source_language': source_lang,
        'target_language': target_lang,
        'original': Path(original).name if original != 'Unknown' else xliff_path.name,
        'file_display': xliff_path.name
    }
    
    quality_data = []
    trans_units = root.findall('.//xliff:trans-unit', namespaces)
    translatable_units = [tu for tu in trans_units if tu.get('translate') != 'no']
    
    def inner_text(elem):
        """Extract full text including inline tags."""
        return ''.join(elem.itertext()) if elem is not None else ''
    
    for trans_unit in translatable_units:
        seg_source = trans_unit.find('xliff:seg-source', namespaces)
        target = trans_unit.find('xliff:target', namespaces)
        
        if seg_source is None or target is None:
            continue
        
        source_mrk = seg_source.find('.//xliff:mrk', namespaces)
        target_mrk = target.find('.//xliff:mrk', namespaces)
        
        if source_mrk is None or target_mrk is None:
            continue
        
        source_text = inner_text(source_mrk)
        target_text = inner_text(target_mrk)
        seg_id = source_mrk.get('mid', '') or trans_unit.get('id', '')
        
        seg_defs = trans_unit.find('.//sdl:seg-defs', namespaces)
        if seg_defs is None:
            continue
        
        seg = seg_defs.find('.//sdl:seg', namespaces)
        if seg is None:
            continue
        
        score = None
        description = None
        model = None
        
        values = seg.findall('.//sdl:value', namespaces)
        for value in values:
            key = value.get('key', '')
            if key == 'tqe-score-1':
                try:
                    score = int((value.text or '').strip())
                except (TypeError, ValueError):
                    continue
            elif key == 'tqe-description-1':
                description = (value.text or '').strip()
            elif key == 'tqe-model-1':
                model = (value.text or '').strip()
        
        if score is not None:
            quality_data.append({
                'segment_id': seg_id,
                'source': source_text,
                'target': target_text,
                'score': score,
                'description': description,
                'model': model
            })
    
    return quality_data, metadata

def calculate_statistics(quality_data):
    """Calculate statistics based only on actual scores in the data."""
    if not quality_data:
        return None
    
    scores = [d['score'] for d in quality_data]
    
    # Count actual score values - don't invent categories
    score_distribution = {}
    for score in scores:
        score_distribution[score] = score_distribution.get(score, 0) + 1
    
    return {
        'total_segments': len(scores),
        'average_score': sum(scores) / len(scores),
        'median_score': statistics.median(scores),
        'stdev_score': statistics.pstdev(scores) if len(scores) > 1 else 0.0,
        'score_distribution': score_distribution
    }

def categorise_issue(description):
    """Categorize error type from description."""
    if not description:
        return 'Unspecified'
    
    text = description.lower()
    
    if any(k in text for k in ['omit', 'missing', 'left out']):
        return 'Omission'
    if any(k in text for k in ['accur', 'mistrans', 'meaning', 'inaccur']):
        return 'Accuracy'
    if any(k in text for k in ['style', 'tone', 'register']):
        return 'Style'
    if any(k in text for k in ['grammar', 'case', 'capital', 'agreement', 'plural', 'syntax']):
        return 'Grammar'
    if any(k in text for k in ['terminology', 'term']):
        return 'Terminology'
    
    return 'Other'

def make_score_distribution_chart(dist_dict, out_png, is_binary=False):
    """Create a chart showing score distribution using matplotlib."""
    labels = sorted(dist_dict.keys(), reverse=True)
    values = [dist_dict[k] for k in labels]
    
    if is_binary:
        # Pie chart for binary scores
        plt.figure(figsize=(4.5, 3.0), dpi=150)
        colors_list = ['#4caf50' if l >= 90 else '#f44336' for l in labels]
        plt.pie(values, labels=[f'Score {l}' for l in labels], autopct='%1.1f%%', colors=colors_list, startangle=90)
        plt.title('Score Distribution')
        plt.tight_layout()
    else:
        # Bar chart for multiple scores
        plt.figure(figsize=(4.5, 3.0), dpi=150)
        plt.bar(range(len(labels)), values, color=['#4caf50' if l >= 90 else '#f44336' for l in labels])
        plt.xticks(range(len(labels)), [str(l) for l in labels], rotation=0)
        plt.xlabel('Score')
        plt.ylabel('Count')
        plt.title('Score Distribution')
        plt.tight_layout()
    
    plt.savefig(out_png)
    plt.close()

def create_consolidated_report(files_data, output_file):
    """Create a single PDF with all files, summary at the end."""
    doc = SimpleDocTemplate(
        output_file, pagesize=A4,
        rightMargin=36, leftMargin=36, topMargin=48, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#1a237e'),
        alignment=TA_CENTER,
        spaceAfter=18
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#283593'),
        spaceBefore=12,
        spaceAfter=8
    )
    
    file_heading_style = ParagraphStyle(
        'FileHeading',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a237e'),
        spaceBefore=12,
        spaceAfter=12
    )
    
    small_style = ParagraphStyle(
        'small',
        parent=styles['Normal'],
        fontSize=9,
        leading=12
    )
    
    elements = []
    
    # COVER PAGE
    elements.append(Spacer(1, 5*cm))
    elements.append(Paragraph("Translation Quality Evaluation Report", title_style))
    
    report_date = datetime.now().strftime("%d %B %Y")
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(f"<b>Report Date:</b> {report_date}", styles['Normal']))
    elements.append(Paragraph(f"<b>Files Analyzed:</b> {len(files_data)}", styles['Normal']))
    elements.append(PageBreak())
    
    # BATCH SUMMARY AT THE START
    elements.append(Paragraph("Batch Summary", title_style))
    elements.append(Spacer(1, 12))
    
    # Calculate overall totals
    total_segments_all = sum(fd['stats']['total_segments'] for fd in files_data)
    total_good_all = sum(fd['stats']['score_distribution'].get(100, 0) for fd in files_data)
    total_poor_all = sum(fd['stats']['score_distribution'].get(10, 0) for fd in files_data)
    
    # Calculate category totals across all files
    category_totals = {}
    for file_data in files_data:
        for seg in file_data['quality_data']:
            if seg['score'] == 10:  # Only count poor segments
                category = categorise_issue(seg.get('description'))
                category_totals[category] = category_totals.get(category, 0) + 1
    
    # Calculate weighted average score
    weighted_sum = sum(fd['stats']['average_score'] * fd['stats']['total_segments'] for fd in files_data)
    weighted_avg = weighted_sum / total_segments_all if total_segments_all > 0 else 0
    
    # Find best and worst files
    files_with_good_pct = [(fd['metadata']['file_display'], 
                           fd['stats']['score_distribution'].get(100, 0) / fd['stats']['total_segments'] * 100)
                          for fd in files_data]
    best_file = max(files_with_good_pct, key=lambda x: x[1])
    worst_file = min(files_with_good_pct, key=lambda x: x[1])
    
    # Detect if all files have binary scoring
    all_binary = all(len(fd['stats']['score_distribution']) == 2 for fd in files_data)
    
    summary_rows = [['File', 'Total Segs', 'Good (100)', 'Poor (10)', 'Avg Score']]
    
    for file_data in files_data:
        stats = file_data['stats']
        metadata = file_data['metadata']
        
        good_count = stats['score_distribution'].get(100, 0)
        poor_count = stats['score_distribution'].get(10, 0)
        good_pct = (good_count / stats['total_segments']) * 100 if stats['total_segments'] > 0 else 0
        poor_pct = (poor_count / stats['total_segments']) * 100 if stats['total_segments'] > 0 else 0
        
        summary_rows.append([
            metadata['file_display'],
            str(stats['total_segments']),
            f"{good_count} ({good_pct:.1f}%)",
            f"{poor_count} ({poor_pct:.1f}%)",
            f"{stats['average_score']:.1f}"
        ])
    
    # Add overall totals row
    overall_good_pct = (total_good_all / total_segments_all) * 100 if total_segments_all > 0 else 0
    overall_poor_pct = (total_poor_all / total_segments_all) * 100 if total_segments_all > 0 else 0
    
    summary_rows.append([
        'OVERALL TOTALS',
        str(total_segments_all),
        f"{total_good_all} ({overall_good_pct:.1f}%)",
        f"{total_poor_all} ({overall_poor_pct:.1f}%)",
        f"{weighted_avg:.1f}"
    ])
    
    summary_tbl = Table(summary_rows, colWidths=[5*cm, 2*cm, 3*cm, 3*cm, 2*cm], repeatRows=1)
    summary_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#263238')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -2), 8),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#eceff1')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        # Style the totals row
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#37474f')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 9),
    ]))
    
    elements.append(summary_tbl)
    elements.append(Spacer(1, 12))
    
    # Add insights
    elements.append(Paragraph(f"<b>Best File:</b> {best_file[0]} ({best_file[1]:.1f}% good)", styles['Normal']))
    elements.append(Paragraph(f"<b>Worst File:</b> {worst_file[0]} ({worst_file[1]:.1f}% good)", styles['Normal']))
    elements.append(Paragraph(f"<b>Weighted Average Score:</b> {weighted_avg:.1f}/100", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Add category breakdown
    if category_totals:
        elements.append(Paragraph("Issue Categories (Poor Segments Only)", heading_style))
        
        category_rows = [['Category', 'Count', 'Percentage']]
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        
        for category, count in sorted_categories:
            pct = (count / total_poor_all) * 100 if total_poor_all > 0 else 0
            category_rows.append([category, str(count), f"{pct:.1f}%"])
        
        category_tbl = Table(category_rows, colWidths=[6*cm, 3*cm, 3*cm])
        category_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c62828')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ffebee')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER')
        ]))
        
        elements.append(category_tbl)
        elements.append(Spacer(1, 12))
    
    # Overall pie chart for the entire batch
    if all_binary:
        overall_chart_path = str(Path(output_file).parent / 'overall_distribution.png')
        overall_dist = {100: total_good_all, 10: total_poor_all}
        make_score_distribution_chart(overall_dist, overall_chart_path, is_binary=True)
        elements.append(Paragraph("Overall Quality Distribution", heading_style))
        elements.append(Image(overall_chart_path, width=10*cm, height=6.5*cm))
    
    # Model info
    if files_data and files_data[0]['quality_data']:
        first_model = files_data[0]['quality_data'][0].get('model')
        if first_model:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"<i>Quality evaluation performed by: {first_model}</i>", small_style))
    
    elements.append(PageBreak())
    
    # INDIVIDUAL FILE REPORTS
    for idx, file_data in enumerate(files_data):
        quality_data = file_data['quality_data']
        metadata = file_data['metadata']
        stats = file_data['stats']
        
        # File header
        elements.append(Paragraph(f"File: {metadata['file_display']}", file_heading_style))
        elements.append(Paragraph(f"<b>Original:</b> {metadata['original']}", styles['Normal']))
        elements.append(Paragraph(f"<b>Language Pair:</b> {metadata['source_language']} → {metadata['target_language']}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Summary table for this file
        elements.append(Paragraph("Summary", heading_style))
        
        # Detect if scoring is binary (only 2 distinct values)
        is_binary = len(stats['score_distribution']) == 2
        
        # Define custom labels for scores
        score_labels = {
            100: 'Excellent Quality (100)',
            10: 'Requires Attention (10)',
        }
        
        summary_rows = [['Metric', 'Value']]
        summary_rows.append(['Total Segments', str(stats['total_segments'])])
        
        if is_binary:
            # Simplified metrics for binary scoring
            for score in sorted(stats['score_distribution'].keys(), reverse=True):
                count = stats['score_distribution'][score]
                percentage = (count / stats['total_segments']) * 100
                label = score_labels.get(score, f'Score {score}')
                summary_rows.append([label, f'{count} ({percentage:.1f}%)'])
        else:
            # Full statistics for multi-value scoring
            summary_rows.append(['Average Score', f"{stats['average_score']:.1f}/100"])
            summary_rows.append(['Median Score', f"{stats['median_score']:.1f}/100"])
            summary_rows.append(['Std Dev', f"{stats['stdev_score']:.1f}"])
            
            # Add score distribution
            for score in sorted(stats['score_distribution'].keys(), reverse=True):
                count = stats['score_distribution'][score]
                percentage = (count / stats['total_segments']) * 100
                label = score_labels.get(score, f'Score {score}')
                summary_rows.append([label, f'{count} ({percentage:.1f}%)'])
        
        summary_tbl = Table(summary_rows, colWidths=[7*cm, 7*cm])
        summary_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        elements.append(summary_tbl)
        elements.append(Spacer(1, 12))
        
        # Add category breakdown for this file
        file_category_counts = {}
        for seg in quality_data:
            if seg['score'] == 10:  # Only poor segments
                category = categorise_issue(seg.get('description'))
                file_category_counts[category] = file_category_counts.get(category, 0) + 1
        
        if file_category_counts:
            elements.append(Paragraph("Issue Categories", styles['Heading3']))
            
            cat_rows = [['Category', 'Count']]
            sorted_cats = sorted(file_category_counts.items(), key=lambda x: x[1], reverse=True)
            
            for cat, cnt in sorted_cats:
                cat_rows.append([cat, str(cnt)])
            
            cat_tbl = Table(cat_rows, colWidths=[8*cm, 3*cm])
            cat_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff9800')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff3e0')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER')
            ]))
            
            elements.append(cat_tbl)
            elements.append(Spacer(1, 12))
        
        # Score distribution chart
        chart_path = str(Path(output_file).parent / f'chart_{idx}.png')
        make_score_distribution_chart(stats['score_distribution'], chart_path, is_binary=is_binary)
        elements.append(Image(chart_path, width=10*cm, height=6.5*cm))
        elements.append(Spacer(1, 12))
        
        # Poor segments
        poor_segments = [d for d in quality_data if d['score'] == 10]
        
        if poor_segments:
            elements.append(Paragraph(f"Segments Requiring Attention ({len(poor_segments)})", heading_style))
            
            rows = [['ID', 'Score', 'Category', 'Issue', 'Source', 'Target']]
            
            for seg in poor_segments:
                category = categorise_issue(seg.get('description'))
                issue = seg.get('description') or 'No description'
                
                def limit(text, max_len=250):
                    return (text[:max_len] + '…') if len(text) > max_len else text
                
                rows.append([
                    str(seg['segment_id']),
                    f"{seg['score']}",
                    category,
                    Paragraph(limit(issue), small_style),
                    Paragraph(limit(seg['source']), small_style),
                    Paragraph(limit(seg['target']), small_style)
                ])
            
            col_widths = [1.5*cm, 1.2*cm, 2.5*cm, 4.5*cm, 5.5*cm, 5.5*cm]
            tbl = Table(rows, colWidths=col_widths, repeatRows=1)
            tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffebee')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#c62828')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fffaf9')]),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            elements.append(tbl)
            elements.append(Spacer(1, 12))
        
        # Good segments
        good_segments = [d for d in quality_data if d['score'] == 100]
        
        if good_segments:
            elements.append(Paragraph(f"High-Quality Segments ({len(good_segments)})", heading_style))
            
            sample = good_segments[:10]
            rows2 = [['ID', 'Source', 'Target']]
            
            def limit2(text, max_len=250):
                return (text[:max_len] + '…') if len(text) > max_len else text
            
            for seg in sample:
                rows2.append([
                    str(seg['segment_id']),
                    Paragraph(limit2(seg['source']), small_style),
                    Paragraph(limit2(seg['target']), small_style)
                ])
            
            tbl2 = Table(rows2, colWidths=[1.5*cm, 9*cm, 9*cm], repeatRows=1)
            tbl2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f6fffa')]),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            elements.append(tbl2)
            
            if len(good_segments) > len(sample):
                elements.append(Spacer(1, 6))
                elements.append(Paragraph(f"…and {len(good_segments) - len(sample)} more.", small_style))
        
        # Add page break between files (except after last file)
        if idx < len(files_data) - 1:
            elements.append(PageBreak())
    
    doc.build(elements)
    print(f"  ✓ Generated consolidated report: {output_file}")

def process_folder(folder_path, output_folder='reports'):
    """Process all XLIFF files in a folder."""
    folder = Path(folder_path)
    
    # Create output folder inside the analysis folder
    output_path = folder / output_folder
    output_path.mkdir(exist_ok=True)
    
    xliff_files = list(folder.glob('*.sdlxliff'))
    
    if not xliff_files:
        print(f"No .sdlxliff files found in {folder_path}")
        return
    
    print(f"Found {len(xliff_files)} XLIFF file(s) to process\n")
    
    files_data = []
    
    for xliff_file in xliff_files:
        print(f"Processing: {xliff_file.name}")
        
        try:
            quality_data, metadata = parse_xliff_quality_data(xliff_file)
            
            if not quality_data:
                print(f"  Warning: No quality data found in {xliff_file.name}")
                continue
            
            stats = calculate_statistics(quality_data)
            
            files_data.append({
                'quality_data': quality_data,
                'metadata': metadata,
                'stats': stats
            })
            
            print(f"  ✓ Processed {len(quality_data)} segments")
            
        except Exception as e:
            print(f"  Error processing {xliff_file.name}: {e}")
    
    # Create consolidated report
    if files_data:
        print("\nGenerating consolidated report...")
        output_file = output_path / 'quality_report.pdf'
        create_consolidated_report(files_data, str(output_file))
    
    print(f"\n{'='*60}")
    print(f"Processing complete. Report saved to: {output_path.absolute()}")
    print(f"{'='*60}")

def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1:
        # Folder path provided as command line argument
        folder_path = sys.argv[1]
        output_folder = sys.argv[2] if len(sys.argv) > 2 else 'reports'
    else:
        # Prompt for folder path
        print("="*60)
        print("XLIFF Quality Report Generator")
        print("="*60)
        print()
        
        folder_path = input("Enter the path to the folder containing XLIFF files: ").strip()
        
        # Remove quotes if user copied path with quotes
        folder_path = folder_path.strip('"').strip("'")
        
        if not folder_path:
            print("No path provided. Exiting.")
            return
        
        # Check if path exists
        if not Path(folder_path).exists():
            print(f"Error: Path does not exist: {folder_path}")
            return
        
        # Prompt for output folder (optional)
        output_folder = input("Enter output folder name (press Enter for 'reports'): ").strip()
        if not output_folder:
            output_folder = 'reports'
    
    process_folder(folder_path, output_folder)

if __name__ == "__main__":
    main()