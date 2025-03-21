from lxml import etree
import os
import shutil
from datetime import datetime
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:
    print("Error: 'reportlab' library is not installed. Please run 'pip install reportlab' and try again.")
    exit()

# Prompt the user for the full path to the SDLPROJ file
sdlproj_path = input("Please enter the full path to the SDLPROJ file (e.g., C:\\Users\\paul\\Projects\\project.sdlproj): ").strip()

# Validate the SDLPROJ file exists
if not os.path.isfile(sdlproj_path) or not sdlproj_path.lower().endswith(".sdlproj"):
    print(f"Error: '{sdlproj_path}' is not a valid SDLPROJ file or does not exist.")
    exit()

# Derive the project directory and target folder
project_dir = os.path.dirname(sdlproj_path)
target_folder = os.path.join(project_dir, "de-DE")

# Ensure the target folder exists
if not os.path.exists(target_folder):
    print(f"Target folder not found: {target_folder}")
    exit()

# Find all SDLXLIFF files in the de-DE folder
sdlxliff_files = [os.path.join(target_folder, f) for f in os.listdir(target_folder) if f.endswith(".sdlxliff")]

# Check if there are any SDLXLIFF files to process
if not sdlxliff_files:
    print(f"No SDLXLIFF files found in: {target_folder}")
    exit()

# Global list to store all removed comments
all_removed_comments = []

# Process each SDLXLIFF file in the target folder
for file_path in sdlxliff_files:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue
    
    # Create a backup by duplicating the original file
    backup_path = file_path + ".bak"
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        print(f"Backup created: {backup_path}")
    else:
        print(f"Backup already exists: {backup_path}")

    # Load and parse the SDLXLIFF file with lxml
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(file_path, parser)
    root = tree.getroot()

    # Debug: Print processing info
    print(f"Processing {file_path}")
    print(f"Root tag: {root.tag}")

    # Track modifications and comments removed
    modified = False
    comments_found = 0

    # Get comment definitions from <doc-info>
    cmt_defs = {}
    doc_info = root.xpath(".//*[local-name()='doc-info']")
    if doc_info:
        for cmt_def in doc_info[0].xpath(".//*[local-name()='cmt-def']"):
            cmt_id = cmt_def.get("id")
            comments = cmt_def.xpath(".//*[local-name()='Comment']")
            cmt_defs[cmt_id] = [(c.text, c.get("user")) for c in comments]

    # Remove <sdl:cmt> from <header>
    headers = root.xpath(".//*[local-name()='header']")
    for header in headers:
        cmt_xpath = ".//*[local-name()='cmt' and namespace-uri()='http://sdl.com/FileTypes/SdlXliff/1.0']"
        for cmt in header.xpath(cmt_xpath):
            comments_found += 1
            cmt_id = cmt.get("id")
            print(f"Found file-level comment in header: {etree.tostring(cmt, encoding='unicode')}")
            if cmt_id in cmt_defs:
                for comment_text, user in cmt_defs[cmt_id]:
                    all_removed_comments.append((os.path.basename(file_path), "N/A", comment_text, user))
            parent = cmt.getparent()
            parent.remove(cmt)
            modified = True

    # Remove <mrk mtype="x-sdl-comment"> from <target>
    targets = root.xpath(".//*[local-name()='target']")
    print(f"Found {len(targets)} <target> tags")
    for target in targets:
        mrk_xpath = ".//*[local-name()='mrk' and @mtype='x-sdl-comment']"
        for mrk in target.xpath(mrk_xpath):
            comments_found += 1
            cmt_id = mrk.get("{http://sdl.com/FileTypes/SdlXliff/1.0}cid")
            segment = target.xpath(".//*[local-name()='mrk' and @mtype='seg']")[0].get("mid") if target.xpath(".//*[local-name()='mrk' and @mtype='seg']") else "Unknown"
            comment_text = mrk.text or ""
            print(f"Found segment-level comment in target: {etree.tostring(mrk, encoding='unicode')}")
            user = "Unknown"
            if cmt_id in cmt_defs and cmt_defs[cmt_id]:
                user = cmt_defs[cmt_id][0][1]  # Take the first comment’s user if multiple
            all_removed_comments.append((os.path.basename(file_path), segment, comment_text, user))
            parent = mrk.getparent()
            if mrk.text:
                parent.text = (parent.text or '') + mrk.text
            parent.remove(mrk)
            modified = True

    # Report findings
    if comments_found > 0:
        print(f"Total comments removed from {file_path}: {comments_found}")
    else:
        print(f"No comments found in: {file_path}")

    # Save the modified content back to the original file if changes were made
    if modified:
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        print(f"Comments removed, original file updated: {file_path}")

# Generate PDF log if any comments were removed
if all_removed_comments:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_file = os.path.join(project_dir, f"comments_removed_log_{timestamp}.pdf")
    print(f"Attempting to generate PDF: {pdf_file}")
    try:
        doc = SimpleDocTemplate(pdf_file, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Table data: header + rows, with wrapped headers
        header_style = styles["Normal"]
        header_style.fontSize = 10
        header_style.leading = 12  # Line spacing for wrapping
        data = [
            [
                Paragraph("Filename", header_style),
                Paragraph("Segment Number", header_style),
                Paragraph("Comment", header_style),
                Paragraph("User", header_style)
            ]
        ] + [
            [filename, segment, Paragraph(comment, styles["Normal"]), user]
            for filename, segment, comment, user in all_removed_comments
        ]

        # Create table with styling
        table = Table(data, colWidths=[150, 80, 250, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        elements.append(table)

        # Build PDF
        doc.build(elements)
        print(f"All removed comments logged to: {pdf_file}")
        if os.path.exists(pdf_file):
            print(f"PDF file confirmed at: {os.path.abspath(pdf_file)}")
        else:
            print("PDF creation failed: File not found after generation.")
    except Exception as e:
        print(f"Error generating PDF: {e}")
else:
    print("No comments were removed from any files.")

print("Processing complete.")
print("To reinstate originals, rename the .bak files back to .sdlxliff (e.g., remove the .bak extension).")