"""
XLIFF/SDLXLIFF file handling for Really Smart Review.
Parses segments with context and injects structured comments.
Uses lxml for proper namespace preservation.
"""

from lxml import etree
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime


class XLIFFHandler:
    """Handle XLIFF file parsing and comment injection with proper namespace preservation."""
    
    NAMESPACES = {
        'xliff': 'urn:oasis:names:tc:xliff:document:1.2',
        'sdl': 'http://sdl.com/FileTypes/SdlXliff/1.0'
    }
    
    @staticmethod
    def parse_file(xliff_path: Path) -> Dict[str, Any]:
        """
        Parse SDLXLIFF file and extract segments with metadata.
        
        Returns:
            Dictionary containing segments, metadata, and file tree
        """
        parser = etree.XMLParser(remove_blank_text=False, strip_cdata=False)
        tree = etree.parse(str(xliff_path), parser)
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
        
        # Get score (handle None)
        score = evaluation.get('overall_score')
        
        # QE Score
        if fmt['include_score']:
            if score is not None:
                comment_parts.append(f"QE Score: {score}")
            else:
                comment_parts.append(f"QE Score: Error")
        
        # QE Band (score range)
        if fmt['include_band']:
            if score is not None:
                band_start = (score // 10) * 10
                band_end = band_start + 10
                comment_parts.append(f"QE Band: {band_start}-{band_end}")
            else:
                comment_parts.append(f"QE Band: Error")
        
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
        
        # Build namespace map for XPath
        nsmap = {'xliff': ns['xliff'], 'sdl': ns['sdl']}
        
        # Find or create doc-info element
        doc_info = root.find('.//sdl:doc-info', nsmap)
        
        if doc_info is None:
            # Create doc-info as first child of root with proper namespace
            doc_info = etree.Element(
                '{http://sdl.com/FileTypes/SdlXliff/1.0}doc-info',
                nsmap={'sdl': ns['sdl']}
            )
            root.insert(0, doc_info)
        
        # Get or create cmt-defs
        cmt_defs = doc_info.find('sdl:cmt-defs', nsmap)
        if cmt_defs is None:
            cmt_defs = etree.SubElement(
                doc_info,
                '{http://sdl.com/FileTypes/SdlXliff/1.0}cmt-defs'
            )
        
        # Build a mapping of segment_id -> comment_id first
        comment_map = {}
        
        for evaluation in evaluations:
            if not evaluation.get('comment'):
                continue
            
            segment_id = evaluation['segment_id']
            comment_id = str(uuid.uuid4())
            comment_map[segment_id] = comment_id
            
            # Create cmt-def with proper namespace
            cmt_def = etree.SubElement(
                cmt_defs,
                '{http://sdl.com/FileTypes/SdlXliff/1.0}cmt-def',
                id=comment_id
            )
            
            # CRITICAL: Comments and Comment MUST be in null namespace
            # Force empty default namespace with nsmap
            comments = etree.Element('Comments', nsmap={None: ''})
            cmt_def.append(comments)
            
            severity = evaluation.get('trados_severity', 'Low')
            
            # Comment element also in null namespace
            comment = etree.Element(
                'Comment',
                severity=severity,
                user="smart-review",
                date=datetime.now().isoformat(),
                version="1.0"
            )
            comment.text = evaluation['comment']
            comments.append(comment)
        
        # Now link comments to their segments
        trans_units = root.findall('.//xliff:trans-unit', nsmap)
        
        for trans_unit in trans_units:
            target = trans_unit.find('xliff:target', nsmap)
            if target is None:
                continue
            
            # Find all mrk elements with mtype="seg" at this level
            for target_mrk in target.findall('xliff:mrk[@mtype="seg"]', nsmap):
                seg_id = target_mrk.get('mid')
                
                # Check if this segment has a comment
                if seg_id in comment_map:
                    comment_id = comment_map[seg_id]
                    
                    # Check if already wrapped (avoid double-wrapping)
                    existing_comment = target_mrk.find('xliff:mrk[@mtype="x-sdl-comment"]', nsmap)
                    if existing_comment is not None:
                        continue
                    
                    # Create comment wrapper with proper namespace
                    comment_mrk = etree.Element(
                        '{urn:oasis:names:tc:xliff:document:1.2}mrk',
                        mtype='x-sdl-comment'
                    )
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
                            evaluations: List[Dict[str, Any]],
                            parsed_tree=None, parsed_root=None):
        """
        Save XLIFF file with injected comments using lxml for proper namespace preservation.
        
        Args:
            input_path: Original XLIFF file (only used if tree not provided)
            output_path: Where to save annotated file
            evaluations: List of segment evaluations with comments
            parsed_tree: Pre-parsed tree (optional, avoids re-parsing)
            parsed_root: Pre-parsed root (optional, avoids re-parsing)
        """
        # Use pre-parsed tree if available, otherwise parse
        if parsed_tree is not None and parsed_root is not None:
            tree = parsed_tree
            root = parsed_root
        else:
            # Fallback: parse the file
            data = XLIFFHandler.parse_file(input_path)
            tree = data['tree']
            root = data['root']
        
        # Inject all comments
        tree = XLIFFHandler.inject_comments_to_xliff(
            tree, 
            root, 
            evaluations
        )
        
        # Save with lxml - this preserves namespaces perfectly
        tree.write(
            str(output_path),
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=False
        )
