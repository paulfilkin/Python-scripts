
"""
Cross-language comparative report for XLIFF evaluations.
Compares multiple languages and translation sources in a single PDF with exportable charts.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
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
from collections import Counter, defaultdict
import os
import sys
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def find_and_register_unicode_font():
    """Find and register a Unicode-capable font."""
    font_candidates = []

    if sys.platform.startswith('linux'):
        font_candidates = [
            ('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc', 'NotoSansCJK'),
            ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 'NotoSansCJK'),
            ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 'DejaVu'),
            ('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf', 'Liberation'),
        ]
    elif sys.platform.startswith('win'):
        font_candidates = [
            ('C:\\Windows\\Fonts\\arial.ttf', 'C:\\Windows\\Fonts\\arialbd.ttf', 'Arial'),
            ('C:\\Windows\\Fonts\\calibri.ttf', 'C:\\Windows\\Fonts\\calibrib.ttf', 'Calibri'),
        ]
    elif sys.platform == 'darwin':
        font_candidates = [
            ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf', 'Arial'),
        ]

    for regular_path, bold_path, font_family in font_candidates:
        try:
            if os.path.exists(regular_path) and os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont('UniFont', regular_path))
                pdfmetrics.registerFont(TTFont('UniFontBold', bold_path))
                return ('UniFont', 'UniFontBold')
        except Exception:
            continue

    return ('Helvetica', 'Helvetica-Bold')


def load_evaluation_json(file_path: Path) -> dict:
    """Load and parse evaluation JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_statistics(data: dict) -> dict:
    """Extract statistics from evaluation data."""
    results = data.get('results', [])
    valid_evals = [e for e in results if e.get('overall_score') is not None]

    if not valid_evals:
        return None

    scores = [e['overall_score'] for e in valid_evals]

    # Dimension scores
    dim_scores = defaultdict(list)
    for e in valid_evals:
        dims = e.get('dimensions', {})
        for dim, score in dims.items():
            if score is not None:
                dim_scores[dim].append(score)

    dim_avg = {dim: statistics.mean(scores) for dim, scores in dim_scores.items() if scores}

    # Issue categories
    issue_counts = Counter()
    for e in valid_evals:
        for issue in e.get('issues', []):
            issue_counts[issue.get('type', 'unknown')] += 1

    # Calculate % needing review (below 70)
    needing_review = len([s for s in scores if s < 70])
    review_pct = (needing_review / len(scores) * 100) if scores else 0

    return {
        'total_segments': len(results),
        'evaluated_segments': len(valid_evals),
        'avg_score': statistics.mean(scores),
        'median_score': statistics.median(scores),
        'min_score': min(scores),
        'max_score': max(scores),
        'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0,
        'needing_review_pct': review_pct,
        'dimension_scores': dim_avg,
        'issue_counts': dict(issue_counts),
        'scores': scores
    }


def create_cross_language_report(
    evaluations: list,
    output_dir: Path,
    report_title: str = "Cross-Language Quality Analysis"
) -> tuple:
    """
    Create cross-language comparison report.

    Args:
        evaluations: List of dicts with:
            - 'filename': Original filename
            - 'label': Display label (e.g., "Turkish - MT")
            - 'language': Target language code (e.g., "tr-TR")
            - 'source_type': Translation source (MT, AI, HT, etc.)
            - 'data': Loaded JSON data
            - 'stats': Extracted statistics
        output_dir: Directory for output files
        report_title: Title for the report

    Returns:
        Tuple of (pdf_path, list of chart paths)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    chart_paths = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create charts
    # 1. Overall score comparison by language
    score_chart = output_dir / f"chart_scores_{timestamp}.png"
    _create_score_comparison_chart(evaluations, score_chart)
    chart_paths.append(score_chart)

    # 2. Clustered bar chart - scores by source type per language
    if _has_multiple_source_types(evaluations):
        clustered_chart = output_dir / f"chart_clustered_{timestamp}.png"
        _create_clustered_comparison_chart(evaluations, clustered_chart)
        chart_paths.append(clustered_chart)

    # 3. Issue category breakdown
    issue_chart = output_dir / f"chart_issues_{timestamp}.png"
    _create_issue_category_chart(evaluations, issue_chart)
    chart_paths.append(issue_chart)

    # 4. Dimension comparison radar
    radar_chart = output_dir / f"chart_radar_{timestamp}.png"
    _create_dimension_radar_comparison(evaluations, radar_chart)
    chart_paths.append(radar_chart)

    # 5. Needing review percentage
    review_chart = output_dir / f"chart_review_{timestamp}.png"
    _create_review_percentage_chart(evaluations, review_chart)
    chart_paths.append(review_chart)

    # Create PDF report
    pdf_path = output_dir / f"cross_language_report_{timestamp}.pdf"
    _create_pdf_report(evaluations, pdf_path, chart_paths, report_title)

    return pdf_path, chart_paths


def _has_multiple_source_types(evaluations: list) -> bool:
    """Check if there are multiple source types to compare."""
    source_types = set(e.get('source_type', 'Unknown') for e in evaluations)
    return len(source_types) > 1


def _create_score_comparison_chart(evaluations: list, output_path: Path):
    """Create horizontal bar chart comparing overall scores."""
    fig, ax = plt.subplots(figsize=(12, max(6, len(evaluations) * 0.6)))

    # Sort by score
    sorted_evals = sorted(evaluations, key=lambda x: x['stats']['avg_score'])

    labels = [e['label'] for e in sorted_evals]
    scores = [e['stats']['avg_score'] for e in sorted_evals]
    medians = [e['stats']['median_score'] for e in sorted_evals]

    y_pos = np.arange(len(labels))

    # Color based on score
    colors_list = ['#4caf50' if s >= 90 else '#8bc34a' if s >= 80 else '#ffc107' if s >= 70 else '#f44336' for s in scores]

    bars = ax.barh(y_pos, scores, color=colors_list, alpha=0.8, label='Average')
    ax.scatter(medians, y_pos, color='navy', marker='|', s=200, linewidths=3, label='Median', zorder=5)

    # Add score labels
    for i, (bar, score, median) in enumerate(zip(bars, scores, medians)):
        ax.text(score + 1, i, f'{score:.1f}', va='center', fontsize=10, fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Overall Quality Score Comparison', fontsize=14, fontweight='bold')
    ax.set_xlim(0, 105)
    ax.grid(axis='x', alpha=0.3)
    ax.legend(loc='lower right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def _create_clustered_comparison_chart(evaluations: list, output_path: Path):
    """Create clustered bar chart comparing source types across languages."""
    # Group by language
    by_language = defaultdict(dict)
    source_types = set()

    for e in evaluations:
        lang = e.get('language', 'Unknown')
        source = e.get('source_type', 'Unknown')
        by_language[lang][source] = e['stats']['avg_score']
        source_types.add(source)

    source_types = sorted(source_types)
    languages = sorted(by_language.keys())

    fig, ax = plt.subplots(figsize=(max(10, len(languages) * 2), 8))

    x = np.arange(len(languages))
    width = 0.8 / len(source_types)

    # Colours for different source types
    source_colors = {
        'MT': '#2196f3',
        'AI': '#4caf50',
        'HT': '#ff9800',
        'MLT': '#9c27b0',
    }
    default_colors = ['#607d8b', '#795548', '#009688', '#e91e63']

    for i, source in enumerate(source_types):
        scores = [by_language[lang].get(source, 0) for lang in languages]
        color = source_colors.get(source, default_colors[i % len(default_colors)])
        bars = ax.bar(x + i * width - (len(source_types) - 1) * width / 2, scores,
                      width, label=source, color=color, alpha=0.8)

        # Add value labels
        for bar, score in zip(bars, scores):
            if score > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                        f'{score:.1f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_xlabel('Language', fontsize=12, fontweight='bold')
    ax.set_ylabel('Average Score', fontsize=12, fontweight='bold')
    ax.set_title('Score Comparison by Translation Source', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(languages, fontsize=10)
    ax.set_ylim(0, 105)
    ax.legend(title='Source Type')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def _create_issue_category_chart(evaluations: list, output_path: Path):
    """Create clustered bar chart showing issue categories by evaluation."""
    # Collect all issue types
    all_issues = set()
    for e in evaluations:
        all_issues.update(e['stats'].get('issue_counts', {}).keys())

    if not all_issues:
        return

    issue_types = sorted(all_issues)

    fig, ax = plt.subplots(figsize=(max(10, len(evaluations) * 1.5), 8))

    x = np.arange(len(issue_types))
    width = 0.8 / len(evaluations)

    # Colours
    colors_list = plt.cm.tab10(np.linspace(0, 1, len(evaluations)))

    for i, e in enumerate(evaluations):
        counts = e['stats'].get('issue_counts', {})
        total = sum(counts.values()) or 1
        # Convert to percentages
        pcts = [(counts.get(issue, 0) / total * 100) for issue in issue_types]

        bars = ax.bar(x + i * width - (len(evaluations) - 1) * width / 2, pcts,
                      width, label=e['label'][:20], color=colors_list[i], alpha=0.8)

    ax.set_xlabel('Issue Category', fontsize=12, fontweight='bold')
    ax.set_ylabel('Percentage of Issues', fontsize=12, fontweight='bold')
    ax.set_title('Issue Distribution by Category', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace('_', ' ').title() for t in issue_types], fontsize=10, rotation=45, ha='right')
    ax.legend(title='Evaluation', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def _create_dimension_radar_comparison(evaluations: list, output_path: Path):
    """Create radar chart comparing quality dimensions across evaluations."""
    dimensions = ['accuracy', 'fluency', 'style', 'context_coherence']
    dim_labels = ['Accuracy', 'Fluency', 'Style', 'Context\nCoherence']

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
    angles += angles[:1]

    colors_list = plt.cm.tab10(np.linspace(0, 1, len(evaluations)))

    for i, e in enumerate(evaluations):
        dim_scores = e['stats'].get('dimension_scores', {})
        values = [dim_scores.get(d, 0) for d in dimensions]
        values += values[:1]

        ax.plot(angles, values, 'o-', linewidth=2, label=e['label'][:25], color=colors_list[i])
        ax.fill(angles, values, alpha=0.1, color=colors_list[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dim_labels, fontsize=11)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.grid(True, alpha=0.3)
    ax.set_title('Quality Dimensions Comparison', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1), fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def _create_review_percentage_chart(evaluations: list, output_path: Path):
    """Create bar chart showing percentage needing review."""
    fig, ax = plt.subplots(figsize=(12, max(6, len(evaluations) * 0.6)))

    sorted_evals = sorted(evaluations, key=lambda x: x['stats']['needing_review_pct'])

    labels = [e['label'] for e in sorted_evals]
    review_pcts = [e['stats']['needing_review_pct'] for e in sorted_evals]

    y_pos = np.arange(len(labels))

    # Color: green = low review %, red = high
    colors_list = ['#4caf50' if p <= 5 else '#8bc34a' if p <= 10 else '#ffc107' if p <= 20 else '#f44336' for p in review_pcts]

    bars = ax.barh(y_pos, review_pcts, color=colors_list, alpha=0.8)

    for i, (bar, pct) in enumerate(zip(bars, review_pcts)):
        ax.text(pct + 0.5, i, f'{pct:.1f}%', va='center', fontsize=10, fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel('Percentage Needing Review (<70 score)', fontsize=12, fontweight='bold')
    ax.set_title('Segments Requiring Attention', fontsize=14, fontweight='bold')
    ax.set_xlim(0, max(review_pcts) * 1.2 + 5 if review_pcts else 20)
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def _create_pdf_report(evaluations: list, output_path: Path, chart_paths: list, title: str):
    """Create PDF report with all charts and summary tables."""
    doc = SimpleDocTemplate(
        str(output_path), pagesize=landscape(A4),
        rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm
    )

    font_name, font_bold = find_and_register_unicode_font()

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'],
        fontName=font_bold, fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        alignment=TA_CENTER, spaceAfter=0.5*cm
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2', parent=styles['Heading2'],
        fontName=font_bold, fontSize=16,
        textColor=colors.HexColor('#1976d2'),
        spaceAfter=0.3*cm
    )

    normal_style = ParagraphStyle(
        'CustomNormal', parent=styles['Normal'],
        fontName=font_name, fontSize=11, leading=14
    )

    small_style = ParagraphStyle(
        'CustomSmall', parent=styles['Normal'],
        fontName=font_name, fontSize=9, leading=12
    )

    elements = []

    # Cover page
    elements.append(Spacer(1, 2*cm))
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 1*cm))

    report_date = datetime.now().strftime("%d %B %Y, %H:%M")
    elements.append(Paragraph(f"<b>Generated:</b> {report_date}", normal_style))
    elements.append(Paragraph(f"<b>Evaluations Compared:</b> {len(evaluations)}", normal_style))
    elements.append(Spacer(1, 0.5*cm))

    # List evaluations
    elements.append(Paragraph("<b>Files Included:</b>", normal_style))
    for e in evaluations:
        elements.append(Paragraph(f"• {e['label']} ({e.get('language', 'Unknown')} - {e.get('source_type', 'Unknown')})", small_style))

    elements.append(PageBreak())

    # Summary table
    elements.append(Paragraph("Summary Statistics", heading2_style))
    elements.append(Spacer(1, 0.3*cm))

    # Build summary table
    headers = ['Evaluation', 'Language', 'Source', 'Avg', 'Median', 'Min', 'Max', 'Std Dev', '% Review']
    table_data = [headers]

    sorted_evals = sorted(evaluations, key=lambda x: x['stats']['avg_score'], reverse=True)

    for e in sorted_evals:
        s = e['stats']
        table_data.append([
            Paragraph(e['label'][:30], small_style),
            e.get('language', '-'),
            e.get('source_type', '-'),
            f"{s['avg_score']:.1f}",
            f"{s['median_score']:.1f}",
            f"{s['min_score']:.0f}",
            f"{s['max_score']:.0f}",
            f"{s['std_dev']:.1f}",
            f"{s['needing_review_pct']:.1f}%"
        ])

    summary_table = Table(table_data, colWidths=[5*cm, 2*cm, 2*cm, 1.5*cm, 1.5*cm, 1.3*cm, 1.3*cm, 1.5*cm, 1.8*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e3f2fd')]),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.5*cm))

    # Overall statistics
    all_avgs = [e['stats']['avg_score'] for e in evaluations]
    all_medians = [e['stats']['median_score'] for e in evaluations]
    all_review = [e['stats']['needing_review_pct'] for e in evaluations]

    elements.append(Paragraph(f"<b>Overall Average:</b> {statistics.mean(all_avgs):.1f} | "
                              f"<b>Overall Median:</b> {statistics.mean(all_medians):.1f} | "
                              f"<b>Average % Needing Review:</b> {statistics.mean(all_review):.1f}%", normal_style))

    elements.append(PageBreak())

    # Charts
    for chart_path in chart_paths:
        if chart_path.exists():
            elements.append(Image(str(chart_path), width=24*cm, height=14*cm))
            elements.append(Spacer(1, 0.5*cm))

    # Build PDF
    doc.build(elements)
    print(f"✓ Generated cross-language report: {output_path}")