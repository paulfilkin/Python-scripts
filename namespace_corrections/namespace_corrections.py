import xml.etree.ElementTree as ET
import re
from collections import defaultdict

def find_missing_namespaces():
    # Prompt the user for the XML file path
    xml_file = input("Please enter the path to the XML settings file: ")

    try:
        # Load and parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Find all declared namespaces by manually filtering elements
        declared_namespaces = {}
        settings = root.findall(".//Setting")
        for elem in settings:
            if elem.get("Id") == "Xml_NS_List_0_NS_Prefix":
                ns_prefix = elem.text.strip() if elem.text else ""
                # Look for the sibling `Xml_NS_List_0_NS_Uri` by iterating within the same parent
                for sibling in elem.iterfind("../Setting"):
                    if sibling.get("Id") == "Xml_NS_List_0_NS_Uri":
                        declared_namespaces[ns_prefix] = sibling.text.strip() if sibling.text else ""

        # Check XPath selectors for missing namespace prefixes
        missing_namespaces = defaultdict(list)
        for elem in settings:
            if "XPathSelector" in elem.get("Id", ""):
                xpath_selector = elem.text or ""
                parser_rule = elem.get("Id")
                
                # Extract all prefixes in the XPath selector (e.g., `fct` in `fct:ExternalLink`)
                prefixes = set(re.findall(r'(\w+):\w+', xpath_selector))
                for prefix in prefixes:
                    if prefix not in declared_namespaces:
                        missing_namespaces[prefix].append(parser_rule)
        
        # Print results
        if missing_namespaces:
            print("Missing namespace declarations found:")
            for prefix in missing_namespaces:
                print(f"Prefix: {prefix}")
                print(f"Uri: [MISSING URI]")
        else:
            print("No missing namespace declarations found.")

    except FileNotFoundError:
        print(f"Error: File '{xml_file}' not found.")
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Run the function
find_missing_namespaces()
