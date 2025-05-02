from lxml import etree
from pathlib import Path
import copy

def add_targets(input_file: Path):
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(str(input_file), parser)
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

    output_file = input_file.parent / f"t_{input_file.name}"
    tree.write(str(output_file), encoding="utf-8", xml_declaration=True, pretty_print=True)

    print(f"{count} <target> elements processed.")
    print(f"Output written to: {output_file}")

if __name__ == "__main__":
    input_path = input("Enter path to the XLIFF (.xlf) file: ").strip()
    source_file = Path(input_path)

    if not source_file.exists() or source_file.suffix.lower() != ".xlf":
        print("Invalid file. Please provide a valid .xlf path.")
    else:
        add_targets(source_file)