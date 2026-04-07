import requests
from bs4 import BeautifulSoup
import ssl
from requests.adapters import HTTPAdapter
from datetime import datetime
import json
from Scripts.write_to_txt_file import write_to_MargeFile



# def write_to_MargeFile(newline):
#     file_path = r"D:\\Rera_new_collection\\New_Rera_west_bengal.txt"
#     with open(file_path, 'a', encoding='utf-8') as text_file:
#         json.dump(newline, text_file, ensure_ascii=False)
#         text_file.write(",\n")

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.load_verify_locations(
            r"D:\Rera_project\Reraproject\rera_scraping_app\security\_.wb.gov.in.crt")  # Load your specific certificate
        context.options |= ssl.OP_LEGACY_SERVER_CONNECT  # Enable legacy renegotiation
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)


def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
    except Exception:
        return None


def final_payload(result, project_details):
    promoter_info = project_details.get('promoter_details', {})

    return {
        'projectCin': None,
        'promoterCin': None,
        'projectName': result.get('project_name') or project_details.get('project_name'),
        'promoterName': promoter_info.get('promoter_name'),
        'acknowledgementNumber': None,
        'projectRegistrationNo': result.get('registration_no') or project_details.get('registration_no'),
        'reraRegistrationDate': convert_date_format(result.get('registration_date')),
        'projectProposeCompletionDate': convert_date_format(result.get('completion_date')),
        'projectStatus': project_details.get('project_status'),
        'projectType': project_details.get('project_type'),
        'promoterType': promoter_info.get('company_type'),
        'projectStateName': "West Bengal",  # Fixed value for this use case
        'projectPinCode': promoter_info.get('pincode'),
        'projectDistrictName': "North 24-Parganas",  # Can parse if needed
        'projectVillageName': None,  # Not available directly
        'projectAddress': project_details.get('location_address'),
        'totalLandArea': project_details.get('land_area'),
        'promotersAddress': promoter_info.get('address'),
        'landownerTypes': None,
        'promoterPinCode': promoter_info.get('pincode'),
        'longitude': None,
        'latitude': None,
        'viewLink': result.get('project_detail_link'),
    }


def get_project_details(url, session):
    response = session.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {url} - Status: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    data = {}

    # --- Project main details ---
    outer_ul = soup.find('ul', class_='outerrera')
    if outer_ul:
        lis = outer_ul.find_all('li')
        for li in lis:
            text = li.get_text(separator=" ", strip=True)
            if 'PROJECT STATUS' in text:
                data['project_status'] = text.replace('PROJECT STATUS -', '').strip()
            elif 'PROJECT ID' in text:
                data['project_id'] = text.replace('PROJECT ID:', '').strip()
            elif 'PROJECT COMPLETION DATE' in text:
                data['completion_date'] = text.replace('PROJECT COMPLETION DATE:', '').strip()
            elif 'EXTENSION COMPLETION DATE' in text:
                data['extension_completion_date'] = text.replace('EXTENSION COMPLETION DATE:', '').strip()
            elif 'RERA REGISTRATION NO' in text:
                data['registration_no'] = text.replace('RERA REGISTRATION NO.:', '').strip()

    # --- Highlights ---
    highlights = soup.select('div.ms_overviewList ul li')
    for li in highlights:
        label_tag = li.find('span')
        if label_tag:
            parts = label_tag.get_text(separator='|').split('|')
            if len(parts) == 2:
                label = parts[0].strip()
                value = parts[1].strip()
                if 'Project Type' in label:
                    data['project_type'] = value
                elif 'Land Area' in label:
                    data['land_area'] = value

    # --- Location section ---
    loc_section = soup.find('section', class_='locationmap')
    if loc_section:
        # Extract address
        h5 = loc_section.find('h5')
        if h5:
            data['location_address'] = h5.get_text(separator=' ', strip=True)

    # --- Promoter details ---

    promoter_heading = soup.find('h3', string=lambda t: t and 'Promoter Details' in t)
    if promoter_heading:
        # Get the next section (amenities) after this heading
        promoter_section = promoter_heading.find_next('section')

    if promoter_section:
        promoter_data = {}

        # Name
        name_tag = promoter_section.find('h3', class_='text-primary')
        if not name_tag:
            name_tag = promoter_section.find('h3')
        if name_tag:
            promoter_data['promoter_name'] = name_tag.get_text(strip=True)

        # Company info
        leads = promoter_section.find_all('div', class_='lead')
        for lead in leads:
            text = lead.get_text(separator=" ", strip=True)
            if 'Company Type' in text:
                promoter_data['company_type'] = text.replace('Company Type    :', '').strip()
            elif 'Address' in text:
                promoter_data['address'] = text.replace('Address         :', '').strip()

            elif 'Pincode' in text:
                promoter_data['pincode'] = text.replace('Pincode         :', '').strip()

        data['promoter_details'] = promoter_data

    return data


def rera_West_bengal():
    session = requests.Session()
    session.mount('https://', SSLAdapter())

    url = "https://rera.wb.gov.in/district_project.php?dcode=0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Referer": "https://rera.wb.gov.in/project_details.php?procode=15660000000008",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1"
    }

    # Send GET request
    response = session.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        # print(soup)
        rows = soup.select("#projectDataTable tbody tr")
        # projects = []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 6:
                project = {
                    "sl_no": cols[0].text.strip(),
                    "project_id": cols[1].text.strip(),
                    "project_name": cols[2].text.strip(),
                    "project_detail_link": "https://rera.wb.gov.in/" + cols[2].find("a")["href"].strip(),
                    "completion_date": cols[3].text.strip(),
                    "registration_no": cols[4].text.strip(),
                    "registration_date": cols[5].text.strip(),
                }
                print(project)
                project_details = get_project_details(project["project_detail_link"], session)
                # print(project_details)
                final_data = final_payload(project, project_details)
                print(final_data)
                write_to_MargeFile(final_data,"WestBengal")


# scrape_wb_rera_projects()
