"""
Enhanced PDF report generation for Really Smart Review.
Extends the basic report with LLM-powered insights and detailed analysis.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime
from pathlib import Path
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def create_enhanced_report(all_results, output_file, config):
    """
    Create comprehensive PDF report from Smart Review results.
    
    Args:
        all_results: List of file analysis results
        output_file: Path for output PDF
        config: Configuration used for analysis
    """
    doc = SimpleDocTemplate(
        str(output_file), pagesize=A4,
        rightMargin=36, leftMargin=36, topMargin=48, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#424242'),
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#283593'),
        spaceBefore=16,
        spaceAfter=10
    )
    
    small_style = ParagraphStyle(
        'small',
        parent=styles['Normal'],
        fontSize=9,
        leading=12
    )
    
    elements = []
    
    # COVER PAGE
    elements.append(Spacer(1, 4*cm))
    elements.append(Paragraph("Really Smart Review", title_style))
    elements.append(Paragraph("LLM-Powered Translation Quality Analysis", subtitle_style))
    elements.append(Spacer(1, 2*cm))
    
    report_date = datetime.now().strftime("%d %B %Y, %H:%M")
    elements.append(Paragraph(f"<b>Generated:</b> {report_date}", styles['Normal']))
    elements.append(Paragraph(f"<b>Files Analyzed:</b> {len(all_results)}", styles['Normal']))
    elements.append(Paragraph(f"<b>Model Used:</b> {config['llm_provider']['model']}", styles['Normal']))
    elements.append(Paragraph(f"<b>Profile:</b> {config['review_profile'].replace('_', ' ').title()}", styles['Normal']))
    elements.append(Paragraph(f"<b>Content Type:</b> {config['content_type'].replace('_', ' ').title()}", styles['Normal']))
    elements.append(PageBreak())
    
    # EXECUTIVE SUMMARY
    elements.append(Paragraph("Executive Summary", title_style))
    elements.append(Spacer(1, 12))
    
    # Calculate overall statistics
    total_segments = sum(r['statistics']['total_segments'] for r in all_results)
    total_evaluated = sum(r['statistics']['evaluated_segments'] for r in all_results)
    
    all_scores = []
    for result in all_results:
        for eval in result['evaluations']:
            if eval.get('overall_score') is not None:
                all_scores.append(eval['overall_score'])
    
    if all_scores:
        overall_avg = statistics.mean(all_scores)
        overall_median = statistics.median(all_scores)
        
        # Quality band
        if overall_avg >= 90:
            quality_band = "Excellent"
            band_color = "#4caf50"
        elif overall_avg >= 80:
            quality_band = "Good"
            band_color = "#8bc34a"
        elif overall_avg >= 70:
            quality_band = "Acceptable"
            band_color = "#ffc107"
        elif overall_avg >= 60:
            quality_band = "Needs Improvement"
            band_color = "#ff9800"
        else:
            quality_band = "Poor"
            band_color = "#f44336"
        
        summary_rows = [
            ['Total Segments Analyzed', str(total_segments)],
            ['Successfully Evaluated', str(total_evaluated)],
            ['Overall Average Score', f"{overall_avg:.1f}/100"],
            ['Overall Median Score', f"{overall_median:.1f}/100"],
            ['Quality Assessment', quality_band]
        ]
        
        summary_table = Table(summary_rows, colWidths=[8*cm, 6*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor(band_color)),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke if overall_avg < 70 else colors.black),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
    
    # Aggregate issue categories
    all_issues = {}
    for result in all_results:
        for category, count in result['statistics'].get('issue_categories', {}).items():
            all_issues[category] = all_issues.get(category, 0) + count
    
    if all_issues:
        elements.append(Paragraph("Issue Distribution", heading_style))
        
        sorted_issues = sorted(all_issues.items(), key=lambda x: x[1], reverse=True)
        issue_rows = [['Issue Type', 'Count', 'Percentage']]
        total_issues = sum(all_issues.values())
        
        for issue_type, count in sorted_issues[:10]:  # Top 10
            pct = (count / total_issues) * 100
            issue_rows.append([issue_type.replace('_', ' ').title(), str(count), f"{pct:.1f}%"])
        
        issue_table = Table(issue_rows, colWidths=[6*cm, 3*cm, 3*cm])
        issue_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff6f00')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff3e0')]),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ]))
        
        elements.append(issue_table)
        elements.append(Spacer(1, 20))
    
    # Create visualizations
    chart_dir = Path(output_file).parent / 'charts'
    chart_dir.mkdir(exist_ok=True)
    
    # Score distribution chart
    if all_scores:
        score_dist_path = chart_dir / 'score_distribution.png'
        create_score_distribution_chart(all_scores, score_dist_path)
        elements.append(Paragraph("Score Distribution", heading_style))
        elements.append(Image(str(score_dist_path), width=14*cm, height=8*cm))
        elements.append(Spacer(1, 12))
    
    # Dimension analysis
    all_dimensions = {'accuracy': [], 'fluency': [], 'style': [], 'context_coherence': []}
    for result in all_results:
        for eval in result['evaluations']:
            if 'dimensions' in eval:
                for dim, score in eval['dimensions'].items():
                    if dim in all_dimensions:
                        all_dimensions[dim].append(score)
    
    if any(all_dimensions.values()):
        dim_avg = {k: statistics.mean(v) if v else 0 for k, v in all_dimensions.items()}
        
        radar_path = chart_dir / 'dimension_radar.png'
        create_dimension_radar_chart(dim_avg, radar_path)
        elements.append(Paragraph("Quality Dimensions", heading_style))
        elements.append(Image(str(radar_path), width=12*cm, height=12*cm))
    
    elements.append(PageBreak())
    
    # FILE-BY-FILE ANALYSIS
    elements.append(Paragraph("Detailed File Analysis", title_style))
    elements.append(Spacer(1, 12))
    
    for idx, result in enumerate(all_results):
        elements.extend(create_file_section(result, idx, chart_dir, small_style, styles, heading_style))
        
        if idx < len(all_results) - 1:
            elements.append(PageBreak())
    
    # Build PDF
    doc.build(elements)
    print(f"✓ Generated comprehensive report: {output_file}")


def create_file_section(result, idx, chart_dir, small_style, styles, heading_style):
    """Create detailed section for a single file."""
    elements = []
    
    metadata = result['metadata']
    stats = result['statistics']
    evaluations = result['evaluations']
    
    # File header
    elements.append(Paragraph(f"File: {result['file_name']}", heading_style))
    elements.append(Paragraph(f"<b>Language Pair:</b> {metadata['source_language']} → {metadata['target_language']}", styles['Normal']))
    elements.append(Paragraph(f"<b>Segments:</b> {stats['total_segments']} total, {stats['evaluated_segments']} evaluated", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Statistics table
    stat_rows = [
        ['Metric', 'Value'],
        ['Average Score', f"{stats['average_score']:.1f}/100"],
        ['Median Score', f"{stats['median_score']:.1f}/100"],
        ['Score Range', f"{stats['min_score']:.0f} - {stats['max_score']:.0f}"],
        ['Segments Needing Review', f"{stats['segments_needing_review']} ({stats['segments_needing_review']/stats['total_segments']*100:.1f}%)"]
    ]
    
    stat_table = Table(stat_rows, colWidths=[8*cm, 6*cm])
    stat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5c6bc0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8eaf6')]),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ]))
    
    elements.append(stat_table)
    elements.append(Spacer(1, 12))
    
    # Score distribution for this file
    file_scores = [e['overall_score'] for e in evaluations if e.get('overall_score') is not None]
    if file_scores:
        score_chart_path = chart_dir / f'file_{idx}_scores.png'
        create_file_score_chart(file_scores, score_chart_path)
        elements.append(Image(str(score_chart_path), width=12*cm, height=6*cm))
        elements.append(Spacer(1, 12))
    
    # Critical issues - handle None scores safely
    critical_issues = []
    for eval in evaluations:
        score = eval.get('overall_score')
        if score is not None and score < 70:
            critical_issues.append(eval)
    
    if critical_issues:
        elements.append(Paragraph(f"Segments Requiring Attention ({len(critical_issues)})", heading_style))
        
        issue_rows = [['ID', 'Score', 'Issues', 'Explanation']]
        
        for eval in critical_issues[:20]:  # Limit to top 20
            issues_text = ', '.join([i['type'].replace('_', ' ') for i in eval.get('issues', [])])
            explanation = eval.get('explanation', 'No explanation')
            
            # Truncate long explanations
            if len(explanation) > 200:
                explanation = explanation[:200] + '...'
            
            # Handle None score safely
            score_display = f"{eval['overall_score']:.0f}" if eval.get('overall_score') is not None else "Error"
            
            issue_rows.append([
                str(eval['segment_id']),
                score_display,  # Changed this line
                Paragraph(issues_text, small_style),
                Paragraph(explanation, small_style)
            ])
        
        issue_table = Table(issue_rows, colWidths=[1.5*cm, 1.5*cm, 4*cm, 8*cm], repeatRows=1)
        issue_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d32f2f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ffebee')]),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ]))
        
        elements.append(issue_table)
        
        if len(critical_issues) > 20:
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(f"...and {len(critical_issues) - 20} more segments requiring review.", small_style))
    
    elements.append(Spacer(1, 12))
    
    # Sample excellent segments
    excellent = [e for e in evaluations if e.get('overall_score') is not None and e['overall_score'] >= 95]
    if excellent:
        elements.append(Paragraph(f"Excellent Quality Samples ({len(excellent)} segments)", heading_style))
        
        sample_rows = [['ID', 'Score', 'Source', 'Target']]
        
        for eval in excellent[:5]:
            sample_rows.append([
                str(eval['segment_id']),
                f"{eval['overall_score']:.0f}",
                Paragraph(eval['source'][:150], small_style),
                Paragraph(eval['target'][:150], small_style)
            ])
        
        sample_table = Table(sample_rows, colWidths=[1.5*cm, 1.5*cm, 7*cm, 7*cm], repeatRows=1)
        sample_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#388e3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8f5e9')]),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ]))
        
        elements.append(sample_table)
    
    return elements


def create_score_distribution_chart(scores, output_path):
    """Create histogram of score distribution."""
    plt.figure(figsize=(10, 6), dpi=150)
    
    bins = [0, 50, 60, 70, 80, 90, 100]
    
    # Create histogram and get the patches to color individually
    n, bins_out, patches = plt.hist(scores, bins=bins, edgecolor='black', alpha=0.7)
    
    # Color each bar based on score range
    colors_list = ['#d32f2f', '#f57c00', '#fbc02d', '#8bc34a', '#4caf50', '#2e7d32']
    for i, patch in enumerate(patches):
        if i < len(colors_list):
            patch.set_facecolor(colors_list[i])
    
    plt.xlabel('Score Range', fontsize=12)
    plt.ylabel('Number of Segments', fontsize=12)
    plt.title('Quality Score Distribution', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    
    # Add average line
    avg = statistics.mean(scores)
    plt.axvline(avg, color='navy', linestyle='--', linewidth=2, label=f'Average: {avg:.1f}')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(str(output_path))
    plt.close()


def create_dimension_radar_chart(dimensions, output_path):
    """Create radar chart for quality dimensions."""
    categories = list(dimensions.keys())
    values = list(dimensions.values())
    
    # Format labels
    labels = [c.replace('_', ' ').title() for c in categories]
    
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'), dpi=150)
    ax.plot(angles, values, 'o-', linewidth=2, color='#3f51b5', label='Scores')
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


def create_file_score_chart(scores, output_path):
    """Create bar chart showing score ranges for a file."""
    plt.figure(figsize=(10, 5), dpi=150)
    
    ranges = {
        '90-100': len([s for s in scores if s >= 90]),
        '80-89': len([s for s in scores if 80 <= s < 90]),
        '70-79': len([s for s in scores if 70 <= s < 80]),
        '60-69': len([s for s in scores if 60 <= s < 70]),
        '0-59': len([s for s in scores if s < 60])
    }
    
    colors_list = ['#2e7d32', '#4caf50', '#8bc34a', '#fbc02d', '#d32f2f']
    
    plt.bar(ranges.keys(), ranges.values(), color=colors_list, edgecolor='black')
    plt.xlabel('Score Range', fontsize=11)
    plt.ylabel('Number of Segments', fontsize=11)
    plt.title('Score Distribution', fontsize=13, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(str(output_path))
    plt.close()
