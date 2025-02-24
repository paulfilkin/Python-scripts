import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog

# Function to select folder
def select_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select Folder Containing Excel Files")
    return folder_path

# Prompt for folder and target language label
folder_path = select_folder()
if not folder_path:
    print("No folder selected. Exiting.")
    exit()

target_label = input("Enter the target language label (e.g., fr-FR, de-DE): ").strip()

# Define the output structure
columns = {"en-US": "Source text", target_label: "Target text"}
merged_data = pd.DataFrame(columns=columns.keys())

# Process files in sequence
for i in range(1, 12):  # Files from Generated_01 to Generated_11
    file_prefix = f"Generated_{i:02}"
    
    # Find matching files
    matching_files = [f for f in os.listdir(folder_path) if f.startswith(file_prefix) and f.endswith(".xlsx")]
    
    if matching_files:
        file_path = os.path.join(folder_path, matching_files[0])  # Take the first match
        print(f"Processing: {file_path}")
        
        try:
            # Read the specific columns
            df = pd.read_excel(file_path, usecols=["Source text", "Target text"], header=0)
            df.columns = columns.keys()  # Rename columns
            merged_data = pd.concat([merged_data, df], ignore_index=True)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    else:
        print(f"No matching file found for prefix: {file_prefix}")

# Save merged file
output_file = os.path.join(folder_path, "Merged_Translations.xlsx")
merged_data.to_excel(output_file, index=False)
print(f"Merged file saved as: {output_file}")
