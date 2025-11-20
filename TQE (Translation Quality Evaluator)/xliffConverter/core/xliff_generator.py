"""
XLIFF 2.2 generator with candidate matches for approved translations.
Generates multilingual XLIFF files where non-source languages are stored as reference matches.
"""

from lxml import etree
from typing import List, Dict
from datetime import datetime
import uuid


class XLIFFGenerator:
    """Generate XLIFF 2.0 files with reference translations as metadata"""
    
    XLIFF_NS = "urn:oasis:names:tc:xliff:document:2.0"
    METADATA_NS = "urn:oasis:names:tc:xliff:metadata:2.0"
    
    NSMAP = {
        None: XLIFF_NS,
        'mda': METADATA_NS
    }
    
    def generate_xliff(
        self,
        groups: List[List[str]],
        languages: List[str],
        source_lang: str,
        target_lang: str,
        filename: str
    ) -> str:
        """
        Generate XLIFF 2.0 content.
        
        Args:
            groups: List of aligned text groups
            languages: List of language codes in order
            source_lang: Source language code
            target_lang: Target language code (primary target)
            filename: Original filename
            
        Returns:
            XLIFF 2.0 XML as string
        """
        # Find source language index
        try:
            source_idx = languages.index(source_lang)
        except ValueError:
            raise ValueError(f"Source language {source_lang} not found in language list")
        
        # Create root element
        root = etree.Element(
            'xliff',
            version='2.0',
            srcLang=source_lang,
            trgLang=target_lang,
            nsmap=self.NSMAP
        )
        
        # Create file element
        file_elem = etree.SubElement(root, 'file')
        file_elem.set('id', str(uuid.uuid4()))
        file_elem.set('original', filename)
        
        # Add skeleton (optional, but good practice)
        skeleton = etree.SubElement(file_elem, 'skeleton')
        skeleton.text = f"Original file: {filename}"
        
        # Process each group as a unit
        for group_idx, group in enumerate(groups, start=1):
            unit = self._create_unit(
                group=group,
                languages=languages,
                source_idx=source_idx,
                unit_id=group_idx
            )
            file_elem.append(unit)
        
        # Generate pretty XML
        xml_str = etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding='utf-8'
        ).decode('utf-8')
        
        return xml_str
    
    def _create_unit(
        self,
        group: List[str],
        languages: List[str],
        source_idx: int,
        unit_id: int
    ) -> etree.Element:
        """
        Create a single unit element with source and reference translations as metadata.
        
        Args:
            group: Aligned text lines
            languages: Language codes
            source_idx: Index of source language
            unit_id: Unit identifier
            
        Returns:
            Unit element
        """
        unit = etree.Element('unit')
        unit.set('id', str(unit_id))
        
        # Add reference translations as metadata (if there are other languages)
        if len(group) > 1:
            metadata = etree.SubElement(unit, '{' + self.METADATA_NS + '}metadata')
            meta_group = etree.SubElement(metadata, '{' + self.METADATA_NS + '}metaGroup')
            meta_group.set('category', 'reference-translations')
            
            for idx, (text, lang) in enumerate(zip(group, languages)):
                # Skip source language
                if idx == source_idx:
                    continue
                
                meta = etree.SubElement(meta_group, '{' + self.METADATA_NS + '}meta')
                meta.set('type', f'ref-{lang}')
                meta.text = text
        
        # Create segment
        segment = etree.SubElement(unit, 'segment')
        segment.set('id', str(unit_id))
        
        # Add source
        source = etree.SubElement(segment, 'source')
        source.text = group[source_idx]
        
        return unit
    
    def add_metadata_to_unit(
        self,
        unit: etree.Element,
        metadata: Dict[str, str]
    ) -> etree.Element:
        """
        Add custom metadata to a unit.
        
        Args:
            unit: Unit element
            metadata: Dictionary of metadata key-value pairs
            
        Returns:
            Modified unit element
        """
        # Find or create metadata element
        metadata_elem = unit.find('{' + self.XLIFF_NS + '}metadata')
        if metadata_elem is None:
            metadata_elem = etree.SubElement(unit, '{' + self.XLIFF_NS + '}metadata')
        
        # Create custom meta group
        meta_group = etree.SubElement(metadata_elem, 'metaGroup')
        meta_group.set('category', 'custom')
        
        for key, value in metadata.items():
            meta = etree.SubElement(meta_group, 'meta')
            meta.set('type', key)
            meta.text = str(value)
        
        return unit