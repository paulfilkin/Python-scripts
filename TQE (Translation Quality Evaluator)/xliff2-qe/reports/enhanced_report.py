"""
Enhanced PDF report generation for XLIFF 2.0 QE system.
Provides detailed analysis with visualisations matching Really Smart Review style.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from pathlib import Path
import statistics
from collections import Counter
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def find_and_register_unicode_font():
    """
    Try to find and register a Unicode-capable font on the system.
    Prioritizes CJK-capable fonts for Asian language support.
    Returns (font_name, font_bold) tuple.
    """
    font_candidates = []
    
    # Linux - prioritize CJK fonts first
    if sys.platform.startswith('linux'):
        cjk_fonts = [
            # Noto Sans CJK (best CJK support)
            ('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc', 'NotoSansCJK'),
            ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 'NotoSansCJK'),
            # WQY (Chinese)
            ('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 'WQY'),
            # Standard fallbacks
            ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 'DejaVu'),
            ('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf', 'Liberation'),
            ('/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf', 'Liberation2'),
        ]
        font_candidates.extend(cjk_fonts)
    
    # Windows
    if sys.platform.startswith('win'):
        font_candidates.extend([
            ('C:\\Windows\\Fonts\\msgothic.ttc', 'C:\\Windows\\Fonts\\msgothic.ttc', 'MSGothic'),  # Japanese
            ('C:\\Windows\\Fonts\\msyh.ttc', 'C:\\Windows\\Fonts\\msyhbd.ttc', 'MSYaHei'),  # Chinese
            ('C:\\Windows\\Fonts\\arial.ttf', 'C:\\Windows\\Fonts\\arialbd.ttf', 'Arial'),
            ('C:\\Windows\\Fonts\\calibri.ttf', 'C:\\Windows\\Fonts\\calibrib.ttf', 'Calibri'),
        ])
    
    # macOS
    elif sys.platform == 'darwin':
        font_candidates.extend([
            ('/System/Library/Fonts/PingFang.ttc', '/System/Library/Fonts/PingFang.ttc', 'PingFang'),  # Chinese
            ('/System/Library/Fonts/Hiragino Sans GB.ttc', '/System/Library/Fonts/Hiragino Sans GB.ttc', 'HiraginoSans'),
            ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf', 'Arial'),
            ('/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/Helvetica.ttc', 'Helvetica'),
        ])
    
    for regular_path, bold_path, font_family in font_candidates:
        try:
            if os.path.exists(regular_path) and os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont('UniFont', regular_path))
                pdfmetrics.registerFont(TTFont('UniFontBold', bold_path))
                print(f"✓ Using {font_family} fonts for CJK/Unicode support")
                return ('UniFont', 'UniFontBold')
        except Exception as e:
            continue
    
    print("⚠ WARNING: No Unicode-capable fonts found - special characters may display incorrectly")
    return ('Helvetica', 'Helvetica-Bold')


def create_evaluation_report(evaluations: list, output_file: Path, config: dict, metadata: dict, attention_threshold: float = 70):
    """
    Create comprehensive PDF report from evaluation results.
    
    Args:
        evaluations: List of segment evaluations
        output_file: Path for output PDF
        config: Configuration used
        metadata: XLIFF metadata (languages, etc.)
        attention_threshold: Score below which segments require attention (default: 70)
    """
    doc = SimpleDocTemplate(
        str(output_file), pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm
    )
    
    # Register Unicode fonts
    font_name, font_bold = find_and_register_unicode_font()
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_bold,
        fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        alignment=TA_CENTER,
        spaceAfter=0.5*cm
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        textColor=colors.HexColor('#424242'),
        alignment=TA_CENTER,
        spaceAfter=0.3*cm
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontName=font_bold,
        fontSize=16,
        textColor=colors.HexColor('#283593'),
        spaceAfter=0.3*cm,
        spaceBefore=0.5*cm
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontName=font_bold,
        fontSize=14,
        textColor=colors.HexColor('#3f51b5'),
        spaceAfter=0.2*cm,
        spaceBefore=0.3*cm
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10
    )
    
    small_style = ParagraphStyle(
        'CustomSmall',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        leading=12
    )
    
    elements = []
    
    # COVER PAGE
    elements.append(Spacer(1, 3*cm))
    elements.append(Paragraph("Translation Quality Evaluation", title_style))
    elements.append(Paragraph("LLM-Powered Quality Analysis", subtitle_style))
    elements.append(Spacer(1, 2*cm))
    
    # Metadata
    report_date = datetime.now().strftime("%d %B %Y, %H:%M")
    source_filename = output_file.stem.replace('_evaluation', '')  # Remove _evaluation suffix
    elements.append(Paragraph(f"<b>File:</b> {source_filename}", normal_style))
    elements.append(Paragraph(f"<b>Generated:</b> {report_date}", normal_style))
    elements.append(Paragraph(f"<b>Source Language:</b> {metadata['source_language']}", normal_style))
    elements.append(Paragraph(f"<b>Target Language:</b> {metadata['target_language']}", normal_style))
    elements.append(Paragraph(f"<b>Segments Evaluated:</b> {len(evaluations)}", normal_style))
    elements.append(Paragraph(f"<b>Model:</b> {config['llm_provider']['model']}", normal_style))
    elements.append(Paragraph(f"<b>Content Type:</b> {config.get('content_type', 'general').replace('_', ' ').title()}", normal_style))
    
    elements.append(PageBreak())
    
    # Calculate statistics
    valid_evals = [e for e in evaluations if e.get('overall_score') is not None]
    valid_scores = [e['overall_score'] for e in valid_evals]
    
    if not valid_scores:
        elements.append(Paragraph("No valid evaluation results found.", normal_style))
        doc.build(elements)
        return
    
    # EXECUTIVE SUMMARY
    elements.append(Paragraph("Executive Summary", heading1_style))
    
    avg_score = statistics.mean(valid_scores)
    median_score = statistics.median(valid_scores)
    min_score = min(valid_scores)
    max_score = max(valid_scores)
    
    # Quality assessment
    quality_band, band_color = _get_quality_band(avg_score)
    
    # Score ranges
    excellent = sum(1 for s in valid_scores if s >= 90)
    good = sum(1 for s in valid_scores if 80 <= s < 90)
    acceptable = sum(1 for s in valid_scores if 70 <= s < 80)
    needs_review = sum(1 for s in valid_scores if 60 <= s < 70)
    poor = sum(1 for s in valid_scores if s < 60)
    
    summary_data = [
        ['Total Segments Analyzed', str(len(evaluations))],
        ['Successfully Evaluated', str(len(valid_evals))],
        ['Overall Average Score', f"{avg_score:.1f}/100"],
        ['Overall Median Score', f"{median_score:.1f}/100"],
        ['Quality Assessment', quality_band]
    ]
    
    summary_table = Table(summary_data, colWidths=[8*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (0, -1), font_bold),
        ('FONTNAME', (1, 0), (-1, -1), font_name),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor(band_color)),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke if avg_score < 70 else colors.black),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 1*cm))
    
    # Issue Distribution
    all_issues = []
    for eval in valid_evals:
        all_issues.extend(eval.get('issues', []))
    
    if all_issues:
        elements.append(Paragraph("Issue Distribution", heading2_style))
        
        issue_type_counter = Counter(issue['type'] for issue in all_issues)
        issue_data = [['Issue Type', 'Count', 'Percentage']]
        total_issues = len(all_issues)
        
        for issue_type, count in issue_type_counter.most_common(10):
            pct = count / total_issues * 100
            issue_data.append([
                issue_type.replace('_', ' ').title(),
                str(count),
                f"{pct:.1f}%"
            ])
        
        issue_table = Table(issue_data, colWidths=[6*cm, 3*cm, 3*cm])
        issue_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff6f00')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff3e0')]),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ]))
        
        elements.append(issue_table)
        elements.append(Spacer(1, 0.5*cm))
    
    # Score Distribution Chart
    chart_path = output_file.parent / f"{output_file.stem}_chart_dist.png"
    _create_score_distribution_chart(valid_scores, chart_path)
    if chart_path.exists():
        elements.append(Paragraph("Score Distribution", heading2_style))
        elements.append(Image(str(chart_path), width=15*cm, height=9*cm))
        elements.append(Spacer(1, 0.5*cm))
    
    elements.append(PageBreak())
    
    # Quality Dimensions
    elements.append(Paragraph("Quality Dimensions", heading1_style))
    
    dimensions = ['accuracy', 'fluency', 'style', 'context_coherence']
    dim_scores = {dim: [] for dim in dimensions}
    
    for eval in valid_evals:
        dims = eval.get('dimensions', {})
        for dim in dimensions:
            if dim in dims and dims[dim] is not None:
                dim_scores[dim].append(dims[dim])
    
    # Dimension averages
    dim_avg = {dim: statistics.mean(scores) if scores else 0 for dim, scores in dim_scores.items()}
    
    # Radar chart
    radar_path = output_file.parent / f"{output_file.stem}_chart_radar.png"
    _create_dimension_radar_chart(dim_avg, radar_path)
    if radar_path.exists():
        elements.append(Image(str(radar_path), width=12*cm, height=12*cm))
    
    elements.append(PageBreak())
    
    # Detailed Results
    elements.append(Paragraph("Detailed Segment Results", heading1_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Segments requiring attention
    critical_segs = [e for e in valid_evals if e.get('overall_score', 100) < attention_threshold]
    
    if critical_segs:
        elements.append(Paragraph(f"Segments Requiring Attention ({len(critical_segs)})", heading2_style))
        
        issue_rows = [['ID', 'Score', 'Issues', 'Explanation']]
        
        for eval in sorted(critical_segs, key=lambda e: e.get('overall_score', 0)):
            issues_text = ', '.join([i['type'].replace('_', ' ') for i in eval.get('issues', [])])
            explanation = eval.get('explanation', 'No explanation')
            
            # Handle encoding
            if isinstance(explanation, bytes):
                explanation = explanation.decode('utf-8', errors='replace')
            
            # Escape XML
            explanation = explanation.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            score_display = f"{eval['overall_score']:.0f}" if eval.get('overall_score') is not None else "Error"
            
            issue_rows.append([
                str(eval['segment_id'])[:15],
                score_display,
                Paragraph(issues_text, small_style),
                Paragraph(explanation, small_style)
            ])
        
        issue_table = Table(issue_rows, colWidths=[2*cm, 1.5*cm, 4*cm, 9.5*cm], repeatRows=1)
        issue_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d32f2f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ffebee')]),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ]))
        
        elements.append(issue_table)
    
    elements.append(Spacer(1, 1*cm))
    
    # Excellent Quality Samples
    excellent_segs = [e for e in valid_evals if e.get('overall_score', 0) >= 95]
    
    if excellent_segs:
        elements.append(Paragraph(f"Excellent Quality Samples ({len(excellent_segs)} segments)", heading2_style))
        
        sample_rows = [['ID', 'Score', 'Source', 'Target']]
        
        for eval in excellent_segs[:5]:
            source_text = eval.get('source', '')[:150]
            target_text = eval.get('target', '')[:150]
            
            # Handle encoding
            if isinstance(source_text, bytes):
                source_text = source_text.decode('utf-8', errors='replace')
            if isinstance(target_text, bytes):
                target_text = target_text.decode('utf-8', errors='replace')
            
            # Escape XML
            source_text = source_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            target_text = target_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            sample_rows.append([
                str(eval['segment_id'])[:15],
                f"{eval['overall_score']:.0f}",
                Paragraph(source_text, small_style),
                Paragraph(target_text, small_style)
            ])
        
        sample_table = Table(sample_rows, colWidths=[1.5*cm, 1.5*cm, 7.5*cm, 7.5*cm], repeatRows=1)
        sample_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#388e3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8f5e9')]),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ]))
        
        elements.append(sample_table)
    
    # Build PDF
    doc.build(elements)
    
    # Clean up chart files
    for pattern in ['_chart_dist.png', '_chart_radar.png']:
        chart_file = output_file.parent / f"{output_file.stem}{pattern}"
        if chart_file.exists():
            chart_file.unlink()
    
    print(f"✓ Generated PDF report: {output_file}")


def _get_quality_band(score: float) -> tuple:
    """Get quality band and colour for a score."""
    if score >= 90:
        return "Excellent", "#4caf50"
    elif score >= 80:
        return "Good", "#8bc34a"
    elif score >= 70:
        return "Acceptable", "#ffc107"
    elif score >= 60:
        return "Needs Improvement", "#ff9800"
    else:
        return "Poor", "#f44336"


def _create_score_distribution_chart(scores: list, output_path: Path):
    """Create histogram of score distribution with percentages."""
    plt.figure(figsize=(10, 6), dpi=150)
    
    bins = [0, 60, 70, 80, 90, 100]
    colors_list = ['#d32f2f', '#fbc02d', '#8bc34a', '#4caf50', '#2e7d32']
    
    n, bins_out, patches = plt.hist(scores, bins=bins, edgecolor='black', alpha=0.8)
    
    # Colour bars
    for i, patch in enumerate(patches):
        if i < len(colors_list):
            patch.set_facecolor(colors_list[i])
    
    total = len(scores)
    
    # Add count and percentage labels
    for patch, count in zip(patches, n):
        if count > 0:
            height = patch.get_height()
            percentage = (count / total * 100)
            plt.text(patch.get_x() + patch.get_width()/2., height,
                    f'{int(count)}\n({percentage:.1f}%)',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.xlabel('Score Range', fontsize=12)
    plt.ylabel('Number of Segments', fontsize=12)
    plt.title('Quality Score Distribution', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Average line
    avg = statistics.mean(scores)
    plt.axvline(avg, color='navy', linestyle='--', linewidth=2, label=f'Average: {avg:.1f}')
    plt.legend(fontsize=10)
    
    plt.tight_layout()
    plt.savefig(str(output_path), bbox_inches='tight')
    plt.close()


def _create_dimension_radar_chart(dimensions: dict, output_path: Path):
    """Create radar chart for quality dimensions."""
    categories = list(dimensions.keys())
    values = list(dimensions.values())
    
    # Format labels
    labels = [c.replace('_', ' ').title() for c in categories]
    
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'), dpi=150)
    ax.plot(angles, values, 'o-', linewidth=2, color='#3f51b5')
    ax.fill(angles, values, alpha=0.25, color='#3f51b5')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=11)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], size=9)
    ax.set_title('Quality Dimensions', size=14, fontweight='bold', pad=20)
    ax.grid(True)
    
    plt.tight_layout()
    plt.savefig(str(output_path), bbox_inches='tight')
    plt.close()