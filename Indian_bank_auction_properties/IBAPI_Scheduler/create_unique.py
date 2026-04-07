import os
import json
from datetime import datetime

# === CONFIG PATHS ===
data_dir = r"D:\IBAPI\IBAPI_project\Data"
old_data_dir = r"D:\IBAPI\IBAPI_project\Old_Data"
unique_output_dir = r"D:\IBAPI\IBAPI_project\unique_data"
log_dir = r"D:\IBAPI\IBAPI_project\log"
today = datetime.now().strftime("%Y-%m-%d")
log_file_path = os.path.join(log_dir, f"compare_log_{today}.log")

# === Ensure directories exist ===
os.makedirs(unique_output_dir, exist_ok=True)
os.makedirs(old_data_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

# === Logging function ===
def write_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"[{timestamp}] {message}\n")
    print(message)

# === Helper to clean line and parse JSON ===
def clean_and_parse_line(line):
    line = line.strip().rstrip(',')

    # Fix Unicode quotes and remove non-ASCII chars (optional)
    line = line.replace('\u201c', '"').replace('\u201d', '"')
    line = line.replace('\u2018', "'").replace('\u2019', "'")
    line = line.encode('ascii', 'ignore').decode('ascii')

    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None

# === Compare old and new files, save unique ===
def compare_files(old_file_path, new_file_path, unique_output_path, bank_name):
    try:
        old_data = set()
        new_data = set()

        # Load old data
        if os.path.exists(old_file_path):
            with open(old_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parsed = clean_and_parse_line(line)
                    if parsed:
                        parsed.pop('CLICK_COUNT', None)  # Remove CLICK_COUNT if exists
                        old_data.add(json.dumps(parsed, sort_keys=True))

        # Load new data
        if os.path.exists(new_file_path):
            with open(new_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parsed = clean_and_parse_line(line)
                    if parsed:
                        parsed.pop('CLICK_COUNT', None)
                        new_data.add(json.dumps(parsed, sort_keys=True))

        # Calculate unique entries
        unique_data = new_data - old_data

        if unique_data:
            with open(unique_output_path, 'w', encoding='utf-8') as out_file:
                for entry in unique_data:
                    out_file.write(entry + '\n')
            write_log(f"✅ Unique entries saved for {bank_name}: {unique_output_path}")
        else:
            write_log(f"⚠️ No unique entries found for {bank_name}.")

    except Exception as e:
        write_log(f"❌ Error comparing files for {bank_name}: {e}")

# === Main function to process all files ===
def compare_and_update_all():
    write_log("\n========== IBAPI COMPARISON RUN STARTED ==========")
    for file_name in os.listdir(data_dir):
        if file_name.endswith('.txt') and "_" in file_name:
            try:
                # Extract bank name (everything before last underscore)
                bank_name = "_".join(file_name.split("_")[:-1])
                new_file_path = os.path.join(data_dir, file_name)
                old_file_path = os.path.join(old_data_dir, f"{bank_name}.txt")
                unique_output_path = os.path.join(unique_output_dir, f"All_unique_{today}_{bank_name}.txt")

                write_log(f"\n🔍 Processing: {file_name} → Bank: {bank_name}")

                # Compare and create unique file
                compare_files(old_file_path, new_file_path, unique_output_path, bank_name)

                # Overwrite old file with new file content
                with open(new_file_path, 'r', encoding='utf-8') as newf, \
                     open(old_file_path, 'w', encoding='utf-8') as oldf:
                    oldf.writelines(newf.readlines())

                write_log(f"📦 Old data updated for {bank_name}: {old_file_path}")

            except Exception as err:
                write_log(f"❌ Failed to process file {file_name}: {err}")

    # Delete all files from Data directory after processing
    for file in os.listdir(data_dir):
        file_path = os.path.join(data_dir, file)
        if os.path.isfile(file_path) and file.endswith('.txt'):
            try:
                os.remove(file_path)
                write_log(f"🗑️ Deleted processed file from Data dir: {file}")
            except Exception as e:
                write_log(f"❌ Failed to delete file {file}: {e}")

    write_log("✅ IBAPI COMPARISON RUN COMPLETED\n")

# === Run the script ===
# if __name__ == "__main__":
#     compare_and_update_all()
