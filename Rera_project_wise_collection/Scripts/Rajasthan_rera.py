import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from datetime import datetime
from Scripts.write_to_txt_file import write_to_MargeFile


# def write_to_MargeFile(newline):
#     file_path = r"D:\\Rera_new_collection\\New_Rajasthan_rera.txt"
#     with open(file_path, 'a', encoding='utf-8') as text_file:
#         json_line = json.dumps(newline, ensure_ascii=False)
#         text_file.write(json_line)
#         text_file.write(",\n")


# =========================== Helpers ===========================
def convert_date_format(date_str):
    formats = [
        "%d-%m-%Y",
        "%B %d, %Y",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y-%m-%d"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def final_payload(row_data, project_data, project_details):
    promoter_info = project_details.get('Promoter Details', {})
    project_info = project_details.get('Project Details', {})

    reg_date = project_data.get('Date of Registration')
    if reg_date:
        reg_date = convert_date_format(reg_date)

    comp_date = project_info.get('Estimated Finish Date')
    if comp_date:
        comp_date = convert_date_format(comp_date)
    return {
        'projectCin': None,
        'promoterCin': None,
        'projectName': row_data.get('Project Name'),
        'promoterName': row_data.get('Promoter Name') or promoter_info.get('Organization Name'),
        'acknowledgementNumber': row_data.get('Application No'),
        'projectRegistrationNo': row_data.get('Registration No'),
        'reraRegistrationDate': reg_date,
        'projectProposeCompletionDate': comp_date,
        'projectStatus': project_data.get('Status of Project'),
        'projectType': project_info.get('Project Type'),
        'promoterType': promoter_info.get('Organization Type'),
        'projectStateName': project_info.get('State'),
        'projectPinCode': project_info.get('Pincode'),
        'projectDistrictName': project_info.get('District'),
        'projectVillageName': project_info.get('Village  Town  City'),
        'projectAddress': project_data.get('Project Address').replace(':', '').replace('/', ' ').replace('.',
                                                                                                         '').strip() if project_data.get(
            'Project Address') else None,
        'totalLandArea': project_info.get('Total Area Of Project (In sq meters)'),
        'promotersAddress': promoter_info.get('Street  Locality'),
        'landownerTypes': None,
        'promoterPinCode': promoter_info.get('Pin Code'),
        'longitude': None,
        'latitude': None,
        'viewLink': row_data.get('View Link'),
    }


def extract_table_data(table):
    data = {}
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all(['td', 'th'])
        # Handle cases where there are 2 or 4 columns per row for key-value pairs
        if len(cols) == 2:
            key = cols[0].get_text(strip=True).replace(':', '').replace('/', ' ').replace('.', '').strip()
            value = cols[1].get_text(strip=True).strip()
            if key and value:  # Ensure both key and value are not empty
                data[key] = value
        elif len(cols) == 4:
            key1 = cols[0].get_text(strip=True).replace(':', '').replace('/', ' ').replace('.', '').strip()
            value1 = cols[1].get_text(strip=True).strip()
            key2 = cols[2].get_text(strip=True).replace(':', '').replace('/', ' ').replace('.', '').strip()
            value2 = cols[3].get_text(strip=True).strip()
            if key1: data[key1] = value1
            if key2: data[key2] = value2
    return data


def parse_project_summary_html(url):
    base_url = "https://rera.rajasthan.gov.in"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    promoter_details = {}
    project_details = {}

    # Extract Promoter Details
    promoter_section_heading = soup.find('h2', class_='mainHeading', string='Promoter Details')
    if promoter_section_heading:
        promoter_tables = promoter_section_heading.find_next_siblings('table', class_='table-bordered')
        for table in promoter_tables:
            promoter_details.update(extract_table_data(table))

    # Extract Project Details
    project_section_heading = soup.find('h2', class_='mainHeading', string='Project Details')
    if project_section_heading:
        project_tables = project_section_heading.find_next_siblings('table', class_='table-bordered')
        for table in project_tables:
            project_details.update(extract_table_data(table))

    return {"Promoter Details": promoter_details, "Project Details": project_details}


def parse_project_view(view_url):
    base_url = "https://rera.rajasthan.gov.in"
    response = requests.get(view_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    project_data = {}

    # Get main heading (Project Name)
    heading = soup.find('article').find('h1')
    if heading:
        project_data["Project Name"] = heading.get_text(strip=True)

    # Parse overview tab details
    overview = soup.find('div', class_='tab-content overview')
    if overview:
        details = overview.find_all('div', class_='details')
        for detail in details:
            label = detail.find('span', class_='label') or detail.find('label')
            value = detail.find('span', class_='value') or detail.find('strong', class_='value')
            if label and value:
                key = label.get_text(strip=True)
                # Join all text, including <br> or embedded text nodes
                val_text = value.get_text(separator=' ', strip=True)

                # Special handling: Registration certificate link
                link_tag = value.find('a')
                if link_tag and 'Certificate' in key:
                    val_text = val_text.replace("View", "").strip()
                    project_data["Certificate Link"] = link_tag['href'] if link_tag else None

                # Summary links
                if "Project details as at the time" in key:
                    link = value.find('a')
                    if link:
                        project_data["Project Summary (Original)"] = base_url + link['href']
                elif "Updated project details" in key:
                    link = value.find('a')
                    if link:
                        project_data["Project Summary (Updated)"] = base_url + link['href']

                project_data[key] = val_text

        # Parse card-grid items (Total Area, Units, etc.)
        for card in overview.select('.card-grid .card'):
            label = card.find('span', class_='label').get_text(strip=True)
            value = card.find('span', class_='value').get_text(strip=True)
            project_data[label] = value

    # print("project_data====",project_data)
    final_data = parse_project_summary_html(project_data['Project Summary (Original)'])
    # print(final_data)
    return project_data, final_data


def rera_rajasthan():
    base_url = "https://rera.rajasthan.gov.in/project-search/"
    page = 1  # Start from page 1

    while True:
        url = f"{base_url}?per_page={page}"
        print(f"Fetching page: {page} URL: {url}")

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find('table', class_='table')

        if not table:
            print("No table found — stopping pagination.")
            break

        headers = [th.get_text(strip=True) for th in table.find_all('th')]

        for row in table.find('tbody').find_all('tr'):
            cols = row.find_all('td')
            values = [td.get_text(strip=True) for td in cols]

            # Extract 'View' link separately
            view_link_tag = row.find('a', class_='btn-primary')
            view_link = view_link_tag['href'] if view_link_tag else None
            values.append(view_link)

            if len(values) == len(headers) + 1:
                row_data = dict(zip(headers + ['View Link'], values))
            else:
                row_data = dict(zip(headers, values))

            # Process project details
            project_data, project_details = parse_project_view(view_link)
            final_data = final_payload(row_data, project_data, project_details)
            print(final_data)
            write_to_MargeFile(final_data,"Rajasthan")

        page += 1


# rera_rajasthan()