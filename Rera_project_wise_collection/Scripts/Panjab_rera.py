import requests
import easyocr
from PIL import Image
from io import BytesIO
import numpy as np
from bs4 import BeautifulSoup
import time
from datetime import datetime
import json
from Scripts.write_to_txt_file import write_to_MargeFile

# def write_to_MargeFile(newline):
#     file_path = r"D:\\Rera_new_collection\\New_Rera_panjab.txt"
#     with open(file_path, 'a', encoding='utf-8') as text_file:
#         json_line = json.dumps(newline, ensure_ascii=False)
#         text_file.write(json_line)
#         text_file.write(",\n")

def convert_date_format(date_str):
    formats = [
        "%d-%m-%Y",
        "%B %d, %Y",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d-%b-%Y"  # Added this format for abbreviated month names
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def get_final_payload(data, ViewProjectDetail):
    project_data = {
        'projectCin': None,
        'promoterCin': None,
        'projectName': data.get('Project Name'),
        'promoterName': data.get('Promoter Name'),
        'acknowledgementNumber': None,
        'projectRegistrationNo': data.get('Registration Number'),
        'reraRegistrationDate': convert_date_format(ViewProjectDetail['Projects'].get('Project Start Date', None)),
        'projectProposeCompletionDate': convert_date_format(ViewProjectDetail['Projects'].get('Proposed/ Expected Date of Project Completion as specified in Form B', None)),
        'projectStatus': ViewProjectDetail['Projects'].get('Project Status', None),
        'projectType': ViewProjectDetail['Projects'].get('Type of Project', None),
        'promoterType': ViewProjectDetail['Promotors'].get('Type of Organization', None),
        'projectStateName': "Punjab",
        'projectPinCode': ViewProjectDetail['Projects'].get('Project Address', '').split('-')[-1].strip(),
        'projectDistrictName': data.get('District Name'),
        'projectVillageName': ViewProjectDetail['Projects'].get('Project Address', '').split(',')[0].strip(),
        'projectAddress': ViewProjectDetail['Projects'].get('Project Address', None),
        'totalLandArea': ViewProjectDetail['Projects'].get('Total Area of Land Proposed to be developed (in sqr mtrs)', None),
        'promotersAddress': ViewProjectDetail['Promotors'].get('Registered Address of Organization', None),
        'landownerTypes': None,
        'promoterPinCode': ViewProjectDetail['Promotors'].get('Registered Address of Organization', '').split('-')[-1].strip(),
        'longitude': None,
        'latitude': None,
        'viewLink': f"https://rera.punjab.gov.in/reraindex/PublicView/ProjectViewDetails?inProject_ID={data.get('Project ID')}&inPromoter_ID={data.get('Promoter ID')}&inPromoterType={data.get('Promoter Type')}",
    }
    return project_data


# Initialize a session
session = requests.Session()

# Set common headers
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "origin": "https://rera.punjab.gov.in",
    "referer": "https://rera.punjab.gov.in/reraindex/publicview/projectinfo",
    "x-requested-with": "XMLHttpRequest",
}

def fetch_captcha_and_solve():
    """Fetches CAPTCHA from the website and extracts text using EasyOCR."""
    captcha_url = "https://rera.punjab.gov.in/reraindex/publicview/FileView_ProjectNumberImageCpacha"
    reader = easyocr.Reader(['en'])

    for _ in range(5):  # Retry up to 5 times
        try:
            response = session.get(captcha_url, headers=headers)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                # image.show()
                image_np = np.array(image)
                result = reader.readtext(image_np, detail=0)
                if result:
                    captcha_text = ''.join(result).strip()
                    print(f"Extracted CAPTCHA: {captcha_text}")
                    return captcha_text
                else:
                    print("No text found in the CAPTCHA. Retrying...")
            else:
                print(f"Failed to fetch CAPTCHA. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error processing CAPTCHA: {e}")
        time.sleep(1)  # Wait before retrying
    return None

def get_request_verification_token():
    """Extracts __RequestVerificationToken from the main page."""
    page_url = "https://rera.punjab.gov.in/reraindex/publicview/projectinfo"
    try:
        response = session.get(page_url, headers=headers)
        if response.status_code == 200:
            token_start = response.text.find("__RequestVerificationToken")
            if token_start != -1:
                token_value_start = response.text.find('value="', token_start) + len('value="')
                token_value_end = response.text.find('"', token_value_start)
                token = response.text[token_value_start:token_value_end]
                print(f"Extracted __RequestVerificationToken: {token}")
                return token
        print("Failed to extract __RequestVerificationToken.")
    except Exception as e:
        print(f"Error fetching verification token: {e}")
    return None

def clean_text(text):
    return " ".join(text.replace("\r\n", " ").strip().split())

def extract_table_data(postsoup,table_id):
    table = postsoup.find("div", id=table_id)
    if not table:
        return None
    data = {}
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) == 2:  # Single key-value pair
            key = clean_text(cols[0].get_text(strip=True))
            value = clean_text(cols[1].get_text(strip=True))
            data[key] = value
        elif len(cols) == 4:  # Two key-value pairs in one row
            key1 = clean_text(cols[0].get_text(strip=True))
            value1 = clean_text(cols[1].get_text(strip=True))
            key2 = clean_text(cols[2].get_text(strip=True))
            value2 = clean_text(cols[3].get_text(strip=True))
            data[key1] = value1
            data[key2] = value2
    return data



def submit_request(captcha_text, verification_token):
    """Submits the form using the extracted CAPTCHA and verification token."""
    url = "https://rera.punjab.gov.in/reraindex/PublicView/ProjectPVregdprojectInfo"

    for attempt in range(5):  # Retry up to 5 times if rows are empty
        print(f"Attempt {attempt + 1}...")
        # Define the form data
        data = {
            "__RequestVerificationToken": verification_token,
            "Input_SearchOptionTabFlag": "1",
            "Input_AdvSearch_MoreOptionsFlag": "1",
            "Input_RegdProject_PromoterName": "Ltd",
            "Input_RegdProject_CaptchaText": captcha_text,
            "Input_GeoTagging_TypeOfProject": "AL",
            "Input_AdvSearch_OptionTypeName": "REG",
            "Input_AdvSearch_TypeOfProject": "AL",
            "Input_MoreOptions_MegaProjectCategory": "NA",
            "dataTableSearchProject_length": "10",
            "dataTableSearchQUpdatesProject_length": "10",
        }

        # Send the POST request
        response = session.post(url, headers=headers, data=data)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.select("tbody tr")

            if rows:
                print("Request successful!")
                datas = []
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 7:
                        project_name_tag = cols[2].find("input", {"class": "hdnProjectID"})
                        promoter_id_tag = cols[2].find("input", {"class": "hdnPromoterID"})
                        promoter_type_tag = cols[2].find("input", {"class": "hdnPromoterType"})
                        cert_link_tag = cols[6].find("a", href=True)

                        datas.append({
                            "SNo": cols[0].text.strip(),
                            "District Name": cols[1].text.strip(),
                            "Project Name": cols[2].get("data-project-name", "").strip(),
                            "Promoter Name": cols[3].text.strip(),
                            "Registration Number": cols[4].get("data-diary-no", "").strip(),
                            "Valid Upto Date": cols[5].text.strip(),
                            "Project ID": project_name_tag["value"] if project_name_tag else "",
                            "Promoter ID": promoter_id_tag["value"] if promoter_id_tag else "",
                            "Promoter Type": promoter_type_tag["value"] if promoter_type_tag else "",
                            "Certificate Link": cert_link_tag["href"].replace("\\", "/") if cert_link_tag else ""
                        })
                for item in datas:
                    # print(item)
                    posturl = "https://rera.punjab.gov.in/reraindex/PublicView/ProjectViewDetails"

                    # Define headers
                    postheaders = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
                    }

                    # Define query parameters
                    params = {
                        "inProject_ID": item['Project ID'],
                        "inPromoter_ID": item['Promoter ID'],
                        "inPromoterType": item['Promoter Type']
                    }

                    # Send a GET request with parameters
                    res = requests.get(posturl, headers=postheaders, params=params)

                    # Print the response
                    postsoup = BeautifulSoup(res.text, "html.parser")
                    result = {
                        "Projects": extract_table_data(postsoup,"Projects"),
                        "Promotors": extract_table_data(postsoup,"Promoter")
                    }

                    finaldata = get_final_payload(item,result)
                    print(finaldata)
                    write_to_MargeFile(finaldata,"Panjab")
                # return datas
            else:
                print("No data found, possibly due to incorrect CAPTCHA. Retrying...")
        else:
            print(f"Request failed with status code {response.status_code}")
        time.sleep(1)



def rera_punjab():
    # Execute the steps with retry logic
    verification_token = get_request_verification_token()
    if verification_token:
        for _ in range(5):  # Retry up to 5 times for CAPTCHA

            captcha_text = fetch_captcha_and_solve()
            if captcha_text:
                submit_request(captcha_text, verification_token)
                break
            print("Incorrect CAPTCHA, retrying...")
            time.sleep(1)
    else:
        print("Failed to obtain verification token.")


