# import json
# import os
# import shutil
# import datetime
#
#
#
# def compare_files(data_file, old_file, unique_file, log_file):
#     def log(message):
#         timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         with open(log_file, 'a', encoding='utf-8') as lf:
#             lf.write(f"[{timestamp}] {message}\n")
#
#     def load_json_lines(file_path):
#         data = []
#         if not os.path.exists(file_path):
#             log(f"⚠ File not found (treated as empty): {file_path}")
#             return data
#         with open(file_path, 'r', encoding='utf-8') as f:
#             for line in f:
#                 line = line.strip().rstrip(",")
#                 if line:
#                     try:
#                         data.append(json.loads(line))
#                     except json.JSONDecodeError as e:
#                         log(f"❌ Skipping invalid JSON in {file_path}: {line}. Error: {e}")
#         return data
#
#     def normalize(record):
#         # Create a string with sorted keys to ensure consistent comparison
#         return json.dumps(record, sort_keys=True)
#
#     try:
#         log(f"Started comparison: {data_file}")
#         new_data = load_json_lines(data_file)
#         old_data = load_json_lines(old_file)
#
#         # Normalize and compare
#         new_set = set(normalize(d) for d in new_data)
#         old_set = set(normalize(d) for d in old_data)
#
#         unique = new_set - old_set
#         unique_records = [json.loads(u) for u in unique]  # Convert back to dicts
#
#         if unique_records:
#             with open(unique_file, 'w', encoding='utf-8') as f:
#                 for entry in unique_records:
#                     f.write(json.dumps(entry, ensure_ascii=False) + ",\n")
#             log(f"✅ {len(unique_records)} unique records written: {unique_file}")
#         else:
#             log(f"⚠ No unique records found for {data_file}")
#
#     except Exception as e:
#         log(f"❌ ERROR comparing {data_file}: {e}")
#
#
# def create_unique():
#     base_dir = r"D:\RERA_Scheduler"
#     data_folder = os.path.join(base_dir, "New_Data")
#     old_folder = os.path.join(base_dir, "Old_Data")
#     unique_folder = os.path.join(base_dir, "Unique_data")
#     log_file = os.path.join(base_dir, "process_log.txt")
#
#     # Ensure folders exist
#     os.makedirs(old_folder, exist_ok=True)
#     os.makedirs(unique_folder, exist_ok=True)
#
#     for file in os.listdir(data_folder):
#         if file.endswith(".txt"):
#             data_file = os.path.join(data_folder, file)
#
#             # Extract state name and date
#             parts = file.split("_")
#             if len(parts) < 4:
#                 with open(log_file, 'a', encoding='utf-8') as lf:
#                     lf.write(f"[{datetime.datetime.now()}] ⚠ Invalid file name format skipped: {file}\n")
#                 continue
#
#             state_name = parts[2]
#             timestamp = parts[3].split('.')[0]
#
#             old_file = os.path.join(old_folder, f"Rera_cases_{state_name}.txt")
#             unique_file = os.path.join(unique_folder, f"Unique_{state_name}_{timestamp}.txt")
#
#             # Compare files
#             compare_files(data_file, old_file, unique_file, log_file)
#
#             # Move data file as latest old snapshot
#             try:
#                 shutil.move(data_file, old_file)
#                 with open(log_file, 'a', encoding='utf-8') as lf:
#                     lf.write(f"[{datetime.datetime.now()}] ✅ Data file moved to old snapshot: {old_file}\n")
#             except Exception as e:
#                 with open(log_file, 'a', encoding='utf-8') as lf:
#                     lf.write(f"[{datetime.datetime.now()}] ❌ Error moving file to old snapshot: {data_file}. Error: {e}\n")

import json
import os
import shutil
import datetime

def compare_files(data_file, old_file, unique_file, log_file):
    def log(message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, 'a', encoding='utf-8') as lf:
            lf.write(f"[{timestamp}] {message}\n")

    def load_json_lines(file_path):
        data = []
        if not os.path.exists(file_path):
            log(f"⚠ File not found (treated as empty): {file_path}")
            return data
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().rstrip(",")
                if line:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        log(f"❌ Skipping invalid JSON in {file_path}: {line}. Error: {e}")
        return data

    def normalize(record):
        return json.dumps(record)

    try:
        log(f"Started comparison: {data_file}")
        new_data = load_json_lines(data_file)
        old_data = load_json_lines(old_file)

        new_set = set(normalize(d) for d in new_data)
        old_set = set(normalize(d) for d in old_data)

        unique = new_set - old_set
        unique_records = [json.loads(u) for u in unique]

        if unique_records:
            with open(unique_file, 'w', encoding='utf-8') as f:
                for entry in unique_records:
                    f.write(json.dumps(entry, ensure_ascii=False) + ",\n")
            log(f"✅ {len(unique_records)} unique records written: {unique_file}")
        else:
            log(f"⚠ No unique records found for {data_file}")

    except Exception as e:
        log(f"❌ ERROR comparing {data_file}: {e}")

def create_unique():
    base_dir = r"D:\RERA_Scheduler"
    data_folder = os.path.join(base_dir, "New_Data")
    old_folder = os.path.join(base_dir, "Old_Data")
    unique_folder = os.path.join(base_dir, "Unique_data")
    log_file = os.path.join(base_dir, "process_log.txt")

    os.makedirs(old_folder, exist_ok=True)
    os.makedirs(unique_folder, exist_ok=True)

    for file in os.listdir(data_folder):
        if file.endswith(".txt"):
            data_file = os.path.join(data_folder, file)

            parts = file.split("_")
            if len(parts) < 4:
                with open(log_file, 'a', encoding='utf-8') as lf:
                    lf.write(f"[{datetime.datetime.now()}] ⚠ Invalid file name format skipped: {file}\n")
                continue

            state_name = parts[2]
            timestamp = parts[3].split('.')[0]

            old_file = os.path.join(old_folder, f"Rera_cases_{state_name}.txt")
            unique_file = os.path.join(unique_folder, f"Unique_{state_name}_{timestamp}.txt")

            compare_files(data_file, old_file, unique_file, log_file)

            try:
                shutil.move(data_file, old_file)
                with open(log_file, 'a', encoding='utf-8') as lf:
                    lf.write(f"[{datetime.datetime.now()}] ✅ Data file moved to old snapshot: {old_file}\n")
            except Exception as e:
                with open(log_file, 'a', encoding='utf-8') as lf:
                    lf.write(f"[{datetime.datetime.now()}] ❌ Error moving file to old snapshot: {data_file}. Error: {e}\n")


