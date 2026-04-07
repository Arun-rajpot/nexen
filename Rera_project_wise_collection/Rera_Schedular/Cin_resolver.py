import requests
import json
import os
import shutil
from datetime import date

today = date.today()

def write_data_to_textfile(data):
    try:
        post_data = json.dumps(data)
        with open(f"D:\\New_Rera\\New_rera_project\\Cin_Resolve\\Resolve\\rera_Resolved_old_API{today}.txt", 'a', encoding='utf-8') as f:
            f.write(post_data + ',\n')
    except Exception as e:
        print(f"Exception occurred while writing data: {e}")

def write_errordata_in_textfile(data):
    try:
        post_data = json.dumps(data)
        with open(f"D:\\New_Rera\\New_rera_project\\Cin_Resolve\\Error\\rera_NotResolvedError_old_api{today}.txt", 'a', encoding='utf-8') as f:
            f.write(post_data + ',\n')
    except Exception as e:
        print(f"Exception occurred while writing error data: {e}")

def postcin_5000(name):
    url = 'http://localhost:5000/api/company-details'
    data = {"company_name": name}
    header = {"Content-Type": "application/json"}
    try:
        resp = requests.post(url=url, data=json.dumps(data), headers=header, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred with port 5000 API: {e}")
        return None
#
# def postcin_5001(name):
#     url = 'http://localhost:5001/api/company-details_new'
#     data = {"company_name": name}
#     header = {"Content-Type": "application/json"}
#     try:
#         resp = requests.post(url=url, data=json.dumps(data), headers=header, timeout=10)
#         resp.raise_for_status()
#         return resp.json()
#     except requests.exceptions.RequestException as e:
#         print(f"An error occurred with port 5001 API: {e}")
#         return None

# def get_cin(company):
#     company = company.replace(" ", "%20")
#     response = requests.get(r"http://127.0.0.1:5011/resolve_cin?company_name={}".format(company))
#     print("  :", response.json())
#     return response.json()

def handle_cin_response(response):
    if isinstance(response, dict):
        return [response["CIN"]] if "CIN" in response else [None]
    elif isinstance(response, list):
        return [item["CIN"] for item in response if "CIN" in item] or [None]
    return [None]

def rera_new_cinresolve(file_path, processed_folder):
    try:
        with open(file_path, 'r', encoding='utf-8') as input_file:
            project_check = None
            promoter_check = None
            projectCin__check = []
            promoterCin__check = []

            for line in input_file:
                json_data = line.strip().replace('},', '}')
                if not json_data:
                    continue
                try:
                    data = json.loads(json_data)
                except json.JSONDecodeError as json_error:
                    print(f"Error parsing JSON: {json_error}")
                    continue

                project = data.get("projectName", "").strip().title()
                promoter = data.get("promoterName", "").strip().title()

                if project != project_check and project:
                    projectCin = postcin_5000(project)
                    if not projectCin or "CIN" not in str(projectCin):
                        projectCin = None #postcin_5001(project)
                    projectCin__check = handle_cin_response(projectCin)
                    project_check = project

                if promoter != promoter_check and promoter:
                    promoterCin = postcin_5000(promoter)
                    if not promoterCin or "CIN" not in str(promoterCin):

                        promoterCin = None#postcin_5001(promoter)
                    promoterCin__check = handle_cin_response(promoterCin)
                    promoter_check = promoter

                projectCin__check = projectCin__check if projectCin__check else [None]
                promoterCin__check = promoterCin__check if promoterCin__check else [None]

                if any(cin and cin != 'null' for cin in projectCin__check + promoterCin__check):
                    for pCin in projectCin__check:
                        for prCin in promoterCin__check:
                            data['projectCin'] = pCin
                            data['promoterCin'] = prCin
                            print(f"Resolved: {data}")
                            write_data_to_textfile(data)
                else:
                    data['projectCin'] = None
                    data['promoterCin'] = None
                    print(f"Not resolved: {data}")
                    write_errordata_in_textfile(data)

        # After processing, move file to Processed folder
        processed_path = os.path.join(processed_folder, os.path.basename(file_path))
        shutil.move(file_path, processed_path)
        print(f"✅ File moved to processed: {processed_path}")

    except Exception as e:
        print(f"An error occurred processing {file_path}: {e}")

def process_all_unique_files():
    unique_folder = r"D:\New_Rera\New_rera_project\Unique_Data"
    processed_folder = r"D:\New_Rera\New_rera_project\Processed"
    os.makedirs(processed_folder, exist_ok=True)

    for file in os.listdir(unique_folder):
        if file.endswith(".txt"):
            file_path = os.path.join(unique_folder, file)
            rera_new_cinresolve(file_path, processed_folder)

# Run the processing
process_all_unique_files()
