from lxml import etree
from pathlib import Path
import copy
import zipfile
import os
from datetime import datetime

def create_zip_backup(folder_path: Path) -> Path:
    """Create a ZIP backup of the entire folder and its subfolders."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = folder_path.parent / f"backup_{folder_path.name}_{timestamp}.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(folder_path.parent)
                zipf.write(file_path, arcname)
    
    return zip_filename

def process_xliff_file(file_path: Path) -> int:
    """Process a single XLIFF file, copying source to target and overwriting the original."""
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(str(file_path), parser)
    root = tree.getroot()

    nsmap = {
        'xlf': 'urn:oasis:names:tc:xliff:document:1.2',
        'ispring': 'http://ispringsolutions.com/custom-xliff'
    }

    count = 0

    for tu in root.xpath(".//xlf:trans-unit", namespaces=nsmap):
        source = tu.find("xlf:source", namespaces=nsmap)
        target = tu.find("xlf:target", namespaces=nsmap)

        if source is not None:
            # If target exists, clear its contents; if not, create a new one
            if target is not None:
                target.clear()
                target.set("state", "new")
            else:
                target = etree.Element("{urn:oasis:names:tc:xliff:document:1.2}target", attrib={"state": "new"})
                tu.append(target)

            # Deep copy all content from source to target
            target.text = source.text
            for child in source:
                target.append(copy.deepcopy(child))

            count += 1

    # Overwrite the original file
    tree.write(str(file_path), encoding="utf-8", xml_declaration=True, pretty_print=True)
    return count

def process_folder(folder_path: Path):
    """Process all XLIFF files in the folder and its subfolders."""
    folder_path = folder_path.resolve()
    
    # Create a backup before processing
    print(f"Creating backup of {folder_path}...")
    backup_file = create_zip_backup(folder_path)
    print(f"Backup created: {backup_file}")

    total_files = 0
    total_targets = 0

    # Recursively find and process all .xlf files
    for xliff_file in folder_path.rglob("*.xlf"):
        print(f"Processing {xliff_file}...")
        try:
            count = process_xliff_file(xliff_file)
            total_files += 1
            total_targets += count
            print(f"  {count} <target> elements processed in {xliff_file.name}")
        except Exception as e:
            print(f"  Error processing {xliff_file.name}: {str(e)}")

    print("\nSummary:")
    print(f"Processed {total_files} XLIFF files.")
    print(f"Updated {total_targets} <target> elements.")
    print(f"Backup saved to: {backup_file}")

if __name__ == "__main__":
    input_path = input("Enter path to the folder containing XLIFF (.xlf) files: ").strip()
    folder = Path(input_path)

    if not folder.exists() or not folder.is_dir():
        print("Invalid folder. Please provide a valid folder path.")
    else:
        process_folder(folder)