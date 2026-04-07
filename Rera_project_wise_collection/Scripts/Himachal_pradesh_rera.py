import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
import re
from  Scripts.write_to_txt_file import write_to_MargeFile


# def write_to_MargeFile(newline):
#     file_path = r"D:\\Rera_new_collection\\New_Rera_Himachal_pradesh.txt"
#     with open(file_path, 'a', encoding='utf-8') as text_file:
#         json.dump(newline, text_file, ensure_ascii=False)
#         text_file.write(",\n")


def convert_date_format(date_str):
    try:
        # Handle date like 22/01/2024
        return datetime.strptime(date_str.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return None


def extract_pincode(address):
    if not address:
        return None
    match = re.search(r'(\d{6})', address)
    if match:
        return match.group(1)
    return None


def final_payload(project, project_details, promoter_data):
    start_date = project.get('updated_date')
    if start_date:
        start_date = convert_date_format(start_date)

    end_date = project.get('valid_upto')
    if end_date:
        end_date = convert_date_format(end_date)
    return {
        'projectCin': None,
        'promoterCin': None,
        'projectName': project.get('project_name') or project_details.get('Name of Real Estate Project'),
        'promoterName': promoter_data.get('Name'),
        'acknowledgementNumber': None,
        'projectRegistrationNo': project.get('rera_no') or promoter_data.get('Registration No.'),
        'reraRegistrationDate': start_date,
        'projectProposeCompletionDate': end_date,
        'projectStatus': project_details.get('Project Status'),
        'projectType': project_details.get('Project Type') or project.get('project_type'),
        'promoterType': promoter_data.get('Promoter Type'),
        'projectStateName': 'Himachal Pradesh',
        'projectPinCode': extract_pincode(project_details.get('Address')) if project_details.get('Address') else None,
        'projectDistrictName': project_details.get('Tehsil'),
        'projectVillageName': project_details.get('Mohal/Mauza No.'),
        'projectAddress': project.get('address') or project_details.get('Address'),
        'totalLandArea': project_details.get('Total Land Area'),
        'promotersAddress': promoter_data.get('Permanent Address'),
        'landownerTypes': None,
        'promoterPinCode': extract_pincode(promoter_data.get('Permanent Address')) if promoter_data.get(
            'Permanent Address') else None,
        'longitude': project_details.get('Longitude'),
        'latitude': project_details.get('Latitude'),
        'viewLink': "https://hprera.nic.in/PublicDashboard",
    }


def get_project_details(qs_token):
    url = f"https://hprera.nic.in/Project/ProjectRegistration/ProjectDetails_PreviewPV?qs={qs_token}&UpdatedChangeDets=Y"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Referer": "https://hprera.nic.in/PublicDashboard",
        "X-Requested-With": "XMLHttpRequest",
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    project_data = {}

    # Locate the table
    table = soup.find('table', class_="table table-bordered table-responsive-lg table-striped table-sm font-sm")

    if table:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)
                project_data[key] = value

    return project_data


def get_promotor_details(qs_token):
    url = f"https://hprera.nic.in/Project/ProjectRegistration/PromotorDetails_PreviewPV?qs={qs_token}&UpdatedChangeDets=N"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Referer": "https://hprera.nic.in/PublicDashboard",
        "X-Requested-With": "XMLHttpRequest",
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    data = {}

    # Locate the table
    table = soup.find('table', class_="table table-borderless table-sm table-responsive-lg table-striped font-sm")

    if table:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)
                data[key] = value

    return data


def fetch_hprera_projects(search_text):
    url = "https://hprera.nic.in/PublicDashboard/GetFilteredProjectsPV"

    params = {
        "DistrictList[0].Selected": "false", "DistrictList[0].Value": "18",
        "DistrictList[1].Selected": "false", "DistrictList[1].Value": "24",
        "DistrictList[2].Selected": "false", "DistrictList[2].Value": "20",
        "DistrictList[3].Selected": "false", "DistrictList[3].Value": "23",
        "DistrictList[4].Selected": "false", "DistrictList[4].Value": "25",
        "DistrictList[5].Selected": "false", "DistrictList[5].Value": "22",
        "DistrictList[6].Selected": "false", "DistrictList[6].Value": "26",
        "DistrictList[7].Selected": "false", "DistrictList[7].Value": "21",
        "DistrictList[8].Selected": "false", "DistrictList[8].Value": "15",
        "DistrictList[9].Selected": "false", "DistrictList[9].Value": "17",
        "DistrictList[10].Selected": "false", "DistrictList[10].Value": "16",
        "DistrictList[11].Selected": "false", "DistrictList[11].Value": "19",

        "PlottedTypeList[0].Selected": "false", "PlottedTypeList[0].Value": "P",
        "PlottedTypeList[1].Selected": "false", "PlottedTypeList[1].Value": "F",
        "PlottedTypeList[2].Selected": "false", "PlottedTypeList[2].Value": "M",

        "ResidentialTypeList[0].Selected": "false", "ResidentialTypeList[0].Value": "R",
        "ResidentialTypeList[1].Selected": "false", "ResidentialTypeList[1].Value": "C",
        "ResidentialTypeList[2].Selected": "false", "ResidentialTypeList[2].Value": "M",

        "AreaFrom": "",
        "AreaUpto": "",
        "SearchText": search_text
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://hprera.nic.in/PublicDashboard"
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        try:

            data = response.text

            soup = BeautifulSoup(data, 'html.parser')

            projects = []

            for div in soup.select('div.col-lg-6 > div.shadow'):
                project = {}

                # Search only within this div
                updated_span = div.find('span', string="Updated on:")

                updated_date = None
                if updated_span and updated_span.next_sibling:
                    updated_date = updated_span.next_sibling.strip()

                project['updated_date'] = updated_date
                # Project Name
                name_tag = div.select_one('span.font-lg')
                project['project_name'] = name_tag.get_text(strip=True) if name_tag else None

                # RERA Number + href (data-qs)
                a_tag = div.select_one('a[onclick*="ApplicationPreview"]')
                project['rera_no'] = a_tag.get_text(strip=True) if a_tag else None
                project['rera_href'] = a_tag['data-qs'] if a_tag and 'data-qs' in a_tag.attrs else None

                # Project Type
                type_tag = a_tag.find_next_sibling(text=True)
                project['project_type'] = type_tag.strip() if type_tag else None

                # Mobile
                mobile_tag = div.select_one('i.fa-mobile-alt + span.ml-1')
                project['mobile'] = mobile_tag.get_text(strip=True) if mobile_tag else None

                # Email
                email_tag = div.select_one('i.fa-at + span.ml-1')
                project['email'] = email_tag.get_text(strip=True) if email_tag else None

                # Address
                addr_tag = div.select_one('i.fa-map-marker-alt + span.ml-1')
                project['address'] = addr_tag.get_text(strip=True) if addr_tag else None

                # Valid Upto
                valid_tag = div.select_one('div.text-right span.text-orange')
                project['valid_upto'] = valid_tag.get_text(strip=True) if valid_tag else None

                project_data = get_project_details(project['rera_href'])

                promoter_data = get_promotor_details(project['rera_href'])

                print("======" * 50)
                final_data = final_payload(project, project_data, promoter_data)
                print(final_data)
                write_to_MargeFile(final_data,"Himachal_pradesh")

        except Exception as e:
            print("Error parsing data:", e)
    else:
        print(f"Request failed: {response.status_code}")


def rera_himachal_pradesh():

    search_texts = ["Ltd", "Limited", "Llp"]
    for search_text in search_texts:
        fetch_hprera_projects(search_text)
