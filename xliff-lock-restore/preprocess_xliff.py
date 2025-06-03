import os
import shutil
from pathlib import Path
from lxml import etree

def create_backup(root_folder):
    root_path = Path(root_folder).resolve()
    backup_path = root_path.parent / f"{root_path.name}_Backup"
    backup_path.mkdir(parents=True, exist_ok=True)
    for ext in ('*.xliff', '*.xlf'):
        for file_path in root_path.rglob(ext):
            rel_path = file_path.relative_to(root_path)
            dest_path = backup_path / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest_path)
    return backup_path

def preprocess_xliff(file_path):
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(str(file_path), parser)
    root = tree.getroot()

    namespaces = root.nsmap
    modified = False

    for g in root.xpath('//g'):
        ctype = g.attrib.get('ctype')
        if ctype == 'x-code' or (ctype == 'x-vsn-link' and any(a for a in g.attrib if a.endswith('page-content-title'))):
            mrk = etree.Element("mrk", mtype="protected", ctype=ctype)
            if 'id' in g.attrib:
                mrk.attrib['id'] = g.attrib['id']
            for attr in g.attrib:
                if attr.endswith('page-content-title'):
                    mrk.attrib[attr] = g.attrib[attr]
            mrk.text = g.text
            g.getparent().replace(g, mrk)
            modified = True

    if modified:
        tree.write(str(file_path), encoding='utf-8', xml_declaration=True, pretty_print=False)

def main():
    folder = input("Enter path to root folder containing XLIFF files: ").strip('"')
    root_path = Path(folder)
    if not root_path.is_dir():
        print("Invalid folder path.")
        return

    backup_path = create_backup(root_path)
    print(f"Backup created at: {backup_path}")

    for ext in ('*.xliff', '*.xlf'):
        for file_path in root_path.rglob(ext):
            print(f"Preprocessing: {file_path}")
            preprocess_xliff(file_path)

    print("Preprocessing completed.")

if __name__ == "__main__":
    main()
