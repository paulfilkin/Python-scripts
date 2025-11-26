"""
Target language populator for XLIFF 2.0 files.
Reads XLIFF and TXT translation files, populates <target> elements.
"""

from lxml import etree
from typing import List, Tuple
from pathlib import Path


class TargetPopulator:
    """Populate target elements in XLIFF 2.0 files from text translations"""
    
    XLIFF_NS = "urn:oasis:names:tc:xliff:document:2.0"
    
    def parse_translation_file(self, content: str) -> List[str]:
        """
        Parse translation text file into list of translations.
        
        Args:
            content: Text file content with one translation per line
            
        Returns:
            List of translation strings
        """
        translations = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line:  # Skip empty lines
                translations.append(line)
        
        return translations
    
    def get_xliff_segment_count(self, xliff_content: str) -> int:
        """
        Count segments in XLIFF file.
        
        Args:
            xliff_content: XLIFF XML content
            
        Returns:
            Number of segments
        """
        try:
            root = etree.fromstring(xliff_content.encode('utf-8'))
            segments = root.xpath('//ns:segment', namespaces={'ns': self.XLIFF_NS})
            return len(segments)
        except Exception as e:
            raise ValueError(f"Error parsing XLIFF: {str(e)}")
    
    def populate_targets(
        self,
        xliff_content: str,
        translations: List[str],
        target_lang: str = None
    ) -> Tuple[str, int]:
        """
        Populate target elements in XLIFF with translations.
        
        Args:
            xliff_content: Original XLIFF XML content
            translations: List of translation strings
            target_lang: Optional target language code to set (MS LCID format)
            
        Returns:
            Tuple of (modified XLIFF content, number of targets added)
        """
        try:
            # Parse XLIFF
            root = etree.fromstring(xliff_content.encode('utf-8'))
            
            # Update target language if provided
            if target_lang:
                root.set('trgLang', target_lang)
            
            # Find all segments
            segments = root.xpath('//ns:segment', namespaces={'ns': self.XLIFF_NS})
            
            # Validate counts
            if len(segments) != len(translations):
                raise ValueError(
                    f"Segment count mismatch: XLIFF has {len(segments)} segments, "
                    f"translation file has {len(translations)} lines"
                )
            
            # Add target elements
            targets_added = 0
            
            for segment, translation in zip(segments, translations):
                # Check if target already exists
                existing_target = segment.find('{' + self.XLIFF_NS + '}target')
                
                if existing_target is not None:
                    # Update existing target
                    existing_target.text = translation
                else:
                    # Create new target element
                    target = etree.SubElement(segment, 'target')
                    target.text = translation
                
                targets_added += 1
            
            # Generate pretty XML
            xml_str = etree.tostring(
                root,
                pretty_print=True,
                xml_declaration=True,
                encoding='utf-8'
            ).decode('utf-8')
            
            return xml_str, targets_added
            
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Invalid XLIFF XML: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error populating targets: {str(e)}")
    
    def validate_xliff_structure(self, xliff_content: str) -> Tuple[bool, str]:
        """
        Validate basic XLIFF structure.
        
        Args:
            xliff_content: XLIFF XML content
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            root = etree.fromstring(xliff_content.encode('utf-8'))
            
            # Check if it's XLIFF 2.0
            if root.tag != '{' + self.XLIFF_NS + '}xliff':
                return False, "Not a valid XLIFF 2.0 file (wrong root element)"
            
            version = root.get('version')
            if version != '2.0':
                return False, f"Unsupported XLIFF version: {version} (expected 2.0)"
            
            # Check for segments
            segments = root.xpath('//ns:segment', namespaces={'ns': self.XLIFF_NS})
            if not segments:
                return False, "No segments found in XLIFF file"
            
            return True, ""
            
        except etree.XMLSyntaxError as e:
            return False, f"Invalid XML: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_xliff_info(self, xliff_content: str) -> dict:
        """
        Extract information from XLIFF file.
        
        Args:
            xliff_content: XLIFF XML content
            
        Returns:
            Dictionary with XLIFF information
        """
        try:
            root = etree.fromstring(xliff_content.encode('utf-8'))
            
            segments = root.xpath('//ns:segment', namespaces={'ns': self.XLIFF_NS})
            
            # Check for existing targets
            segments_with_targets = len([
                s for s in segments 
                if s.find('{' + self.XLIFF_NS + '}target') is not None
            ])
            
            return {
                'version': root.get('version'),
                'source_lang': root.get('srcLang'),
                'target_lang': root.get('trgLang'),
                'total_segments': len(segments),
                'segments_with_targets': segments_with_targets,
                'segments_without_targets': len(segments) - segments_with_targets
            }
            
        except Exception as e:
            return {'error': str(e)}