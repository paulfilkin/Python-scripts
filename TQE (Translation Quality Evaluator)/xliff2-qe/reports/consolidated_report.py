"""
Consolidated comparison report for multiple XLIFF evaluations.
Compares different translation approaches in a single PDF.
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

# Import font registration from main report
from .enhanced_report import find_and_register_unicode_font


def create_consolidated_report(file_evaluations: list, output_file: Path, config: dict):
    """
    Create consolidated comparison report from multiple file evaluations.
    
    Args:
        file_evaluations: List of dicts with 'filename', 'label', 'results', 'metadata'
        output_file: Path for output PDF
        config: Configuration used
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
        fontSize=14,
        textColor=colors.HexColor('#424242'),
        alignment=TA_CENTER,
        spaceAfter=0.5*cm
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontName=font_bold,
        fontSize=16,
        textColor=colors.HexColor('#1976d2'),
        spaceAfter=0.3*cm
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=14
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
    elements.append(Paragraph("Translation Quality Comparison", title_style))
    elements.append(Paragraph("Consolidated Multi-File Analysis", subtitle_style))
    elements.append(Spacer(1, 2*cm))
    
    # Metadata
    report_date = datetime.now().strftime("%d %B %Y, %H:%M")
    elements.append(Paragraph(f"<b>Generated:</b> {report_date}", normal_style))
    elements.append(Paragraph(f"<b>Files Compared:</b> {len(file_evaluations)}", normal_style))
    elements.append(Paragraph(f"<b>Model:</b> {config['llm_provider']['model']}", normal_style))
    elements.append(Paragraph(f"<b>Content Type:</b> {config.get('content_type', 'general').replace('_', ' ').title()}", normal_style))
    elements.append(Paragraph(f"<b>Attention Threshold:</b> &lt;{config.get('attention_threshold', 70):.0f}/100", normal_style))
    
    elements.append(Spacer(1, 1*cm))
    
    # Files being compared
    elements.append(Paragraph("<b>Translation Methods Compared:</b>", normal_style))
    for idx, file_eval in enumerate(file_evaluations, 1):
        label = file_eval['label'] if file_eval['label'] else file_eval['filename']
        elements.append(Paragraph(f"{idx}. {label}", normal_style))
    
    elements.append(PageBreak())
    
    # COMPARATIVE SUMMARY
    elements.append(Paragraph("Comparative Summary", heading2_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Calculate statistics for each file
    comparison_data = []
    for file_eval in file_evaluations:
        results = file_eval['results']
        valid_evals = [e for e in results if e.get('overall_score') is not None]
        
        if valid_evals:
            scores = [e['overall_score'] for e in valid_evals]
            comparison_data.append({
                'label': file_eval['label'] if file_eval['label'] else file_eval['filename'],
                'filename': file_eval['filename'],
                'total_segments': len(results),
                'evaluated_segments': len(valid_evals),
                'avg_score': statistics.mean(scores),
                'median_score': statistics.median(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0
            })
    
    # Comparison table
    if comparison_data:
        comp_rows = [['Method', 'Avg Score', 'Median', 'Min', 'Max', 'Std Dev', 'Segments']]
        
        # Sort by average score descending
        sorted_data = sorted(comparison_data, key=lambda x: x['avg_score'], reverse=True)
        
        for data in sorted_data:
            comp_rows.append([
                Paragraph(data['label'], small_style),
                f"{data['avg_score']:.1f}",
                f"{data['median_score']:.1f}",
                f"{data['min_score']:.0f}",
                f"{data['max_score']:.0f}",
                f"{data['std_dev']:.1f}",
                str(data['evaluated_segments'])
            ])
        
        comp_table = Table(comp_rows, colWidths=[6*cm, 2*cm, 2*cm, 1.5*cm, 1.5*cm, 2*cm, 2*cm])
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e3f2fd')]),
        ]))
        
        elements.append(comp_table)
        elements.append(Spacer(1, 1*cm))
        
        # Winner/recommendation
        best_method = sorted_data[0]
        worst_method = sorted_data[-1]
        improvement = best_method['avg_score'] - worst_method['avg_score']
        
        if improvement > 5:
            elements.append(Paragraph(f"<b>Recommendation:</b> '{best_method['label']}' performed significantly better (avg score: {best_method['avg_score']:.1f} vs {worst_method['avg_score']:.1f}), with a {improvement:.1f} point improvement.", normal_style))
        elif improvement > 2:
            elements.append(Paragraph(f"<b>Recommendation:</b> '{best_method['label']}' performed moderately better (avg score: {best_method['avg_score']:.1f} vs {worst_method['avg_score']:.1f}).", normal_style))
        else:
            elements.append(Paragraph(f"<b>Result:</b> Performance was similar across methods (difference: {improvement:.1f} points). Other factors may be more important.", normal_style))
    
    elements.append(PageBreak())
    
    # COMPARATIVE GRAPHS
    elements.append(Paragraph("Score Distribution Comparison", heading2_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Create comparison bar chart
    comparison_chart_path = output_file.parent / f"{output_file.stem}_comparison.png"
    _create_comparison_chart(comparison_data, comparison_chart_path)
    if comparison_chart_path.exists():
        elements.append(Image(str(comparison_chart_path), width=15*cm, height=10*cm))
        elements.append(Spacer(1, 0.5*cm))
    
    # Quality dimensions radar comparison
    elements.append(Paragraph("Quality Dimensions Comparison", heading2_style))
    elements.append(Spacer(1, 0.5*cm))
    
    radar_comparison_path = output_file.parent / f"{output_file.stem}_radar_comparison.png"
    _create_radar_comparison(file_evaluations, radar_comparison_path)
    if radar_comparison_path.exists():
        elements.append(Image(str(radar_comparison_path), width=15*cm, height=12*cm))
    
    elements.append(PageBreak())
    
    # INDIVIDUAL FILE DETAILS
    attention_threshold = config.get('attention_threshold', 70)
    
    for file_idx, file_eval in enumerate(file_evaluations):
        label = file_eval['label'] if file_eval['label'] else file_eval['filename']
        results = file_eval['results']
        metadata = file_eval['metadata']
        
        elements.append(Paragraph(f"File {file_idx + 1}: {label}", heading2_style))
        elements.append(Paragraph(f"<i>Filename: {file_eval['filename']}</i>", small_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Statistics
        valid_evals = [e for e in results if e.get('overall_score') is not None]
        
        if valid_evals:
            scores = [e['overall_score'] for e in valid_evals]
            avg_score = statistics.mean(scores)
            
            stat_rows = [
                ['Total Segments', str(len(results))],
                ['Successfully Evaluated', str(len(valid_evals))],
                ['Average Score', f"{avg_score:.1f}/100"],
                ['Median Score', f"{statistics.median(scores):.1f}/100"],
            ]
            
            stat_table = Table(stat_rows, colWidths=[8*cm, 8*cm])
            stat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(stat_table)
            elements.append(Spacer(1, 0.5*cm))
            
            # Issue Distribution
            all_issues = []
            for eval in valid_evals:
                all_issues.extend(eval.get('issues', []))
            
            if all_issues:
                elements.append(Paragraph("Issue Distribution", ParagraphStyle(
                    'SubHeading', parent=normal_style, fontName=font_bold, fontSize=12, spaceAfter=0.2*cm
                )))
                
                issue_type_counter = Counter(issue['type'] for issue in all_issues)
                issue_data = [['Issue Type', 'Count', 'Percentage']]
                total_issues = len(all_issues)
                
                for issue_type, count in issue_type_counter.most_common(5):
                    pct = count / total_issues * 100
                    issue_data.append([
                        issue_type.replace('_', ' ').title(),
                        str(count),
                        f"{pct:.1f}%"
                    ])
                
                issue_table = Table(issue_data, colWidths=[8*cm, 4*cm, 4*cm])
                issue_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff6f00')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), font_bold),
                    ('FONTNAME', (0, 1), (-1, -1), font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ]))
                
                elements.append(issue_table)
                elements.append(Spacer(1, 0.5*cm))
            
            # Score distribution chart for this file
            score_chart_path = output_file.parent / f"{output_file.stem}_file{file_idx}_scores.png"
            _create_score_distribution_chart(scores, score_chart_path, avg_score)
            if score_chart_path.exists():
                elements.append(Paragraph("Score Distribution", ParagraphStyle(
                    'SubHeading', parent=normal_style, fontName=font_bold, fontSize=12, spaceAfter=0.2*cm
                )))
                elements.append(Image(str(score_chart_path), width=15*cm, height=9*cm))
                elements.append(Spacer(1, 0.5*cm))
            
            # Quality dimensions radar
            dimensions = ['accuracy', 'fluency', 'style', 'context_coherence']
            dim_scores = {dim: [] for dim in dimensions}
            
            for eval in valid_evals:
                dims = eval.get('dimensions', {})
                for dim in dimensions:
                    if dim in dims and dims[dim] is not None:
                        dim_scores[dim].append(dims[dim])
            
            dim_avg = {dim: statistics.mean(scores) if scores else 0 for dim, scores in dim_scores.items()}
            
            radar_path = output_file.parent / f"{output_file.stem}_file{file_idx}_radar.png"
            _create_dimension_radar_chart(dim_avg, radar_path)
            if radar_path.exists():
                elements.append(Paragraph("Quality Dimensions", ParagraphStyle(
                    'SubHeading', parent=normal_style, fontName=font_bold, fontSize=12, spaceAfter=0.2*cm
                )))
                elements.append(Image(str(radar_path), width=12*cm, height=12*cm))
                elements.append(Spacer(1, 0.5*cm))
            
            # Segments requiring attention WITH FULL EXPLANATIONS
            critical_segs = [e for e in valid_evals if e.get('overall_score', 100) < attention_threshold]
            
            if critical_segs:
                elements.append(Paragraph(f"Segments Requiring Attention ({len(critical_segs)})", ParagraphStyle(
                    'SubHeading', parent=normal_style, fontName=font_bold, fontSize=12, spaceAfter=0.2*cm
                )))
                
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
                elements.append(Spacer(1, 0.5*cm))
            
            # Excellent quality samples
            excellent_segs = [e for e in valid_evals if e.get('overall_score', 0) >= 95]
            
            if excellent_segs:
                elements.append(Paragraph(f"Excellent Quality Samples ({len(excellent_segs)} segments)", ParagraphStyle(
                    'SubHeading', parent=normal_style, fontName=font_bold, fontSize=12, spaceAfter=0.2*cm
                )))
                
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
        
        if file_idx < len(file_evaluations) - 1:
            elements.append(PageBreak())
    
    # Build PDF
    doc.build(elements)


def _create_comparison_chart(comparison_data: list, output_path: Path):
    """Create bar chart comparing average scores across files."""
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        labels = [d['label'][:30] for d in comparison_data]  # Truncate long labels
        scores = [d['avg_score'] for d in comparison_data]
        
        colors_list = ['#4caf50' if s >= 90 else '#ffc107' if s >= 70 else '#f44336' for s in scores]
        
        bars = ax.barh(labels, scores, color=colors_list)
        
        # Add score labels on bars
        for i, (bar, score) in enumerate(zip(bars, scores)):
            ax.text(score + 1, i, f'{score:.1f}', va='center', fontsize=10, fontweight='bold')
        
        ax.set_xlabel('Average Score', fontsize=12, fontweight='bold')
        ax.set_title('Translation Method Comparison', fontsize=14, fontweight='bold')
        ax.set_xlim(0, 105)
        ax.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f"Could not create comparison chart: {e}")


def _create_radar_comparison(file_evaluations: list, output_path: Path):
    """Create radar chart comparing quality dimensions across files."""
    try:
        dimensions = ['Accuracy', 'Fluency', 'Style', 'Context\nCoherence']
        dim_keys = ['accuracy', 'fluency', 'style', 'context_coherence']
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle
        
        for file_eval in file_evaluations:
            results = file_eval['results']
            valid_evals = [e for e in results if e.get('overall_score') is not None]
            
            dim_scores = {dim: [] for dim in dim_keys}
            for eval in valid_evals:
                dims = eval.get('dimensions', {})
                for dim in dim_keys:
                    if dim in dims and dims[dim] is not None:
                        dim_scores[dim].append(dims[dim])
            
            dim_avg = [statistics.mean(dim_scores[dim]) if dim_scores[dim] else 0 for dim in dim_keys]
            dim_avg += dim_avg[:1]  # Complete the circle
            
            label = file_eval['label'] if file_eval['label'] else file_eval['filename']
            ax.plot(angles, dim_avg, 'o-', linewidth=2, label=label[:30])
            ax.fill(angles, dim_avg, alpha=0.15)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dimensions, fontsize=11)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.grid(True, alpha=0.3)
        ax.set_title('Quality Dimensions Comparison', fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f"Could not create radar comparison: {e}")


def _create_score_distribution_chart(scores: list, output_path: Path, avg_score: float):
    """Create histogram of score distribution."""
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        bins = [0, 20, 40, 60, 80, 100]
        counts, bin_edges, patches = ax.hist(scores, bins=bins, edgecolor='black', alpha=0.7)
        
        # Color bars based on quality
        colors_map = ['#f44336', '#ff9800', '#ffc107', '#8bc34a', '#4caf50']
        for i, patch in enumerate(patches):
            patch.set_facecolor(colors_map[i])
        
        # Add percentage labels
        total = len(scores)
        for i, count in enumerate(counts):
            if count > 0:
                pct = count / total * 100
                height = count
                ax.text((bin_edges[i] + bin_edges[i+1])/2, height, f'{pct:.1f}%',
                       ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax.axvline(avg_score, color='blue', linestyle='--', linewidth=2, label=f'Average: {avg_score:.1f}')
        ax.set_xlabel('Score Range', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Segments', fontsize=12, fontweight='bold')
        ax.set_title('Quality Score Distribution', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f"Could not create score distribution chart: {e}")


def _create_dimension_radar_chart(dimensions: dict, output_path: Path):
    """Create radar chart for quality dimensions."""
    try:
        labels = ['Accuracy', 'Fluency', 'Style', 'Context\nCoherence']
        values = [
            dimensions.get('accuracy', 0),
            dimensions.get('fluency', 0),
            dimensions.get('style', 0),
            dimensions.get('context_coherence', 0)
        ]
        
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        ax.plot(angles, values, 'o-', linewidth=2, color='#1976d2')
        ax.fill(angles, values, alpha=0.25, color='#1976d2')
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=11)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.grid(True, alpha=0.3)
        ax.set_title('Quality Dimensions', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f"Could not create radar chart: {e}")