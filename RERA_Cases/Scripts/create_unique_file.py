import os
import json
from datetime import datetime, timedelta
# from compare import compare_files  # Import the function

def get_first_day_previous_month():
    # today = datetime.now()
    # first_day_current_month = today.replace(day=1)
    # last_day_previous_month = first_day_current_month - timedelta(days=1)
    # return last_day_previous_month.replace(day=1).strftime('%Y-%m-%d')
    return  "2025-03-04"

def get_first_day_current_month():
    date = "2025-06-30"
    return date
    #
    # return datetime.now().replace(day=1).strftime('%Y-%m-%d')

def load_json_lines(file_path):
    """Load JSON objects from a newline-separated JSON file."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip().rstrip(",")  # Remove trailing whitespace and comma
            if line:  # Skip empty lines
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Skipping invalid JSON line: {line.strip()}. Error: {e}")
    return data

def compare_files(current_file, previous_file, output_file):
    """
    Compare two files and write unique entries from the current file to the output file.

    Args:
        current_file (str): Path to the current day's data file.
        previous_file (str): Path to the previous month's data file.
        output_file (str): Path to save the unique entries.

    Returns:
        None
    """
    def load_json_lines(file_path):
        """Load JSON objects from a newline-separated JSON file."""
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().rstrip(",")  # Remove trailing whitespace and comma
                if line:  # Skip empty lines
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"Skipping invalid JSON line: {line.strip()}. Error: {e}")
        return data

    # Load data from files
    current_data = load_json_lines(current_file)
    previous_data = load_json_lines(previous_file)

    # Convert data to sets of serialized JSON strings for comparison
    current_set = set(json.dumps(entry) for entry in current_data)
    previous_set = set(json.dumps(entry) for entry in previous_data)

    # Find unique entries in the current file
    unique_entries = current_set - previous_set

    # Write unique entries to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in unique_entries:
            f.write(entry + '\n')

    print(f"Unique entries written to: {output_file}")
