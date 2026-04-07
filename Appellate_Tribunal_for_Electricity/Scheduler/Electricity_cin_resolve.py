import requests
import json
import os
from datetime import datetime, date
import shutil

today = date.today()


# Step:- Write final payload to text file :-
def write_Electricity_resolve_textfile(data, file):
    try:
        post_data = json.dumps(data)
        #         print(post_data)
        with open("D:\\SATElectricity\\Cin resolve\\resolve_file\\" + file + "_ResolvedFile_{}.txt".format(today), 'a') as f:
            f.writelines(post_data)
            f.writelines(',')
            f.writelines('\n')
    except Exception as e:
        print("Exception occurred={}".format(e))


# Step:- Write final payload to text file :-
def write_Electricity_erorr_textfile(data, file):
    try:
        post_data = json.dumps(data)
        #         print(post_data)
        with open("D:\\SATElectricity\\Cin resolve\\error_file\\" + file + "_NotResolvedError_{}.txt".format(today), 'a') as f:
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
        resp.raise_for_status()  # Raises HTTPError for bad responses (4xx and 5xx)
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
        resp.raise_for_status()  # Raises HTTPError for bad responses (4xx and 5xx)
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


def Electricity_cinresolve(file):

    try:
        # Open the input file
        with open(f"D:\\SATElectricity\\Data\\{file}", 'r') as input_file:
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

                petitioner = data.get("Appellant_name").lstrip("12345)(").lstrip(".").strip().title() if data.get(
                    "Appellant_name") else None
                respondent = data.get("Respondent_name").lstrip("12345)(").lstrip(".").strip().title() if data.get(
                    "Respondent_name") else None

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

                data['Appellant_cin'] = petitionerCin__check[0] if petitionerCin__check else None
                data['Respondent_cin'] = respondentCin__check[0] if respondentCin__check else None

                # Write the results
                if any(cin is not None and cin != 'null' for cin in petitionerCin__check + respondentCin__check):
                    for petitionerCin in petitionerCin__check:
                        for respondentCin in respondentCin__check:
                            data['Appellant_cin'] = petitionerCin
                            data['Respondent_cin'] = respondentCin
                            print(data)
                            write_Electricity_resolve_textfile(data, file)
                else:
                    print(data)
                    write_Electricity_erorr_textfile(data, file)

    except Exception as e:
        print(f"An error occurred: {e}")





def cin_resolve_main():

    file_path = r"D:\\SATElectricity\\Data"
    processed_path = r"D:\\SATElectricity\\processed files"

    # Ensure processed directory exists
    os.makedirs(processed_path, exist_ok=True)

    dir_list = os.listdir(file_path)
    for file in dir_list:
        Electricity_cinresolve(file)

    # After processing all files, move them to 'processed files' directory
    for file in dir_list:
        src = os.path.join(file_path, file)
        dst = os.path.join(processed_path, file)
        try:
            shutil.move(src, dst)
            print(f"Moved processed file: {file}")
        except Exception as e:
            print(f"Error moving file {file}: {e}")