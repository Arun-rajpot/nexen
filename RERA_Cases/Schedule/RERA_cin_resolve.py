import requests
import json
import os
import shutil
from datetime import date

today = date.today()

# === WRITE FUNCTIONS ===
def write_resolved_data(data, file):
    try:
        post_data = json.dumps(data)
        with open(f"G:\\RERA\\resolve\\{file}_ResolvedFile_{today}.txt", 'a', encoding='utf-8') as f:
            f.write(post_data + ',\n')
    except Exception as e:
        print(f"Exception occurred while writing resolved data: {e}")

def write_error_data(data, file):
    try:
        post_data = json.dumps(data)
        with open(f"G:\\RERA\\error\\{file}_NotResolvedError_{today}.txt", 'a', encoding='utf-8') as f:
            f.write(post_data + ',\n')
    except Exception as e:
        print(f"Exception occurred while writing error data: {e}")

# === API CALL FUNCTIONS ===
def postcin_5000(name):
    url = 'http://localhost:5000/api/company-details'
    data = {"company_name": name}
    header = {"Content-Type": "application/json"}
    try:
        resp = requests.post(url, data=json.dumps(data), headers=header, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error with 5000 API: {e}")
        return None

def postcin_5001(name):
    url = 'http://localhost:5001/api/company-details_new'
    data = {"company_name": name}
    header = {"Content-Type": "application/json"}
    try:
        resp = requests.post(url, data=json.dumps(data), headers=header, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error with 5001 API: {e}")
        return None

def handle_cin_response(response):
    if isinstance(response, dict):
        return [response["CIN"]] if "CIN" in response else [None]
    elif isinstance(response, list):
        return [item["CIN"] for item in response if "CIN" in item] or [None]
    return [None]

# === MAIN PROCESSING FUNCTION ===
def resolve_cin_for_file(file_path, processed_folder):
    try:
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, 'r', encoding='utf-8') as input_file:
            petitioner_check, respondent_check = None, None
            petitioner_cin_cache, respondent_cin_cache = [], []

            for line in input_file:
                json_data = line.strip().replace('},', '}')
                if not json_data:
                    continue
                try:
                    data = json.loads(json_data)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    continue

                petitioner = data.get("Applicant", "").lstrip("12345).(").strip().title()
                respondent = data.get("Respondent", "").lstrip("12345).(").strip().title()

                # === PETITIONER CIN RESOLUTION ===
                if petitioner and petitioner != petitioner_check:
                    if any(keyword in petitioner for keyword in ["Ltd", "Limited", "Llp", "Bank"]):
                        resp = postcin_5000(petitioner)
                        if not resp or "CIN" not in str(resp):
                            resp = postcin_5001(petitioner)
                        petitioner_cin_cache = handle_cin_response(resp)
                    else:
                        petitioner_cin_cache = [None]
                    petitioner_check = petitioner

                # === RESPONDENT CIN RESOLUTION ===
                if respondent and respondent != respondent_check:
                    if any(keyword in respondent for keyword in ["Ltd", "Limited", "Llp", "Bank"]):
                        resp = postcin_5000(respondent)
                        if not resp or "CIN" not in str(resp):
                            resp = postcin_5001(respondent)
                        respondent_cin_cache = handle_cin_response(resp)
                    else:
                        respondent_cin_cache = [None]
                    respondent_check = respondent

                # Fallback in case API gave no data
                petitioner_cin_cache = petitioner_cin_cache or [None]
                respondent_cin_cache = respondent_cin_cache or [None]

                if any(cin and cin != 'null' for cin in petitioner_cin_cache + respondent_cin_cache):
                    for pCin in petitioner_cin_cache:
                        for rCin in respondent_cin_cache:
                            data["Applicant_Cin"] = pCin
                            data["Respondent_Cin"] = rCin
                            print("✅ Resolved:", data)
                            write_resolved_data(data, file_name)
                else:
                    data["Applicant_Cin"] = None
                    data["Respondent_Cin"] = None
                    print("❌ Not Resolved:", data)
                    write_error_data(data, file_name)

        # Move to processed folder
        processed_path = os.path.join(processed_folder, os.path.basename(file_path))
        shutil.move(file_path, processed_path)
        print(f"📁 Moved to Processed: {processed_path}")

    except Exception as e:
        print(f"Error while processing file {file_path}: {e}")

# === PROCESS ALL FILES ===
def process_all_files():
    input_folder = r"G:\RERA\rera_2025-06-23"
    processed_folder = r"G:\RERA\processed"
    os.makedirs(processed_folder, exist_ok=True)

    for file in os.listdir(input_folder):
        if file.endswith(".txt"):
            file_path = os.path.join(input_folder, file)
            resolve_cin_for_file(file_path, processed_folder)

# # === RUN ===
# process_all_files()
