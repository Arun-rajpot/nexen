# import requests
# import json
# import os
# import shutil
# from datetime import date
#
# today = date.today()
#
# def write_data_to_textfile(data):
#     try:
#         post_data = json.dumps(data)
#         with open(f"D:\\New_Rera\\New_rera_project\\Cin_Resolve\\Resolve\\rera_Resolved_{today}.txt", 'a', encoding='utf-8') as f:
#             f.write(post_data + ',\n')
#     except Exception as e:
#         print(f"Exception occurred while writing data: {e}")
#
# def write_errordata_in_textfile(data):
#     try:
#         post_data = json.dumps(data)
#         with open(f"D:\\New_Rera\\New_rera_project\\Cin_Resolve\\Error\\rera_NotResolvedError_{today}.txt", 'a', encoding='utf-8') as f:
#             f.write(post_data + ',\n')
#     except Exception as e:
#         print(f"Exception occurred while writing error data: {e}")
#
# # def postcin_5000(name):
# #     url = 'http://localhost:5000/api/company-details'
# #     data = {"company_name": name}
# #     header = {"Content-Type": "application/json"}
# #     try:
# #         resp = requests.post(url=url, data=json.dumps(data), headers=header, timeout=10)
# #         resp.raise_for_status()
# #         return resp.json()
# #     except requests.exceptions.RequestException as e:
# #         print(f"An error occurred with port 5000 API: {e}")
# #         return None
# #
# # def postcin_5001(name):
# #     url = 'http://localhost:5001/api/company-details_new'
# #     data = {"company_name": name}
# #     header = {"Content-Type": "application/json"}
# #     try:
# #         resp = requests.post(url=url, data=json.dumps(data), headers=header, timeout=10)
# #         resp.raise_for_status()
# #         return resp.json()
# #     except requests.exceptions.RequestException as e:
# #         print(f"An error occurred with port 5001 API: {e}")
# #         return None
# def get_cin(company):
#     company = company.replace(" ", "%20")
#     response = requests.get(r"http://127.0.0.1:5011/resolve_cin?company_name={}".format(company))
#     print("  :", response.json())
#     return response.json()
# def handle_cin_response(response):
#     if isinstance(response, dict):
#         return [response["cin"]] if "cin" in response else [None]
#     elif isinstance(response, list):
#         return [item["cin"] for item in response if "cin" in item] or [None]
#     return [None]
#
# def rera_new_cinresolve(file_path, processed_folder):
#     try:
#         with open(file_path, 'r', encoding='utf-8') as input_file:
#             project_check = None
#             promoter_check = None
#             projectCin__check = []
#             promoterCin__check = []
#
#             for line in input_file:
#                 json_data = line.strip().replace('},', '}')
#                 if not json_data:
#                     continue
#                 try:
#                     data = json.loads(json_data)
#                 except json.JSONDecodeError as json_error:
#                     print(f"Error parsing JSON: {json_error}")
#                     continue
#
#                 project = data.get("projectName", "").strip().title()
#                 promoter = data.get("promoterName", "").strip().title()
#
#                 if project != project_check and project:
#                     projectCin = get_cin(project)
#                     if not projectCin or "cin" not in str(projectCin):
#                         projectCin = None #postcin_5001(project)
#                     projectCin__check = handle_cin_response(projectCin)
#                     project_check = project
#
#                 if promoter != promoter_check and promoter:
#                     promoterCin = get_cin(promoter)
#                     if not promoterCin or "cin" not in str(promoterCin):
#                         promoterCin = None #postcin_5001(promoter)
#                     promoterCin__check = handle_cin_response(promoterCin)
#                     promoter_check = promoter
#
#                 projectCin__check = projectCin__check if projectCin__check else [None]
#                 promoterCin__check = promoterCin__check if promoterCin__check else [None]
#
#                 if any(cin and cin != 'null' for cin in projectCin__check + promoterCin__check):
#                     for pCin in projectCin__check:
#                         for prCin in promoterCin__check:
#                             data['projectCin'] = pCin
#                             data['promoterCin'] = prCin
#                             print(f"Resolved: {data}")
#                             write_data_to_textfile(data)
#                 else:
#                     data['projectCin'] = None
#                     data['promoterCin'] = None
#                     print(f"Not resolved: {data}")
#                     write_errordata_in_textfile(data)
#
#         # After processing, move file to Processed folder
#         processed_path = os.path.join(processed_folder, os.path.basename(file_path))
#         shutil.move(file_path, processed_path)
#         print(f"✅ File moved to processed: {processed_path}")
#
#     except Exception as e:
#         print(f"An error occurred processing {file_path}: {e}")
#
# def process_all_unique_files():
#     unique_folder = r"D:\New_Rera\New_rera_project\Unique_data"
#     processed_folder = r"D:\New_Rera\New_rera_project\Processed"
#     os.makedirs(processed_folder, exist_ok=True)
#
#     for file in os.listdir(unique_folder):
#         if file.endswith(".txt"):
#             file_path = os.path.join(unique_folder, file)
#             rera_new_cinresolve(file_path, processed_folder)
#
# # Run the processing
# process_all_unique_files()
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
        with open(f"D:\\RERA_Scheduler\\Cin_resolve\\Resolve\\{file}_ResolvedFile_{today}.txt", 'a', encoding='utf-8') as f:
            f.write(post_data + ',\n')
    except Exception as e:
        print(f"Exception occurred while writing resolved data: {e}")

def write_error_data(data, file):
    try:
        post_data = json.dumps(data)
        with open(f"D:\\RERA_Scheduler\\Cin_resolve\\Error\\{file}_NotResolvedError_{today}.txt", 'a', encoding='utf-8') as f:
            f.write(post_data + ',\n')
    except Exception as e:
        print(f"Exception occurred while writing error data: {e}")

# === API CALL FUNCTIONS ===
def postcin_5000(name):
    url = 'http://localhost:5000/api/company-details'
    data = {"company_name": name}
    header = {"Content-Type": "application/json"}
    try:
        resp = requests.post(url, data=json.dumps(data), headers=header)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error with 5000 API: {e}")
        return None

# def postcin_5001(name):
#     url = 'http://localhost:5001/api/company-details_new'
#     data = {"company_name": name}
#     header = {"Content-Type": "application/json"}
#     try:
#         resp = requests.post(url, data=json.dumps(data), headers=header, timeout=10)
#         resp.raise_for_status()
#         return resp.json()
#     except requests.exceptions.RequestException as e:
#         print(f"Error with 5001 API: {e}")
#         return None

def handle_cin_response(response):
    if isinstance(response, dict):
        return [response["CIN"]] if "CIN" in response else [None]
    elif isinstance(response, list):
        return [item["CIN"] for item in response if "CIN" in item] or [None]
    return [None]

# def get_cin(company):
#     company = company.replace(" ", "%20")
#     response = requests.get(r"http://127.0.0.1:5011/resolve_cin?company_name={}".format(company))
#     print("  :", response.json())
#     return response.json()
def handle_cin_response(response):
    if isinstance(response, dict):
        return [response["cin"]] if "cin" in response else [None]
    elif isinstance(response, list):
        return [item["cin"] for item in response if "cin" in item] or [None]
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

                petitioner_raw = data.get("Applicant")
                respondent_raw = data.get("Respondent")

                petitioner = petitioner_raw.lstrip("12345).(").strip().title() if petitioner_raw else ""
                respondent = respondent_raw.lstrip("12345).(").strip().title() if respondent_raw else ""

                # === PETITIONER CIN RESOLUTION ===
                if petitioner and petitioner != petitioner_check:
                    if any(keyword in petitioner for keyword in ["Ltd", "Limited", "Llp", "Bank"]):
                        resp = postcin_5000(petitioner)
                        if not resp or "CIN" not in str(resp):
                            resp = None#postcin_5001(petitioner)
                        petitioner_cin_cache = handle_cin_response(resp)
                    else:
                        petitioner_cin_cache = [None]
                    petitioner_check = petitioner

                # === RESPONDENT CIN RESOLUTION ===
                if respondent and respondent != respondent_check:
                    if any(keyword in respondent for keyword in ["Ltd", "Limited", "Llp", "Bank"]):
                        resp = postcin_5000(respondent)
                        if not resp or "CIN" not in str(resp):
                            resp = None #postcin_5001(respondent)
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
    input_folder = r"D:\RERA_Scheduler\Unique_data"
    processed_folder = r"D:\RERA_Scheduler\Processed_data"
    os.makedirs(processed_folder, exist_ok=True)

    for file in os.listdir(input_folder):
        if file.endswith(".txt"):
            file_path = os.path.join(input_folder, file)
            resolve_cin_for_file(file_path, processed_folder)

# # === RUN ===
process_all_files()
