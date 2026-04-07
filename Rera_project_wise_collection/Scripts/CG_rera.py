import requests
import re
import json
import html
from bs4 import BeautifulSoup
import urllib3
from Scripts.write_to_txt_file import write_to_MargeFile
from dateutil import parser

def convert_to_yyyy_mm_dd(date_str):
    try:
        parsed_date = parser.parse(date_str, dayfirst=True)
        return parsed_date.strftime('%Y-%m-%d')
    except Exception as e:
        return f"Invalid date format: {e}"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://rera.cgstate.gov.in/"
URL = f"{BASE_URL}Approved_project_List.aspx"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def extract_rera_data_from_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://rera.cgstate.gov.in/",
        "Cookie": "",  # Add if needed
    }
    response = requests.get(url, headers=headers, timeout=20, verify=False)
    soup = BeautifulSoup(response.content, 'html.parser')

    fields = [
        'projectCin', 'promoterCin', 'projectName', 'promoterName', 'acknowledgementNumber', 'projectRegistrationNo',
        'reraRegistrationDate', 'projectProposeCompletionDate', 'projectStatus', 'projectType', 'promoterType',
        'projectStateName', 'projectPinCode', 'projectDistrictName', 'projectVillageName', 'projectAddress',
        'totalLandArea', 'promotersAddress', 'landownerTypes', 'promoterPinCode', 'longitude', 'latitude', 'viewLink'
    ]

    data = {}
    null_fields = []

    for field in fields:
        value = None

        # Special fields
        if field == 'projectRegistrationNo':
            span = soup.find('span', {'id': 'ContentPlaceHolder1_AppReferenceNo'})
            if span:
                value = span.text.strip().replace('[ Registration No : ', '').replace(' ]', '')

        elif field == 'projectName':
            input_tag = soup.find('input', {'id': 'ContentPlaceHolder1_txt_proj_name'})
            if input_tag:
                value = input_tag.get('value', '').strip()

        elif field == 'promoterName':
            input_tag = soup.find('input', {'id': 'ContentPlaceHolder1_txt_p_name'})
            if input_tag:
                value = input_tag.get('value', '').strip()

        elif field == 'projectStatus':
            input_tag = soup.find('input', {'id': 'ContentPlaceHolder1_ApplicantType'})
            if input_tag:
                value = input_tag.get('value', '').strip()

        elif field == 'promoterType':
            select_tag = soup.find('select', {'id': 'ContentPlaceHolder1_txt_p_type'})
            if select_tag:
                selected_option = select_tag.find('option', selected=True)
                if selected_option:
                    value = selected_option.text.strip()

        elif field == 'projectType':
            input_tag = soup.find('input', {'id': 'ContentPlaceHolder1_DropDownList5'})
            if input_tag:
                value = input_tag.get('value', '').strip()

        elif field == 'projectProposeCompletionDate':
            input_tag = soup.find('input', {'id': 'ContentPlaceHolder1_txtenddate'})
            if input_tag:
                raw_val = input_tag.get('value', '').strip()
                value = convert_to_yyyy_mm_dd(raw_val) if raw_val else None

        elif field == 'projectAddress':
            textarea_tag = soup.find('textarea', {'id': 'ContentPlaceHolder1_AadharNumber'})
            if textarea_tag:
                value = textarea_tag.text.strip()

        elif field == 'promotersAddress':
            textarea_tag = soup.find('textarea', {'id': 'ContentPlaceHolder1_txt_p_registeredaddress'})
            if textarea_tag:
                value = textarea_tag.text.strip().title()

        elif field == 'reraRegistrationDate':
            table = soup.find('table', {'id': 'ContentPlaceHolder1_grid_plot'})
            if table:
                rows = table.find_all('tr')
                if len(rows) > 1:
                    td = rows[1].find_all('td')
                    if td:
                        raw_val = td[0].text.strip()
                        value = convert_to_yyyy_mm_dd(raw_val)

        elif field == 'projectStateName':
            select_tag = soup.find('select', {'id': 'ContentPlaceHolder1_State_Name'})
            if select_tag:
                selected_option = select_tag.find('option', selected=True)
                if selected_option:
                    value = selected_option.text.strip()

        elif field == 'projectDistrictName':
            select_tag = soup.find('select', {'id': 'ContentPlaceHolder1_District_Name'})
            if select_tag:
                selected_option = select_tag.find('option', selected=True)
                if selected_option:
                    value = selected_option.text.strip()

        else:
            element = soup.find('input', {'id': field}) or soup.find('span', {'id': field})
            if element:
                value = element.get('value', '').strip() if element.name == 'input' else element.text.strip()

        data[field] = value
        if not value:
            null_fields.append(field)

    return data, null_fields

def clean_text(val, case="title"):
    val = val.strip()
    val = re.sub(r'\s+', ' ', val)
    return {
        "title": val.title(),
        "upper": val.upper(),
        "lower": val.lower()
    }.get(case, val)

def parse_description(desc):
    desc = html.unescape(desc)

    def extract(regex):
        match = re.search(regex, desc)
        return match.group(1).strip() if match else ""

    return {
        "promoterName": extract(r'Promoter name\s*:\s*([^<]+)'),
        "projectRegistrationNo": extract(r'CG-RERA Registration No\s*:\s*([^<]+)'),
        "projectStatus": extract(r'Project Status\s*:\s*([^<]+)'),
        "projectTypeDesc": extract(r'Project Type\s*:\s*([^<]+)'),
        "district": extract(r'District\s*:\s*([^<]+)'),
        "tahsil": extract(r'Tahsil\s*:\s*([^<]+)'),
        "projectAddress": extract(r'Project Address\s*:\s*([^<]+)'),
        "viewLink": extract(r'<a href=([^>]+)>More info</a>')
    }

def map_project_to_payload(proj):
    desc_data = parse_description(proj.get("description", ""))
    location = proj.get("location", "")
    latitude, longitude = location.split("|") if "|" in location else ("", "")

    view_link = desc_data.get("viewLink", "").strip('"')
    full_view_link = BASE_URL + view_link if view_link and not view_link.startswith("http") else view_link

    raw_name_full = desc_data.get("promoterName", "")
    promoter_type = re.search(r'\((.*?)\)', raw_name_full)
    promoter_type = promoter_type.group(1) if promoter_type else ""
    promoter_name_clean = re.sub(r'\s*\([^)]*\)', '', raw_name_full).strip()

    development_type_map = {
        "1": "Group Housing",
        "4": "Plotted Development"
    }

    return {
        'projectCin': None,
        'promoterCin': None,
        'projectName': clean_text(proj.get("title", ""), "title"),
        'promoterName': clean_text(promoter_name_clean, "title"),
        'acknowledgementNumber': None,
        'projectRegistrationNo': clean_text(desc_data.get("projectRegistrationNo", ""), "upper"),
        'reraRegistrationDate': "",
        'projectProposeCompletionDate': "",
        'projectStatus': clean_text(desc_data.get("projectStatus", ""), "title"),
        'projectType': clean_text(development_type_map.get(proj.get("development_type", ""), desc_data.get("projectTypeDesc", "")), "title"),
        'promoterType': clean_text(promoter_type, "title"),
        'projectStateName': "Chhattisgarh",
        'projectPinCode': None,
        'projectDistrictName': clean_text(desc_data.get("district", ""), "title"),
        'projectVillageName': None,
        'projectAddress': clean_text(desc_data.get("projectAddress", ""), "title"),
        'totalLandArea': None,
        'promotersAddress': None,
        'landownerTypes': None,
        'promoterPinCode': None,
        'longitude': longitude.strip(),
        'latitude': latitude.strip(),
        'viewLink': full_view_link
    }

def extract_json_from_scripts(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    scripts = soup.find_all('script', {'type': 'text/javascript'})
    json_pattern = re.compile(r'(\[\s*\{.*?\}\s*\])', re.DOTALL)

    for script in scripts:
        if script.string:
            match = json_pattern.search(script.string)
            if match:
                try:
                    return json.loads(html.unescape(match.group(1)))
                except json.JSONDecodeError:
                    continue
    return []

def rera_cg():
    try:
        response = requests.get(URL, headers=HEADERS, verify=False)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Error fetching main page: {e}")
        return

    project_data = extract_json_from_scripts(response.text)
    if not project_data:
        print("❌ No valid project data found.")
        return

    all_payloads = []
    for proj in project_data:
        payload = map_project_to_payload(proj)
        null_fields = [k for k in payload if not payload[k] and k != "viewLink"]

        if null_fields and payload["viewLink"]:
            fetched_data, _ = extract_rera_data_from_url(payload["viewLink"])
            for field in null_fields:
                if not payload[field] and fetched_data.get(field):
                    payload[field] = fetched_data[field]

        # all_payloads.append(payload)
        print(payload)
        write_to_MargeFile(payload,"CG")
#     with open("D:/test/nex_rera/rera_chattisgarh/rera_projects_data_optimized.txt", "a", encoding="utf-8") as f:
#         json.dump(all_payloads, f, ensure_ascii=False, indent=2)
#
#     print(f"\n📁 Saved {len(all_payloads)} projects to 'rera_projects_data_optimized.txt'")
#
# if __name__ == "__main__":
#     main()

rera_cg()