import requests
import json
import os
from datetime import datetime, date

today = date.today()

def write_IBAPI_resolve_textfile(data, file):
    try:
        post_data = json.dumps(data)
        with open(f"D:\\IBAPI\\IBAPI_project\\Cin_Resolve\\Resolve\\{file}_ResolvedFile_{today}.txt", 'a') as f:
            f.writelines(post_data)
            f.writelines(',')
            f.writelines('\n')
    except Exception as e:
        print("Exception occurred={}".format(e))


def write_IBAPI_erorr_textfile(data, file):
    try:
        post_data = json.dumps(data)
        with open(f"D:\\IBAPI\\IBAPI_project\\Cin_Resolve\\Error\\{file}_NotResolvedError_{today}.txt", 'a') as f:
            f.writelines(post_data)
            f.writelines(',')
            f.writelines('\n')
    except Exception as e:
        print("Exception occurred={}".format(e))


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


def ibapi_cinresolve(file):
    try:
        # Open the input file
        with open(f"D:\\IBAPI\\IBAPI_project\\Unique_data\\{file}", 'r') as input_file:
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

                petitioner = data.get("BANK_NAME").lstrip("12345)(").lstrip(".").strip().title() if data.get("BANK_NAME") else None
                respondent = data.get("BORROWER_NAME").lstrip("12345)(").lstrip(".").strip().title() if data.get("BORROWER_NAME") else None

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

                # Combine CINs
                petitionerCin__check = petitionerCin__check if petitionerCin__check else [None]
                respondentCin__check = respondentCin__check if respondentCin__check else [None]

                data['BANK_CIN'] = petitionerCin__check[0] if petitionerCin__check else None
                data['BORROWER_CIN'] = respondentCin__check[0] if respondentCin__check else None

                # Write result
                if any(cin is not None and cin != 'null' for cin in petitionerCin__check + respondentCin__check):
                    for petitionerCin in petitionerCin__check:
                        for respondentCin in respondentCin__check:
                            data['BANK_CIN'] = petitionerCin
                            data['BORROWER_CIN'] = respondentCin
                            print(data)
                            write_IBAPI_resolve_textfile(data, file)
                else:
                    print(data)
                    write_IBAPI_erorr_textfile(data, file)

    except Exception as e:
        print(f"An error occurred while processing file: {file} — {e}")

    # Move file to processed_data
    try:
        source_path = os.path.join("D:\\IBAPI\\IBAPI_project\\Unique_data", file)
        dest_path = os.path.join("D:\\IBAPI\\IBAPI_project\\processed_data", file)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        os.rename(source_path, dest_path)
        print(f"✅ Moved file to processed_data: {file}")
    except Exception as move_err:
        print(f"⚠️ Failed to move file: {file} — {move_err}")


def IBAPI_cin_resolve():
    file_path = r"D:\\IBAPI\\IBAPI_project\\Unique_data"
    os.makedirs("D:\\IBAPI\\IBAPI_project\\processed_data", exist_ok=True)
    dir_list = os.listdir(file_path)
    for file in dir_list:
        ibapi_cinresolve(file)
