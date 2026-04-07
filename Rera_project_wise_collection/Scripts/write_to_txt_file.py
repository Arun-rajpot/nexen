import os
from datetime import datetime
import json

# Global cache for timestamps per state
state_timestamps = {}

def write_to_MargeFile(newline, state_name):
    # Use same timestamp per state across whole run
    if state_name not in state_timestamps:
        state_timestamps[state_name] = datetime.now().strftime("%Y%m%d")

    timestamp = state_timestamps[state_name]

    folder_path = r"D:\New_Rera\New_rera_project\New_Data"
    file_path = fr"{folder_path}\New_Rera_{state_name}_{timestamp}.txt"

    os.makedirs(folder_path, exist_ok=True)

    with open(file_path, 'a', encoding='utf-8') as text_file:
        json_line = json.dumps(newline, ensure_ascii=False)
        text_file.write(json_line)
        text_file.write(",\n")