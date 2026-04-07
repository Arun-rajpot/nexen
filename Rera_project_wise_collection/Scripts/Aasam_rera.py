import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
from Scripts.write_to_txt_file import write_to_MargeFile

def extract_number(text):
    if text:
        match = re.search(r"[\d.,]+", text)
        if match:
            return match.group(0)
    return None

def clean(text):
    return text.strip() if text else None

def convert_to_iso(date_str):
    try:
        return datetime.strptime(date_str.strip(), "%d-%m-%Y").date().isoformat()
    except Exception:
        return None

def convert_url(search_url):
    if "/searchprojectDetail/" in search_url:
        project_id = search_url.rstrip('/').split('/')[-1]
        new_url = f"https://rera.assam.gov.in/view_project/project_preview_open/{project_id}"
        return new_url
    else:
        raise ValueError("URL format is invalid or does not contain /searchprojectDetail/")

def fetch_left_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        data = {}

        # Helper: find label allowing <br> and nested
        def find_label_by_text(label_text):
            labels = soup.find_all('label')
            for lbl in labels:
                if label_text in lbl.get_text(separator=" ", strip=True):
                    return lbl
            return None

        # Extract Temp Project Id, Applicant Type, Project Type
        b_tags = soup.find_all('b')
        for b in b_tags:
            text = b.get_text(strip=True)
            if ':' in text:
                key, val = text.split(':', 1)
                key = key.strip()
                val = val.strip()
                if key in ['Temp Project Id', 'Applicant Type', 'Project Type']:
                    data[key] = val

        # Firm Name
        label_firm = find_label_by_text('1. Name')
        if label_firm:
            tr = label_firm.find_parent('tr')
            if tr:
                b_tags = tr.find_all('b')
                if b_tags:
                    data['promoterName'] = b_tags[-1].get_text(strip=True)

        # Firm Address
        label_addr = find_label_by_text('2. Address of the firm for correspondence')
        if label_addr:
            tr = label_addr.find_parent('tr')
            if tr:
                b_tags = tr.find_all('b')
                if b_tags:
                    data['promoterAddress'] = b_tags[-1].get_text(strip=True)

        # Land Area
        def get_value_by_label(label_text):
            label = find_label_by_text(label_text)
            if label:
                tr = label.find_parent('tr')
                if tr:
                    b_tag = tr.find('b')
                    if b_tag:
                        return b_tag.get_text(strip=True)
            return None

        raw_land_area = get_value_by_label('1. Land area')
        data['Land_Area'] = extract_number(raw_land_area)

        return data
    else:
        print(f"Failed to fetch the URL {url}. Status code:", response.status_code)
        return {}


def get_promoter_from_table(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    tr = soup.find('table', id='table').find('tbody').find('tr')
    promoter = tr.find_all('td')[4].get_text(strip=True)
    current_status = None
    tables = soup.find_all("table")
    for table in tables:
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if "current status" in headers:
            status_index = headers.index("current status")
            tbody = table.find("tbody")
            if tbody:
                tr = tbody.find("tr")
                if tr:
                    tds = tr.find_all("td")
                    current_status = tds[status_index].get_text(strip=True)
            break

    return promoter, current_status

# ============== MAIN SCRAPING START ==============
def rera_Aasam():
    url = "https://rera.assam.gov.in/admincontrol/registered_projects/1"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', id='compliant_hearing')

    # projects = []

    if table:
        rows = table.tbody.find_all('tr')
        for tr in rows:
            cols = tr.find_all('td')
            if len(cols) > 2:
                a_tag = cols[2].find('a')
                if a_tag and a_tag.has_attr('href'):
                    project_url = convert_url(a_tag['href'])
                    left_data = fetch_left_data(project_url)
                    promotor_name , status = get_promoter_from_table(a_tag['href'])
                    project = {
                        'projectCin': None,
                        'promoterCin': None,
                        'projectName': (clean(cols[3].text) if len(cols) > 3 else None).title(),
                        'promoterName': promotor_name,
                        'acknowledgementNumber': None,
                        'projectRegistrationNo': left_data.get('Temp Project Id'),
                        'reraRegistrationDate': convert_to_iso(cols[14].text),
                        'projectProposeCompletionDate': convert_to_iso(cols[15].text),
                        'projectStatus': status,
                        'projectType': left_data.get('Project Type'),
                        'promoterType': left_data.get('Applicant Type'),
                        'projectStateName': 'Assam',
                        'projectPinCode': None,
                        'projectDistrictName': (clean(cols[6].text) if len(cols) > 6 else None).title(),
                        'projectVillageName': None,
                        'projectAddress': (clean(cols[5].text.replace('\n', ', ')) if len(cols) > 5 else None).title(),
                        'totalLandArea': left_data.get('Land_Area'),
                        'promotersAddress': clean(left_data.get('promoterAddress')).title() if left_data.get('promoterAddress') else None,
                        'landownerTypes': None,
                        'promoterPinCode': None,
                        'longitude': None,
                        'latitude': None,
                        'viewLink': project_url
                    }
                    print(project)
                    write_to_MargeFile(project,"Aasam")
                # projects.append(project)


# rera_Aasam()

# Save to file
# with open("real_main_data.txt", "w", encoding="utf-8") as f:
#     for project in projects:
#         json.dump(project, f, ensure_ascii=False)
#         f.write("\n")
#
# print(f"Total projects scraped: {len(projects)}")
# print("Data saved to real_main_data.txt")
