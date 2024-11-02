import re
import os

def generate_toc(md_file):
    if not os.path.isfile(md_file):
        print(f"File '{md_file}' not found. Please check the file path.")
        return

    with open(md_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    toc_lines = []
    content_lines = []
    for line in lines:
        header_match = re.match(r'^(#{1,6}) (.+)', line)
        if header_match:
            level = len(header_match.group(1))  # Number of # symbols
            title = header_match.group(2)
            # Generate anchor link by converting to lowercase, replacing spaces with hyphens, and removing punctuation
            anchor = re.sub(r'[^\w\s-]', '', title).replace(' ', '-').lower()
            toc_lines.append(f"{'  ' * (level - 1)}- [{title}](#{anchor})")
            # Optionally adjust the header to include an explicit ID if needed
            line = f"{header_match.group(1)} {title} {{#{anchor}}}\n"
        content_lines.append(line)

    # Write the TOC and original content back to the same file, without '[TOC]'
    with open(md_file, 'w', encoding='utf-8') as file:
        file.write("## Table of Contents\n\n" + "\n".join(toc_lines) + "\n\n" + "".join(content_lines))

    print(f"Table of contents added to '{md_file}'.")

# Run the function with your Markdown file
generate_toc('input.md')
