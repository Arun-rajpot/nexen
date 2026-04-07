import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
from Scripts.write_to_txt_file import write_to_MargeFile

# def write_to_MargeFile(newline):
#     file_path = r"D:\\Rera_new_collection\\New_jharkhand_rera.txt"
#     with open(file_path, 'a', encoding='utf-8') as text_file:
#         json_line = json.dumps(newline, ensure_ascii=False)
#         text_file.write(json_line)
#         text_file.write(",\n")


def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except:
        return None

def get_final_payload(data, ViewProjectDetail):
    reraRegistrationDate = convert_date_format(ViewProjectDetail.get('Permit valid From'))
    projectProposeCompletionDate = convert_date_format(ViewProjectDetail.get('Permit valid To'))

    project_data = {
        'projectCin': None,
        'promoterCin': None,
        'projectName': data.get('project_name'),
        'promoterName': ViewProjectDetail.get('Builder Details'),
        'acknowledgementNumber': None,
        'projectRegistrationNo': data.get('reg_no_date'),
        'reraRegistrationDate': reraRegistrationDate,
        'projectProposeCompletionDate': projectProposeCompletionDate,
        'projectStatus': None,
        'projectType': ViewProjectDetail.get('Project Type'),
        'promoterType': None,
        'projectStateName': "Jharkhand",
        'projectPinCode': None,
        'projectDistrictName': None,
        'projectVillageName': None,
        'projectAddress': ViewProjectDetail.get('Project Address') or data.get('address'),
        'totalLandArea': None,
        'promotersAddress': ViewProjectDetail.get('Promoter Address'),
        'landownerTypes': None,
        'promoterPinCode': None,
        'longitude': None,
        'latitude': None,
        'viewLink': f"https://jharera.jharkhand.gov.in{data.get('profile_url')}",
    }

    return project_data

def clean_text(text):
    return text.replace('\xa0', ' ').strip() if text else None

def extract_div_data(postsoup):
    data = {}
    rows = postsoup.find_all("div", class_="form-group")
    for row in rows:
        labels = row.find_all("label")
        if len(labels) >= 2:
            label_text = clean_text(labels[0].get_text(strip=True))
            value_parts = []
            for lbl in labels[1:]:
                text = clean_text(lbl.get_text(strip=True))
                if text is not None:
                    value_parts.append(str(text))  # Ensure it's string

            value_text = " ".join(value_parts)
            if label_text and value_text:
                data[label_text] = value_text
    return data

def rera_jharkhand():
    page = 1
    while True:
        print("======page=====",page)
        print(f"Processing page {page}...")
        url = f'https://jharera.jharkhand.gov.in/Home/OnlineRegisteredProjectsList?page={page}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find('table', class_="table")

        if not table:
            break

        rows = table.find_all('tr')[1:]  # Skip header
        if not rows:
            break

        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 6:
                sl_no = cols[0].get_text(strip=True)
                reg_no_date = cols[1].get_text(strip=True)
                project_name = cols[2].get_text(strip=True)
                address = cols[3].get_text(separator=' ', strip=True)
                location_url = cols[4].find('a')['href'] if cols[4].find('a') else None
                profile_url = cols[5].find('a')['href'] if cols[5].find('a') else None

                data_list = {
                    "sl_no": sl_no,
                    "reg_no_date": reg_no_date,
                    "project_name": project_name,
                    "address": address,
                    "location_url": location_url,
                    "profile_url": profile_url
                }

                detail_url = 'https://jharera.jharkhand.gov.in' + profile_url
                detail_resp = requests.get(detail_url)
                detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
                datatag = extract_div_data(detail_soup)

                final_data = get_final_payload(data_list, datatag)
                print(final_data)
                write_to_MargeFile(final_data,"Jharkhand")
                print("========================================")
        page += 1

# Run the scripta
# jharkhand_rera()
