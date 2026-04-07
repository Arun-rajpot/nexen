import json
import os
from datetime import datetime


def clean_line(line):
    """Helper function to clean the line and remove any trailing commas"""
    line = line.strip()
    if line.endswith(','):
        line = line[:-1]  # Remove trailing comma if any
    return line


def compare_datewise_files(previous_file, current_file, output_directory):
    try:
        # Directory to save unique data
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # Unique file path
        current_date = datetime.now().strftime('%Y-%m-%d')
        unique_file = os.path.join(output_directory, f"All_unique_{current_date}.txt")

        # Load previous data
        previous_data = set()
        if os.path.exists(previous_file):
            with open(previous_file, 'r', encoding='utf-8') as prev:
                previous_data = {json.dumps(json.loads(clean_line(line)), ensure_ascii=False) for line in prev}

        # Load current data
        current_data = set()
        if os.path.exists(current_file):
            with open(current_file, 'r', encoding='utf-8') as curr:
                current_data = {json.dumps(json.loads(clean_line(line)), ensure_ascii=False) for line in curr}

        # Find unique entries in current data
        unique_data = current_data - previous_data

        # Check if there is any unique data
        if unique_data:
            # Save unique entries to the file
            with open(unique_file, 'w', encoding='utf-8') as uniq:
                for entry in unique_data:
                    if entry:  # Ensure non-empty entries
                        uniq.write(entry)
                        uniq.write(',\n')
            print(f"Unique data saved to {unique_file}")
        else:
            print("No unique data found. File not created.")

    except Exception as e:
        print(f"Exception occurred while comparing files: {e}")