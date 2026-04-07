import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json, csv, os
from datetime import datetime
from Scripts.write_to_txt_file import write_to_MargeFile



def convert_date_format(date_str):
    return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")


def final_data(extracted_data):
    if extracted_data['project_information'].get('actual_start_date'):
        reraRegistrationDate =  convert_date_format(extracted_data['project_information'].get('actual_start_date'))
    else:
        reraRegistrationDate = None

    if extracted_data['project_information'].get('proposed_end_date') :
        projectProposeCompletionDate = convert_date_format(extracted_data['project_information'].get('proposed_end_date'))
    else:
        projectProposeCompletionDate = None

    final_payload = {
        'projectCin': None,
        'promoterCin': None,
        'projectName': extracted_data['project_information'].get('project_name'),
        'promoterName': extracted_data['promoter_information'].get('name'),
        'acknowledgementNumber':None,
        'projectRegistrationNo': extracted_data['project_information'].get('rera_registration_number'),
        'reraRegistrationDate': reraRegistrationDate,
        'projectProposeCompletionDate': projectProposeCompletionDate,
        'projectStatus': extracted_data['project_information'].get('application_status'),
        'projectType': extracted_data['project_information'].get('project_type'),
        'promoterType': extracted_data['promoter_information'].get('applicant_type'),
        'projectStateName': extracted_data['project_location'].get('state'),
        'projectPinCode': None,
        'projectDistrictName': extracted_data['project_location'].get('district'),
        'projectVillageName': None,
        'projectAddress': extracted_data['project_location'].get('project_address'),
        'totalLandArea': None,
        'promotersAddress': extracted_data['promoter_information'].get('address'),
        'landownerTypes': None,
        'promoterPinCode': None,
        'longitude': None,
        'latitude': None,
        'viewLink': extracted_data['viewLink']
    }

    return final_payload


def extract_project_details(detail_url, base_url, headers):
    """Extract project details by identifying specific sections based on content categories."""
    full_url = urljoin(base_url, detail_url)
    response = requests.get(full_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    project_data = {
        "project_information": {},
        "project_location": {},
        "promoter_information": {}
    }

    sections = {
        "Project Information": "project_information",
        "Project Location": "project_location",
        "Promoter Information": "promoter_information"
    }

    # Iterate over each section title and collect data
    for section_name, section_key in sections.items():
        section_div = soup.find("div", string=section_name)
        if section_div:
            parent_div = section_div.find_parent("div")
            rows = parent_div.find_all("div", class_="row")
            for row in rows:
                cols = row.find_all("div")
                if len(cols) >= 2:
                    key = cols[0].get_text(strip=True).replace(":", "").strip()
                    value = cols[1].get_text(strip=True)
                    key = key.lower().replace(" ", "_").replace("-", "_")
                    project_data[section_key][key] = value

    # Extract company registration document link
    promoter_box = soup.find("div", class_="box")
    if promoter_box:
        doc_link = promoter_box.find("a", href=True)
        if doc_link:
            project_data["promoter_information"]["company_registration_document"] = urljoin(base_url, doc_link["href"])

    return project_data


def rera_mp():
    base_url = "https://www.rera.mp.gov.in/"
    search_url = urljoin(base_url, "projectsrcg-loop.php")
    # search_txts = ["Ltd", "Limited", "Llp"]
    params = {
        "show": "20",
        "pagenum": "1",
        "search_txt": "",
        "search_dist": "",
        "search_tehs": "undefined",
        "project_type_id": "",
        "_": "1743762678646"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    project_list = []

    # for search_txt in search_txts:
    #     params["search_txt"] = search_txt
    response = requests.get(search_url, headers=headers, params=params)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table")
    if table:
        for row in table.find("tbody").find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 7:
                project_name = cols[1].text.strip()
                registration_number = cols[4].text.strip()
                link_tag = cols[-1].find("a")
                detail_url = link_tag["href"] if link_tag else None

                if detail_url:
                    project_data = extract_project_details(detail_url, base_url, headers)
                    project_data["project_information"]["project_name"] = project_name
                    project_data["project_information"]["rera_registration_number"] = registration_number
                    project_data["viewLink"] = detail_url

                    data = final_data(project_data)
                    print(data)
                    write_to_MargeFile(data,"MP")

    # for project in project_list:
    #
    #     data = final_data(project)
    #     print(data)
    #     write_to_MargeFile(data)
    #     print("=" * 100)


# rera_mp()
