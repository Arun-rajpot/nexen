# from bs4 import BeautifulSoup
# import requests
# import json
# from datetime import datetime
# from Scripts.write_to_txt_file import write_to_MargeFile
#
#
#
# def get_final_payload(project, data, data1):
#     print(data)
#     if data.get('Approved Date'):
#         projectStartDate = data.get('Approved Date').split(' ')[0].strip()  # Remove comma
#         print(projectStartDate)  # Check the output
#         projectStartDate = datetime.strptime(projectStartDate, "%d/%m/%Y").strftime("%Y-%m-%d")
#     else:
#         projectStartDate = None
#
#     if data.get('Proposed Date of Completion'):
#         Proposed_Date_of_Completion = data.get('Proposed Date of Completion')
#         Proposed_Date_of_Completion = datetime.strptime(Proposed_Date_of_Completion, "%d/%m/%Y").strftime("%Y-%m-%d")
#
#     else:
#         Proposed_Date_of_Completion = None
#
#     project_data = {
#         'projectCin': None,
#         'promoterCin': None,
#         'projectName': project.get('Project Name'),
#         'promoterName': project.get('Promoter Name'),
#         'acknowledgementNumber': None,
#         'projectRegistrationNo': data.get('Plan Approval Number'),
#         'reraRegistrationDate': projectStartDate,
#         'projectProposeCompletionDate': Proposed_Date_of_Completion,
#         'projectStatus': data.get('Project Status'),
#         'projectType': data.get('Project Type'),
#         'promoterType': data1.get('Promoter Type'),
#         'projectStateName': data.get('State'),
#         'projectPinCode': data.get('PIN Code'),
#         'projectDistrictName': data.get('District'),
#         'projectVillageName': data.get('Mandal'),
#         'projectAddress': data.get('Plot No./House No.'),
#         'totalLandArea': data.get('Total Area(In sqmts)'),
#         'promotersAddress': data1.get('Street  Name'),
#         'landownerTypes': None,
#         'promoterPinCode': data1.get('Pin Code'),
#         'longitude': None,
#         'latitude': None,
#         'viewLink': "https://rerait.telangana.gov.in/SearchList/Search"
#     }
#     return project_data
#
#
# def clean_text(text):
#     return text.replace('\xa0', ' ').strip() if text else None
#
#
# # def extract_div_data(postsoup, container_id):
# #     container = postsoup.find("div", id=container_id)
# #     if not container:
# #         return None
# #
# #     data = {}
# #     rows = container.find_all("div", class_="form-group")
# #
# #     for row in rows:
# #         labels = row.find_all("label")
# #         values = row.find_all("div", class_="col-md-3 col-sm-3")
# #
# #         for i in range(len(labels)):
# #             if len(values) < 4:
# #                 continue
# #             label_text = clean_text(labels[i].get_text(strip=True))
# #             if i == 0:
# #                 value_text = clean_text(values[1].get_text(strip=True)) if i < len(values) else None
# #             else:
# #                 value_text = clean_text(values[3].get_text(strip=True)) if i < len(values) else None
# #
# #             if label_text and value_text:
# #                 data[label_text] = value_text
# #
# #     return data
# def extract_div_data(postsoup, container_id):
#     container = postsoup.find("div", id=container_id)
#     if not container:
#         return None
#
#     data = {}
#     form_groups = container.find_all("div", class_="form-group")
#
#     for group in form_groups:
#         cols = group.find_all("div", class_="col-md-3 col-sm-3")
#
#         i = 0
#         while i < len(cols) - 1:
#             label_tag = cols[i].find("label")
#             if label_tag:
#                 label_text = clean_text(label_tag.get_text(strip=True))
#                 value_text = clean_text(cols[i + 1].get_text(strip=True))
#                 data[label_text] = value_text
#                 i += 2
#             else:
#                 i += 1  # skip if no label
#
#     return data
#
# def rera_telangana():
#     # Step 1: Create a session
#     session = requests.Session()
#
#     # Step 2: Get the initial page to extract cookies and tokens
#     init_url = "https://rerait.telangana.gov.in/SearchList/Search"
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
#     }
#
#     response = session.get(init_url, headers=headers,verify=False)
#     if response.status_code != 200:
#         print(f"Failed to get the initial page, status code: {response.status_code}")
#         exit()
#
#     # Extract cookies and verification token
#     soup = BeautifulSoup(response.text, "html.parser")
#     cookies = session.cookies.get_dict()
#     session_id = cookies.get("ASP.NET_SessionId")
#     verification_token = soup.find("input", {"name": "__RequestVerificationToken"})
#     verification_token_value = verification_token["value"] if verification_token else None
#
#     print(f"Session ID: {session_id}")
#     print(f"Verification Token: {verification_token_value}")
#
#     # Determine total number of pages
#     total_records_element = soup.find("input", {"id": "TotalRecords"})
#     total_records = int(total_records_element["value"]) if total_records_element else 0
#     page_size = 10
#     total_pages = (total_records // page_size) + (1 if total_records % page_size > 0 else 0)
#
#     # Iterate through each page
#     for current_page in range(1, total_pages + 1):
#         print(f"Processing page {current_page} of {total_pages}")
#
#         # Prepare payload for the current page
#         payload = {
#             "__RequestVerificationToken": verification_token_value,
#             "Type": "Promoter",
#             "ID": "0",
#             "pageTraverse": "1",
#             "RoleIDPageload": "1",
#             "Project": "",
#             "hdnProject": "",
#             "Promoter": "",
#             "hdnPromoter": "",
#             "AgentName": "",
#             "hdnAgent": "",
#             "CertiNo": "",
#             "hdnCertiNo": "",
#             "District": "",
#             "hdnDivision": "",
#             "hdnDistrict": "",
#             "hdnProject": "",
#             "hdnDTaluka": "",
#             "hdnVillage": "",
#             "hdnState": "",
#             "Taluka": "",
#             "Village": "",
#             "CompletionDate_From": "",
#             "hdnfromdate": "",
#             "CompletionDate_To": "",
#             "hdntodate": "",
#             "PType": "",
#             "hdnPType": "",
#             "TotalRecords": str(total_records),
#             "CurrentPage": str(current_page),
#             "TotalPages": str(total_pages),
#             "Command": "Next",
#             "PageSize": str(page_size)
#         }
#
#         # Fetch the current page
#         page_response = session.post(init_url, headers=headers, data=payload,verify=False)
#         if page_response.status_code != 200:
#             print(f"Failed to fetch page {current_page}, status code: {page_response.status_code}")
#             continue
#
#         # Parse the page content
#         soup = BeautifulSoup(page_response.text, "html.parser")  # Fix here
#
#         # Update the verification token
#         verification_token = soup.find("input", {"name": "__RequestVerificationToken"})
#         verification_token_value = verification_token["value"] if verification_token else None
#
#         # Extract project list
#         rows = soup.select("table.grid-table tbody tr")
#         projects = []
#         base_url = "https://rerait.telangana.gov.in"
#
#         for row in rows:
#             project = {
#                 "Sr No.": row.find("td", {"data-name": "Srno"}).text.strip(),
#                 "Project Name": row.find("td", {"data-name": "Project"}).text.strip(),
#                 "Promoter Name": row.find("td", {"data-name": "Name"}).text.strip(),
#                 "View Details URL": None,
#                 "View Certificate URL": None
#             }
#
#             details_link = row.find("a", href=True, target="_blank")
#             if details_link:
#                 project["View Details URL"] = base_url + details_link["href"]
#
#             projects.append(project)
#
#         # Process project details
#         for project in projects:
#             # print(project)
#             print_preview_url = project['View Details URL']
#
#             # Access the print preview page
#             print_preview_response = session.get(print_preview_url, headers=headers,verify=False)
#             if print_preview_response.status_code == 200:
#                 rsoup = BeautifulSoup(print_preview_response.text, "html.parser")
#                 data = extract_div_data(rsoup, "DivProject")
#                 # print(data)
#                 data1 = extract_div_data(rsoup, "fldind") or extract_div_data(rsoup, "fldFirm")
#                 # print(data1)
#                 final_data = get_final_payload(project, data, data1)
#                 print(final_data)
#                 # write_to_MargeFile(final_data,"Telangana")
#             else:
#                 print("Failed to access Print Preview:", print_preview_response.status_code)
#
#
# rera_telangana()

# import time
# import json
# import numpy as np
# from io import BytesIO
# from datetime import datetime
# from PIL import Image
# from bs4 import BeautifulSoup
# import requests
# import easyocr
# import cv2
# import numpy as np
# from io import BytesIO
# from PIL import Image
#
#
# # --- Configuration ---
# BASE_URL = "https://rerait.telangana.gov.in"
# SEARCH_URL = f"{BASE_URL}/SearchList/Search"
# CAPTCHA_URL = f"{BASE_URL}/SearchList/SearchCaptcha"
# OUTPUT_FILE = r"D:\Rera_new_collection\New_Rera_telangana_333.txt"
#
# HEADERS = {
#     "User-Agent": (
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
#     )
# }
#
# session = requests.Session()
# reader = easyocr.Reader(['en'], gpu=False)
#
# # --- Utility Functions ---
# # def fetch_captcha_text(max_attempts=5):
# #     """
# #     Fetch the CAPTCHA image and use EasyOCR to extract text.
# #     Retry up to max_attempts if text extraction is empty or looks invalid.
# #     """
# #     for attempt in range(1, max_attempts + 1):
# #         resp = session.get(CAPTCHA_URL, headers=HEADERS, verify=False)
# #         if resp.status_code != 200:
# #             print(f"[Attempt {attempt}] Failed to fetch CAPTCHA image, status: {resp.status_code}")
# #             time.sleep(1)
# #             continue
# #
# #         img = Image.open(BytesIO(resp.content))
# #         # Optional: show the image for debugging, comment out in prod
# #         # img.show()
# #
# #         text_results = reader.readtext(np.array(img), detail=0)
# #         captcha_text = ''.join(text_results).strip() if text_results else ""
# #
# #         # Simple validation: ensure captcha text is not empty and alphanumeric
# #         if captcha_text and captcha_text.isalnum():
# #             print(f"[Attempt {attempt}] CAPTCHA recognized as: {captcha_text}")
# #             return captcha_text
# #         else:
# #             print(f"[Attempt {attempt}] OCR returned invalid CAPTCHA: '{captcha_text}', retrying...")
# #             time.sleep(1)
# #
# #     raise ValueError("CAPTCHA recognition failed after multiple attempts")
#
#
#
# # def fetch_captcha_text():
# #     for attempt in range(5):
# #         resp = session.get(CAPTCHA_URL, headers=HEADERS, verify=False)
# #         if resp.status_code != 200:
# #             time.sleep(1)
# #             continue
# #
# #         # Load image with PIL
# #         img = Image.open(BytesIO(resp.content))
# #
# #         # Convert to grayscale
# #         img_gray = img.convert('L')
# #
# #         # Convert PIL image to OpenCV format
# #         img_np = np.array(img_gray)
# #
# #         # Apply binary thresholding to make text stand out
# #         _, img_thresh = cv2.threshold(img_np, 150, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
# #
# #         # Optional: apply dilation/erosion to clean noise
# #         kernel = np.ones((2, 2), np.uint8)
# #         img_clean = cv2.morphologyEx(img_thresh, cv2.MORPH_CLOSE, kernel)
# #
# #         # Now run OCR on cleaned image
# #         result = reader.readtext(img_clean, detail=0)
# #
# #         captcha_text = ''.join(result).strip() if result else ""
# #
# #         print(f"[Attempt {attempt + 1}] OCR result: '{captcha_text}'")
# #
# #         if captcha_text:
# #             return captcha_text
# #
# #         time.sleep(1)
# #
# #     raise ValueError("CAPTCHA recognition failed after 5 attempts")
# #
# # def format_date(date_str):
# #     try:
# #         return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
# #     except Exception:
# #         return None
# #
# # def get_final_payload(proj, data, data1):
# #     rera_date_raw = proj.get('Last Modified Date')
# #     rera_date = rera_date_raw.split()[0] if rera_date_raw else None
# #     return {
# #         'projectCin': None,
# #         'promoterCin': None,
# #         'projectName': proj.get('Project Name'),
# #         'promoterName': proj.get('Promoter Name'),
# #         'acknowledgementNumber': None,
# #         'projectRegistrationNo': data.get('Plan Approval Number'),
# #         'reraRegistrationDate': format_date(rera_date),
# #         'projectProposeCompletionDate': format_date(data.get('Proposed Date of Completion')),
# #         'projectStatus': data.get('Project Status'),
# #         'projectType': data.get('Project Type'),
# #         'promoterType': data1.get('Promoter Type'),
# #         'projectStateName': data.get('State'),
# #         'projectPinCode': data1.get('PIN Code'),
# #         'projectDistrictName': data.get('District'),
# #         'projectVillageName': data.get('Mandal'),
# #         'projectAddress': data.get('Plot No./House No.'),
# #         'totalLandArea': data.get('Total Area(In sqmts)'),
# #         'promotersAddress': data1.get('Street  Name'),
# #         'landownerTypes': None,
# #         'promoterPinCode': data1.get('Pin Code'),
# #         'longitude': None,
# #         'latitude': None,
# #         'viewLink': proj.get('View Details URL')
# #     }
# #
# #
# # def clean_text(t):
# #
# #     return t.replace('\xa0', ' ').strip() if t else None
# #
# # def extract_div_data(soup, cid):
# #     cont = soup.find("div", id=cid) or soup.find("fieldset", id=cid)
# #     if not cont:
# #         return {}
# #     data = {}
# #     for row in cont.find_all("div", class_="form-group"):
# #         labels = row.find_all("label")
# #         vals = row.find_all("div", class_="col-md-3 col-sm-3")
# #         for i, lbl in enumerate(labels):
# #             if len(vals) <= (1 if i == 0 else 3):
# #                 continue
# #             key = clean_text(lbl.get_text())
# #             val = clean_text(vals[1].get_text() if i == 0 else vals[3].get_text())
# #             if key and val:
# #                 data[key] = val
# #     return data
# #
# # def write_json_line(d: dict):
# #     with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
# #         f.write(json.dumps(d, ensure_ascii=False) + ",\n")
# #
# # def process_list_page(soup):
# #     rows = soup.select("table#projectTable tbody tr")
# #     projects = []
# #     for r in rows:
# #         tds = r.find_all("td")
# #         if len(tds) < 5:
# #             continue
# #         proj = {
# #             "Sr No.": tds[0].get_text(strip=True),
# #             "Project Name": tds[1].get_text(strip=True),
# #             "Promoter Name": tds[2].get_text(strip=True),
# #             "Last Modified Date": None,
# #             "View Details URL": BASE_URL + tds[3].find("a")['href']
# #         }
# #         projects.append(proj)
# #     return projects
# #
# # def process_project_detail(proj):
# #     resp = session.get(proj["View Details URL"], headers=HEADERS, verify=False)
# #     if resp.status_code != 200:
# #         print("Failed detail for", proj["Project Name"])
# #         return
# #     sp = BeautifulSoup(resp.text, 'html.parser')
# #     data = extract_div_data(sp, "DivProject")
# #     data1 = extract_div_data(sp, "fldind") or extract_div_data(sp, "fldFirm")
# #     proj["Last Modified Date"] = data.get("RERA Registration Date") or proj["Last Modified Date"]
# #     final = get_final_payload(proj, data, data1)
# #     print(final)
# #     # write_to_MargeFile(final)
# #
# #
# # # --- Main Flow ---
# # session.get(SEARCH_URL, headers=HEADERS, verify=False)
# # token = BeautifulSoup(session.get(SEARCH_URL, headers=HEADERS, verify=False).text, 'html.parser') \
# #     .find("input", {"name": "__RequestVerificationToken"})["value"]
# #
# # captcha_val = fetch_captcha_text()
# # print("Using CAPTCHA:", captcha_val)
# #
# # first_payload = {
# #     "__RequestVerificationToken": token,
# #     "Type": "Promoter",
# #     "ID": "0",
# #     "pageTraverse": "1",
# #     "RoleIDPageload": "1",
# #     "Project": "", "hdnProject": "",
# #     "Promoter": "", "hdnPromoter": "",
# #     "AgentName": "", "hdnAgent": "",
# #     "CertiNo": "", "hdnCertiNo": "",
# #     "District": "", "hdnDivision": "",
# #     "hdnDistrict": "", "hdnDTaluka": "",
# #     "hdnVillage": "", "hdnState": "",
# #     "Taluka": "", "Village": "",
# #     "CompletionDate_From": "", "hdnfromdate": "",
# #     "CompletionDate_To": "", "hdntodate": "",
# #     "PType": "", "hdnPType": "",
# #     "Captcha": captcha_val,
# #     "Command": "Search"
# # }
# #
# # resp = session.post(SEARCH_URL, headers=HEADERS, data=first_payload, verify=False)
# # sp = BeautifulSoup(resp.text, 'html.parser')
# # total_pages = int(sp.find("input", {"id": "TotalPages"})["value"])
# # print(f"Total pages: {total_pages}")
# #
# # # Process page 1
# # for proj in process_list_page(sp):
# #     process_project_detail(proj)
# #
# # # Process pages 2 to end
# # for page in range(2, total_pages + 1):
# #     token = BeautifulSoup(resp.text, 'html.parser') \
# #         .find("input", {"name": "__RequestVerificationToken"})["value"]
# #     next_payload = first_payload.copy()
# #     next_payload.update({
# #         "__RequestVerificationToken": token,
# #         "pageTraverse": "0",
# #         "Captcha": "",
# #         "Command": "Next",
# #         "CurrentPage": str(page),
# #         "TotalPages": str(total_pages)
# #     })
# #     resp = session.post(SEARCH_URL, headers=HEADERS, data=next_payload, verify=False)
# #     sp = BeautifulSoup(resp.text, 'html.parser')
# #     for proj in process_list_page(sp):
# #         process_project_detail(proj)
# #     time.sleep(0.5)


import time
import json
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import easyocr
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
from Scripts.write_to_txt_file import write_to_MargeFile

# --- Configuration ---
BASE_URL = "https://rerait.telangana.gov.in"
SEARCH_URL = f"{BASE_URL}/SearchList/Search"
CAPTCHA_URL = f"{BASE_URL}/SearchList/SearchCaptcha"
OUTPUT_FILE = r"D:\Rera_new_collection\New_Rera_telangana_333.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

session = requests.Session()
reader = easyocr.Reader(['en'], gpu=False)

# --- Utility Functions ---





def fetch_captcha_text():
    for attempt in range(5):
        resp = session.get(CAPTCHA_URL, headers=HEADERS, verify=False)
        if resp.status_code != 200:
            time.sleep(1)
            continue

        # Load image with PIL
        img = Image.open(BytesIO(resp.content))

        # Convert to grayscale
        img_gray = img.convert('L')

        # Convert PIL image to OpenCV format
        img_np = np.array(img_gray)

        # Apply binary thresholding to make text stand out
        _, img_thresh = cv2.threshold(img_np, 150, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Optional: apply dilation/erosion to clean noise
        kernel = np.ones((2, 2), np.uint8)
        img_clean = cv2.morphologyEx(img_thresh, cv2.MORPH_CLOSE, kernel)

        # Now run OCR on cleaned image
        result = reader.readtext(img_clean, detail=0)

        captcha_text = ''.join(result).strip() if result else ""

        print(f"[Attempt {attempt + 1}] OCR result: '{captcha_text}'")

        if captcha_text:
            return captcha_text

        time.sleep(1)

    raise ValueError("CAPTCHA recognition failed after 5 attempts")


def format_date(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return None


def get_final_payload(proj, data, data1):
    rera_date_raw = proj.get('Last Modified Date')
    rera_date = rera_date_raw.split()[0] if rera_date_raw else None
    return {
        'projectCin': None,
        'promoterCin': None,
        'projectName': proj.get('Project Name'),
        'promoterName': proj.get('Promoter Name'),
        'acknowledgementNumber': None,
        'projectRegistrationNo': data.get('Plan Approval Number'),
        'reraRegistrationDate': format_date(rera_date),
        'projectProposeCompletionDate': format_date(data.get('Proposed Date of Completion')),
        'projectStatus': data.get('Project Status'),
        'projectType': data.get('Project Type'),
        'promoterType': data1.get('Promoter Type'),
        'projectStateName': data.get('State'),
        'projectPinCode': data1.get('PIN Code'),
        'projectDistrictName': data.get('District'),
        'projectVillageName': data.get('Mandal'),
        'projectAddress': data.get('Plot No./House No.'),
        'totalLandArea': data.get('Total Area(In sqmts)'),
        'promotersAddress': data1.get('Street  Name'),
        'landownerTypes': None,
        'promoterPinCode': data1.get('Pin Code'),
        'longitude': None,
        'latitude': None,
        'viewLink': proj.get('View Details URL')
    }


def clean_text(t):
    return t.replace('\xa0', ' ').strip() if t else None


def extract_div_data(soup, cid):
    cont = soup.find("div", id=cid) or soup.find("fieldset", id=cid)
    if not cont: return {}
    data = {}
    for row in cont.find_all("div", class_="form-group"):
        labels = row.find_all("label")
        vals = row.find_all("div", class_="col-md-3 col-sm-3")
        for i, lbl in enumerate(labels):
            if len(vals) <= (1 if i == 0 else 3): continue
            key = clean_text(lbl.get_text())
            val = clean_text(vals[1].get_text() if i == 0 else vals[3].get_text())
            if key and val:
                data[key] = val
    return data


def write_json_line(d: dict):
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(d, ensure_ascii=False) + ",\n")


def process_list_page(soup):
    rows = soup.select("table#projectTable tbody tr")
    projects = []
    for r in rows:
        tds = r.find_all("td")
        if len(tds) < 5: continue
        proj = {
            "Sr No.": tds[0].get_text(strip=True),
            "Project Name": tds[1].get_text(strip=True),
            "Promoter Name": tds[2].get_text(strip=True),
            "Last Modified Date": None,  # will parse later if available
            "View Details URL": BASE_URL + tds[3].find("a")['href']
        }
        projects.append(proj)
    return projects


def process_project_detail(proj):
    resp = session.get(proj["View Details URL"], headers=HEADERS, verify=False)
    if resp.status_code != 200:
        print("Failed detail for", proj["Project Name"])
        return
    sp = BeautifulSoup(resp.text, 'html.parser')
    data = extract_div_data(sp, "DivProject")
    data1 = extract_div_data(sp, "fldind") or extract_div_data(sp, "fldFirm")
    proj["Last Modified Date"] = data.get("RERA Registration Date") or proj["Last Modified Date"]
    final = get_final_payload(proj, data, data1)
    print(final)
    # write_json_line(final)
    # print("Saved:", proj["projectName"])



def rera_Telangana():
    # --- Main Flow ---
    session.get(SEARCH_URL, headers=HEADERS, verify=False)
    token = BeautifulSoup(session.get(SEARCH_URL, headers=HEADERS, verify=False).text, 'html.parser') \
        .find("input", {"name": "__RequestVerificationToken"})["value"]
    captcha_val = fetch_captcha_text()
    print("CAPTCHA:", captcha_val)

    first_payload = {
        "__RequestVerificationToken": token,
        "Type": "Promoter",
        "ID": "0",
        "pageTraverse": "1",
        "RoleIDPageload": "1",
        "Project": "", "hdnProject": "",
        "Promoter": "", "hdnPromoter": "",
        "AgentName": "", "hdnAgent": "",
        "CertiNo": "", "hdnCertiNo": "",
        "District": "", "hdnDivision": "",
        "hdnDistrict": "", "hdnDTaluka": "",
        "hdnVillage": "", "hdnState": "",
        "Taluka": "", "Village": "",
        "CompletionDate_From": "", "hdnfromdate": "",
        "CompletionDate_To": "", "hdntodate": "",
        "PType": "", "hdnPType": "",
        "Captcha": captcha_val,
        "Command": "Search"
    }

    resp = session.post(SEARCH_URL, headers=HEADERS, data=first_payload, verify=False)
    sp = BeautifulSoup(resp.text, 'html.parser')
    total_pages = int(sp.find("input", {"id": "TotalPages"})["value"])
    print(f"Total pages: {total_pages}")

    # Process page 1
    for proj in process_list_page(sp):
        process_project_detail(proj)

    # Process pages 2 to end
    for page in range(2, total_pages + 1):
        token = BeautifulSoup(resp.text, 'html.parser') \
            .find("input", {"name": "__RequestVerificationToken"})["value"]
        next_payload = first_payload.copy()
        next_payload.update({
            "__RequestVerificationToken": token,
            "pageTraverse": "0",
            "Captcha": "",
            "Command": "Next",
            "CurrentPage": str(page),
            "TotalPages": str(total_pages)
        })
        resp = session.post(SEARCH_URL, headers=HEADERS, data=next_payload, verify=False)
        sp = BeautifulSoup(resp.text, 'html.parser')
        for proj in process_list_page(sp):
            process_project_detail(proj)
        time.sleep(0.5)


rera_Telangana()