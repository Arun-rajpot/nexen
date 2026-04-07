import requests
import json
import os
import shutil
from datetime import date

today = date.today()

def write_data_to_textfile(data):
    try:
        post_data = json.dumps(data)
        with open(f"D:\\SAT_DATA\\SAT_project\\Cin_resolve\\Resolve\\sat_Resolved_{today}.txt", 'a') as f:
            f.writelines(post_data)
            f.writelines(',')
            f.writelines('\n')
    except Exception as e:
        print(f"Exception occurred while writing data: {e}")

def write_errordata_in_textfile(data):
    try:
        post_data = json.dumps(data)
        with open(f"D:\\SAT_DATA\\SAT_project\\Cin_resolve\\Error\\sat_NotResolvedError_{today}.txt", 'a') as f:
            f.writelines(post_data)
            f.writelines(',')
            f.writelines('\n')
    except Exception as e:
        print(f"Exception occurred while writing error data: {e}")

def postcin_5000(name):
    url = 'http://localhost:5000/api/company-details'
    data = {"company_name": name}
    header = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url=url, data=json.dumps(data), headers=header)
        resp.raise_for_status()
        print(resp.json())
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred with port 5000 API: {e}")
        return None

def postcin_5001(name):
    url = 'http://localhost:5001/api/company-details_new'
    data = {"company_name": name}
    header = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url=url, data=json.dumps(data), headers=header)
        resp.raise_for_status()
        print(resp.json())
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred with port 5001 API: {e}")
        return None

def handle_cin_response(response):
    if isinstance(response, dict):
        return [response["CIN"]] if "CIN" in response else [None]
    elif isinstance(response, list):
        return [item["CIN"] for item in response if "CIN" in item] or [None]
    return [None]

def nclt_cinresolve(file):
    try:
        input_file_path = f"D:\\SAT_DATA\\SAT_project\\New_Data\\{file}"
        with open(input_file_path, 'r') as input_file:
            petitioner_check = None
            respondent_check = None
            petitionerCin__check = []
            respondentCin__check = []

            for line in input_file:
                json_data = line.strip().replace('},', '}')
                try:
                    data = json.loads(json_data)
                except json.JSONDecodeError as json_error:
                    print(f"Error parsing JSON: {json_error}")
                    continue

                petitioner = data.get("petitionerName").lstrip("12345)(").lstrip(".").strip().title() if data.get("petitionerName") else None
                respondent = data.get("respondentName").lstrip("12345)(").lstrip(".").strip().title() if data.get("respondentName") else None

                # Handle petitioner CIN
                if petitioner == petitioner_check:
                    petitionerCin__check = petitionerCin__check
                elif petitioner and any(keyword in petitioner for keyword in ["Ltd", "Limited", "Llp", "Bank"]):
                    print("---api call 5000-----")
                    petitionerCin = postcin_5000(petitioner)
                    if not petitionerCin or "CIN" not in petitionerCin:
                        print("---api call 5001-----")
                        petitionerCin = postcin_5001(petitioner)
                    petitionerCin__check = handle_cin_response(petitionerCin)
                    petitioner_check = petitioner
                else:
                    petitionerCin__check = [None]
                    petitioner_check = petitioner

                # Handle respondent CIN
                if respondent == respondent_check:
                    respondentCin__check = respondentCin__check
                elif respondent and any(keyword in respondent for keyword in ["Ltd", "Limited", "Llp", "Bank"]):
                    print("---api call 5000-----")
                    respondentCin = postcin_5000(respondent)
                    if not respondentCin or "CIN" not in respondentCin:
                        print("---api call 5001-----")
                        respondentCin = postcin_5001(respondent)
                    respondentCin__check = handle_cin_response(respondentCin)
                    respondent_check = respondent
                else:
                    respondentCin__check = [None]
                    respondent_check = respondent

                # Safely combine petitioner and respondent CIN lists
                petitionerCin__check = petitionerCin__check if petitionerCin__check else [None]
                respondentCin__check = respondentCin__check if respondentCin__check else [None]

                data['petitionerCin'] = petitionerCin__check[0] if petitionerCin__check else None
                data['respondentCin'] = respondentCin__check[0] if respondentCin__check else None

                # Write the results
                if any(cin is not None and cin != 'null' for cin in petitionerCin__check + respondentCin__check):
                    for petitionerCin in petitionerCin__check:
                        for respondentCin in respondentCin__check:
                            data['petitionerCin'] = petitionerCin
                            data['respondentCin'] = respondentCin
                            print(data)
                            write_data_to_textfile(data)
                else:
                    print(data)
                    write_errordata_in_textfile(data)

        # ✅ Move processed file to Old_Data
        old_data_path = f"D:\\SAT_DATA\\SAT_project\\Old_Data\\{file}"
        shutil.move(input_file_path, old_data_path)
        print(f"✅ Moved processed file to Old_Data: {file}")

    except Exception as e:
        print(f"An error occurred: {e}")

def cin_resolve():
    file_path = r"D:\\SAT_DATA\\SAT_project\\New_Data"
    dir_list = os.listdir(file_path)
    for file in dir_list:
        print(f"Processing: {file}")
        nclt_cinresolve(file)

# Trigger the process
# cin_resolve()
