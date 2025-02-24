import os
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_sdlxliff_file(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        namespaces = {
            'sdl': 'http://sdl.com/FileTypes/SdlXliff/1.0',
            '': 'urn:oasis:names:tc:xliff:document:1.2'
        }
        
        results = []
        for trans_unit in root.findall('.//trans-unit', namespaces):
            seg_mrk = trans_unit.find('.//seg-source/mrk[@mtype="seg"]', namespaces)
            segment_id = seg_mrk.get('mid') if seg_mrk is not None else "Not found"
            
            source_elem = trans_unit.find('source', namespaces)
            source_text = source_elem.text if source_elem is not None else "Not found"
            
            merge_status_elem = trans_unit.find(
                './/sdl:seg-defs/sdl:seg/sdl:value[@key="MergeStatus"]', 
                namespaces
            )
            merge_type = merge_status_elem.text if merge_status_elem is not None else None
            
            if merge_type in ["MergedParagraph", "MergedSegment"]:
                results.append({
                    'segment_id': segment_id,
                    'source_text': source_text,
                    'merge_type': merge_type,
                    'filename': file_path.name  # Add filename from the path
                })
        
        return results
        
    except ET.ParseError:
        return []
    except Exception:
        return []

def process_sdlxliff_folder():
    folder_path = input("Please enter the folder path containing sdlxliff files: ")
    
    if not os.path.isdir(folder_path):
        return
    
    sdlxliff_files = list(Path(folder_path).glob('*.sdlxliff'))
    
    for file_path in sdlxliff_files:
        results = parse_sdlxliff_file(file_path)
        
        for result in results:
            print(f"File: {result['filename']}")
            print(f"Segment #{result['segment_id']}:")
            print(f"Source: {result['source_text']}")
            print(f"Merge Type: {result['merge_type']}")
            print("-" * 50)

def main():
    try:
        process_sdlxliff_folder()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()