"""
XLIFF 2.0 file handling for multilingual translation QE.
Parses segments with reference translations from metadata.
"""

from lxml import etree
from pathlib import Path
from typing import List, Dict, Any, Optional


class XLIFF2Handler:
    """Handle XLIFF 2.0 file parsing and target injection."""
    
    NAMESPACES = {
        'xliff': 'urn:oasis:names:tc:xliff:document:2.0',
        'mda': 'urn:oasis:names:tc:xliff:metadata:2.0'
    }
    
    @staticmethod
    def parse_file(xliff_path: Path) -> Dict[str, Any]:
        """
        Parse XLIFF 2.0 file and extract segments with metadata.
        
        Returns:
            Dictionary containing:
            - segments: List of segment dicts with source, target (if present), references
            - metadata: File-level metadata (languages, etc.)
            - tree: Parsed XML tree for modification
            - root: Root element
        """
        parser = etree.XMLParser(remove_blank_text=False, strip_cdata=False)
        tree = etree.parse(str(xliff_path), parser)
        root = tree.getroot()
        
        # Extract language information
        source_lang = root.get('srcLang', 'unknown')
        target_lang = root.get('trgLang', 'unknown')
        
        # Get file element
        file_elem = root.find('.//xliff:file', XLIFF2Handler.NAMESPACES)
        if file_elem is not None:
            original = file_elem.get('original', xliff_path.name)
        else:
            original = xliff_path.name
        
        metadata = {
            'source_language': source_lang,
            'target_language': target_lang,
            'original': Path(original).name,
            'file_path': str(xliff_path)
        }
        
        # Extract all segments
        segments = []
        units = root.findall('.//xliff:unit', XLIFF2Handler.NAMESPACES)
        
        for unit in units:
            unit_id = unit.get('id', '')
            
            # Get segment
            segment_elem = unit.find('.//xliff:segment', XLIFF2Handler.NAMESPACES)
            if segment_elem is None:
                continue
            
            seg_id = segment_elem.get('id', unit_id)
            
            # Extract source
            source_elem = segment_elem.find('xliff:source', XLIFF2Handler.NAMESPACES)
            if source_elem is None:
                continue
            source_text = XLIFF2Handler._extract_text(source_elem)
            
            # Extract target (if present)
            target_elem = segment_elem.find('xliff:target', XLIFF2Handler.NAMESPACES)
            target_text = XLIFF2Handler._extract_text(target_elem) if target_elem is not None else None
            
            # Extract reference translations from metadata
            references = {}
            metadata_elem = unit.find('.//mda:metadata', XLIFF2Handler.NAMESPACES)
            if metadata_elem is not None:
                # Look for reference-translations metaGroup
                for metaGroup in metadata_elem.findall('.//mda:metaGroup', XLIFF2Handler.NAMESPACES):
                    if metaGroup.get('category') == 'reference-translations':
                        # Extract all ref-* meta elements
                        for meta in metaGroup.findall('mda:meta', XLIFF2Handler.NAMESPACES):
                            meta_type = meta.get('type', '')
                            if meta_type.startswith('ref-'):
                                # Extract language code (e.g., 'ref-de-DE' -> 'de-DE')
                                lang_code = meta_type[4:]  # Remove 'ref-' prefix
                                references[lang_code] = meta.text or ''
            
            segments.append({
                'id': seg_id,
                'unit_id': unit_id,
                'source': source_text,
                'target': target_text,
                'references': references,
                'unit_elem': unit,
                'segment_elem': segment_elem
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
    def inject_targets(tree, root, translations: List[Dict[str, str]]):
        """
        Inject translated target elements into XLIFF segments.
        
        Args:
            tree: Parsed XML tree
            root: Root element
            translations: List of dicts with 'segment_id' and 'translation' keys
        """
        ns = XLIFF2Handler.NAMESPACES
        
        # Build translation lookup
        trans_lookup = {t['segment_id']: t['translation'] for t in translations}
        
        # Find all units
        units = root.findall('.//xliff:unit', ns)
        
        for unit in units:
            segment = unit.find('.//xliff:segment', ns)
            if segment is None:
                continue
            
            seg_id = segment.get('id', unit.get('id', ''))
            
            # Check if we have a translation for this segment
            if seg_id in trans_lookup:
                translation = trans_lookup[seg_id]
                
                # Check if target already exists
                target = segment.find('xliff:target', ns)
                if target is not None:
                    # Update existing target
                    target.text = translation
                else:
                    # Create new target element
                    target = etree.Element(
                        '{urn:oasis:names:tc:xliff:document:2.0}target'
                    )
                    target.text = translation
                    
                    # Insert after source
                    source = segment.find('xliff:source', ns)
                    if source is not None:
                        source_index = list(segment).index(source)
                        segment.insert(source_index + 1, target)
                    else:
                        segment.append(target)
        
        return tree
    
    @staticmethod
    def save_xliff(tree, output_path: Path):
        """
        Save XLIFF file with proper namespace preservation.
        
        Args:
            tree: XML tree to save
            output_path: Where to save the file
        """
        tree.write(
            str(output_path),
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True
        )