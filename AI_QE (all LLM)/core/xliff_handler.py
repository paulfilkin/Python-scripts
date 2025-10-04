"""
XLIFF/SDLXLIFF file handling for Really Smart Review.
Parses segments with context and injects structured comments.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime


class XLIFFHandler:
    """Handle XLIFF file parsing and comment injection."""
    
    NAMESPACES = {
        'xliff': 'urn:oasis:names:tc:xliff:document:1.2',
        'sdl': 'http://sdl.com/FileTypes/SdlXliff/1.0'
    }
    
    @staticmethod
    def register_namespaces():
        """Register namespaces to preserve them in output."""
        for prefix, uri in XLIFFHandler.NAMESPACES.items():
            ET.register_namespace(prefix, uri)
    
    @staticmethod
    def parse_file(xliff_path: Path) -> Dict[str, Any]:
        """
        Parse SDLXLIFF file and extract segments with metadata.
        
        Returns:
            Dictionary containing segments, metadata, and file tree
        """
        XLIFFHandler.register_namespaces()
        
        tree = ET.parse(xliff_path)
        root = tree.getroot()
        
        # Extract file metadata
        file_elem = root.find('.//xliff:file', XLIFFHandler.NAMESPACES)
        if file_elem is not None:
            source_lang = file_elem.get('source-language', 'unknown')
            target_lang = file_elem.get('target-language', 'unknown')
            original = file_elem.get('original', xliff_path.name)
        else:
            source_lang = target_lang = 'unknown'
            original = xliff_path.name
        
        metadata = {
            'source_language': source_lang,
            'target_language': target_lang,
            'original': Path(original).name,
            'file_path': str(xliff_path)
        }
        
        # Extract all segments
        segments = []
        trans_units = root.findall('.//xliff:trans-unit', XLIFFHandler.NAMESPACES)
        
        for trans_unit in trans_units:
            # Skip non-translatable units
            if trans_unit.get('translate') == 'no':
                continue
            
            seg_source = trans_unit.find('xliff:seg-source', XLIFFHandler.NAMESPACES)
            target = trans_unit.find('xliff:target', XLIFFHandler.NAMESPACES)
            
            if seg_source is None or target is None:
                continue
            
            # Extract text from mrk elements
            source_mrk = seg_source.find('.//xliff:mrk', XLIFFHandler.NAMESPACES)
            target_mrk = target.find('.//xliff:mrk', XLIFFHandler.NAMESPACES)
            
            if source_mrk is None or target_mrk is None:
                continue
            
            source_text = XLIFFHandler._extract_text(source_mrk)
            target_text = XLIFFHandler._extract_text(target_mrk)
            seg_id = source_mrk.get('mid', '') or trans_unit.get('id', '')
            
            if not source_text or not target_text:
                continue
            
            segments.append({
                'id': seg_id,
                'source': source_text,
                'target': target_text,
                'trans_unit': trans_unit
            })
        
        return {
            'segments': segments,
            'metadata': metadata,
            'tree': tree,
            'root': root
        }
    
    @staticmethod
    def _extract_text(element) -> str:
        """Extract all text content from element including nested tags."""
        if element is None:
            return ''
        return ''.join(element.itertext())
    
    @staticmethod
    def create_comment(evaluation: Dict[str, Any], config: Dict[str, Any]) -> str:
        """
        Create structured comment from evaluation result.
        
        Format follows the spec for filterability in Trados.
        """
        comment_parts = []
        fmt = config['comment_generation']['format']
        
        # QE Score
        if fmt['include_score']:
            score = evaluation.get('overall_score', 0)
            comment_parts.append(f"QE Score: {score}")
        
        # QE Band (score range)
        if fmt['include_band']:
            score = evaluation.get('overall_score', 0)
            band_start = (score // 10) * 10
            band_end = band_start + 10
            comment_parts.append(f"QE Band: {band_start}-{band_end}")
        
        # Issue categories
        if fmt['include_categories'] and evaluation.get('issues'):
            categories = list(set([i['type'] for i in evaluation['issues']]))
            if categories:
                comment_parts.append(f"QE Category: {', '.join(categories)}")
        
        # Severity
        if fmt['include_severity'] and evaluation.get('issues'):
            severities = [i['severity'] for i in evaluation['issues']]
            max_severity = max(severities, default='minor')
            comment_parts.append(f"QE Severity: {max_severity.title()}")
        
        # Dimension scores
        if fmt['include_dimensions'] and evaluation.get('dimensions'):
            dims = evaluation['dimensions']
            dim_str = "|".join([f"{k.title()}:{v}" for k, v in dims.items()])
            comment_parts.append(f"QE Dimensions: {dim_str}")
        
        # Confidence
        if fmt['include_confidence']:
            confidence = evaluation.get('confidence', 100)
            comment_parts.append(f"QE Confidence: {confidence}%")
        
        # Context info
        context_note = evaluation.get('context_note', 'segment-only')
        comment_parts.append(f"QE Context: {context_note}")
        
        # Model info
        model = evaluation.get('model', 'unknown')
        comment_parts.append(f"QE Model: {model}")
        
        # Natural language explanation
        if fmt['include_explanation'] and evaluation.get('explanation'):
            comment_parts.append(f"QE Comment: {evaluation['explanation']}")
        
        return "\n".join(comment_parts)
    
    @staticmethod
    def inject_comments_to_xliff(tree, root, evaluations):
        """
        Inject all comments into XLIFF tree.
        Returns modified tree ready to save.
        """
        ns = XLIFFHandler.NAMESPACES
        
        # Find or create doc-info element
        doc_info = root.find('.//sdl:doc-info', ns)
        
        if doc_info is None:
            # Create doc-info as first child of root
            doc_info = ET.Element('{http://sdl.com/FileTypes/SdlXliff/1.0}doc-info')
            root.insert(0, doc_info)
        
        # Get or create cmt-defs
        cmt_defs = doc_info.find('sdl:cmt-defs', ns)
        if cmt_defs is None:
            cmt_defs = ET.SubElement(doc_info, '{http://sdl.com/FileTypes/SdlXliff/1.0}cmt-defs')
        
        # Build a mapping of segment_id -> comment_id first
        comment_map = {}
        
        for evaluation in evaluations:
            if not evaluation.get('comment'):
                continue
            
            segment_id = evaluation['segment_id']
            comment_id = str(uuid.uuid4())
            comment_map[segment_id] = comment_id
            
            # Create cmt-def
            cmt_def = ET.SubElement(cmt_defs, '{http://sdl.com/FileTypes/SdlXliff/1.0}cmt-def', id=comment_id)
            comments = ET.SubElement(cmt_def, 'Comments')
            
            severity = evaluation.get('trados_severity', 'Low')
            
            comment = ET.SubElement(comments, 'Comment',
                                severity=severity,
                                user="smart-review",
                                date=datetime.now().isoformat(),
                                version="1.0")
            comment.text = evaluation['comment']
        
        # Now link comments to their segments
        trans_units = root.findall('.//xliff:trans-unit', ns)
        
        for trans_unit in trans_units:
            target = trans_unit.find('xliff:target', ns)
            if target is None:
                continue
            
            # Find all mrk elements with mtype="seg" at this level
            for target_mrk in target.findall('xliff:mrk[@mtype="seg"]', ns):
                seg_id = target_mrk.get('mid')
                
                # Check if this segment has a comment
                if seg_id in comment_map:
                    comment_id = comment_map[seg_id]
                    
                    # Check if already wrapped (avoid double-wrapping)
                    existing_comment = target_mrk.find('xliff:mrk[@mtype="x-sdl-comment"]', ns)
                    if existing_comment is not None:
                        continue
                    
                    # Create comment wrapper
                    comment_mrk = ET.Element('{urn:oasis:names:tc:xliff:document:1.2}mrk',
                                        mtype='x-sdl-comment')
                    comment_mrk.set('{http://sdl.com/FileTypes/SdlXliff/1.0}cid', comment_id)
                    
                    # Move all children and text to comment wrapper
                    comment_mrk.text = target_mrk.text
                    target_mrk.text = None
                    
                    for child in list(target_mrk):
                        target_mrk.remove(child)
                        comment_mrk.append(child)
                    
                    # Add comment wrapper as only child of target_mrk
                    target_mrk.append(comment_mrk)
        
        return tree
    
    @staticmethod
    def save_annotated_xliff(input_path: Path, output_path: Path, 
                            evaluations: List[Dict[str, Any]]):
        """
        Save XLIFF file with injected comments.
        
        Args:
            input_path: Original XLIFF file
            output_path: Where to save annotated file
            evaluations: List of segment evaluations with comments
        """
        # Parse original file
        data = XLIFFHandler.parse_file(input_path)
        
        # Inject all comments
        tree = XLIFFHandler.inject_comments_to_xliff(
            data['tree'], 
            data['root'], 
            evaluations
        )
        
        # Save modified tree
        tree.write(str(output_path), encoding='utf-8', xml_declaration=True)