import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
from Scripts.write_to_txt_file import write_to_MargeFile



# def write_to_MargeFile(newline):
#     file_path = r"D:\\Rera_new_collection\\New_tamil_nadu_rera.txt"
#     with open(file_path, 'a', encoding='utf-8') as text_file:
#         json_line = json.dumps(newline, ensure_ascii=False)
#         text_file.write(json_line)
#         text_file.write(",\n")


def convert_date_format(date_str):
    for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except:
            continue
    return None


def final_payload(project_data_1, project_data_2, project_data_3):
    reg_date = convert_date_format(project_data_1.get('registration_date'))
    comp_date = convert_date_format(project_data_2.get('Project Completion Date'))

    return {
        'projectCin': None,
        'promoterCin': None,
        'projectName': None if project_data_2.get('Project Name') == "" else project_data_2.get('Project Name'),
        'promoterName': project_data_3.get('Firm Name'),
        'acknowledgementNumber': None,
        'projectRegistrationNo': project_data_1.get('registration_no'),
        'reraRegistrationDate': reg_date,
        'projectProposeCompletionDate': comp_date,
        'projectStatus': project_data_2.get('Stage of Construction'),
        'projectType': project_data_2.get('Usage'),
        'promoterType': project_data_3.get('Type of Promoter'),
        'projectStateName': "Tamil Nadu",
        'projectPinCode': None,
        'projectDistrictName': None,
        'projectVillageName': None,
        'projectAddress': project_data_2.get('Address'),
        'totalLandArea': project_data_2.get('Site Extent(Sq.m)'),
        'promotersAddress': project_data_3.get('Address'),
        'landownerTypes': None,
        'promoterPinCode': None,
        'longitude': project_data_2.get('Longitude'),
        'latitude': project_data_2.get('Latitude'),
        'viewLink': project_data_1.get('project_details_link'),
    }


def get_promoter_details(prom_url):
    response = requests.get(prom_url, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    promoter_details = {}

    form_sections = soup.find_all('div', class_='form_sec')
    for section in form_sections:
        for group in section.find_all('div', class_='form-group'):
            labels = group.find_all('div', recursive=False)
            if len(labels) >= 2:
                key_tag = labels[0].find(['p1', 'p'])
                value_tag = labels[1].find(['p', 'label'])
                if key_tag and value_tag:
                    key = key_tag.get_text(strip=True).replace(" :", "")
                    value = value_tag.get_text(strip=True)
                    promoter_details[key] = value
    return promoter_details


def get_project_details(project_url):
    response = requests.get(project_url, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    project_details = {}

    form_sections = soup.find_all('div', class_='form_sec')
    for section in form_sections:
        for group in section.find_all('div', class_='form-group'):
            labels = group.find_all('div', recursive=False)
            if len(labels) >= 2:
                key_tag = labels[0].find(['p1', 'p'])
                value_tag = labels[1].find(['p', 'label'])
                if key_tag and value_tag:
                    key = key_tag.get_text(strip=True).replace(" :", "")
                    value = value_tag.get_text(strip=True)
                    project_details[key] = value

    keys = [
        'Project Name', 'Site Extent(Sq.m)', 'Project Completion Date', 'Latitude',
        'Longitude', 'Planning Permission Approval / Renewal Date', 'Address',
        'Usage', 'Stage of Construction'
    ]
    return {key: project_details.get(key, '') for key in keys}


def extract_main_table_data(soup):
    table = soup.find('table', {'id': 'example1'})
    if not table:
        print("No table found")
        return []

    rows = table.find('tbody').find_all('tr')
    print(f"Found {len(rows)} projects")
    all_data = []

    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 8:
            continue

        reg_info = cols[1].get_text(separator=' ').strip().split("dated")
        registration_no = reg_info[0].strip()
        registration_date = reg_info[1].strip() if len(reg_info) > 1 else None

        project_name_line = cols[3].decode_contents().split('<br>')[0]
        project_name = project_name_line.replace('Project Name:', '').strip()

        location_text = cols[6].get_text()
        lat = long = None
        if 'Latitude' in location_text and 'Longitude' in location_text:
            try:
                lat = location_text.split('Latitude-')[1].split(';')[0].strip()
                long = location_text.split('Longitude-')[1].split(';')[0].strip()
            except:
                pass

        links = cols[6].find_all('a')
        promoter_link = links[0]['href'] if len(links) > 0 else None
        project_link = links[1]['href'] if len(links) > 1 else None

        main_data = {
            "s_no": int(cols[0].text.strip()),
            "registration_no": registration_no,
            "registration_date": registration_date,
            "promoter": cols[2].text.strip(),
            "project_name": project_name,
            "project_details": cols[3].get_text(separator=' ').replace(project_name_line, '').strip(),
            "approval_details": cols[4].text.strip(),
            "project_completion_date": cols[5].text.strip(),
            "promoter_details_link": promoter_link,
            "project_details_link": project_link,
            "location": {"latitude": lat, "longitude": long},
            "current_status": cols[7].text.strip()
        }

        project_details = get_project_details(project_link) if project_link else {}
        promoter_details = get_promoter_details(promoter_link) if promoter_link else {}

        final_data = final_payload(main_data, project_details, promoter_details)
        write_to_MargeFile(final_data,"TamilNadu")
        # all_data.append(final_data)
    # return all_data


def rera_tamil_nadu():
    base_url = "https://rera.tn.gov.in/registered-building/tn"
    session = requests.Session()

    # Initial GET for 2025
    print("Fetching 2025 data...")
    get_response = session.get(base_url, verify=False)
    soup = BeautifulSoup(get_response.text, "html.parser")
    extract_main_table_data(soup)

    # Extract _token
    token_input = soup.find('input', {'name': '_token'})
    if not token_input:
        print("Token not found")
        return
    token = token_input.get('value')

    # For 2024 and 2023
    for year in ['2024', '2023']:
        print(f"Fetching {year} data...")
        payload = {'_token': token, 'year': year}
        post_response = session.post(base_url, data=payload, verify=False)
        soup = BeautifulSoup(post_response.text, "html.parser")
        extract_main_table_data(soup)
        # all_results.extend(year_results)



# Run it
# rera_tamil_nadu()
