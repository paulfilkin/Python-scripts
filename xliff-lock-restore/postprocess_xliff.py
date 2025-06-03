import os
from pathlib import Path
from lxml import etree

def postprocess_xliff(file_path):
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(str(file_path), parser)
    root = tree.getroot()

    modified = False

    for unit in root.xpath('//trans-unit'):
        for tag in ['source', 'target']:
            seg = unit.find(tag)
            if seg is not None:
                for mrk in seg.findall('mrk'):
                    if mrk.attrib.get('mtype') == 'protected':
                        g = etree.Element("g", ctype=mrk.attrib.get('ctype', 'x-code'))
                        if 'id' in mrk.attrib:
                            g.attrib['id'] = mrk.attrib['id']
                        for attr in mrk.attrib:
                            if attr.endswith('page-content-title'):
                                g.attrib[attr] = mrk.attrib[attr]
                        g.text = mrk.text
                        mrk.getparent().replace(mrk, g)
                        modified = True

    if modified:
        tree.write(str(file_path), encoding='utf-8', xml_declaration=True, pretty_print=False)

def main():
    folder = input("Enter path to root folder containing translated XLIFF files: ").strip('"')
    root_path = Path(folder)
    if not root_path.is_dir():
        print("Invalid folder path.")
        return

    for ext in ('*.xliff', '*.xlf'):
        for file_path in root_path.rglob(ext):
            print(f"Postprocessing: {file_path}")
            postprocess_xliff(file_path)

    print("Postprocessing completed.")

if __name__ == "__main__":
    main()
