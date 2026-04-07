import requests
from bs4 import BeautifulSoup
import re
import json
import urllib3
from datetime import datetime
import time
from Scripts.write_to_txt_file import write_to_MargeFile

from datetime import datetime
safe_time_str = datetime.now().strftime('%Y-%m-%d')
output_file_ = f"D:\\test\\nex_rera\\Rera_Delhi\\rera_Delhi_data_{safe_time_str}.txt"


urllib3.disable_warnings()

BASE_URL = "https://www.rera.delhi.gov.in/registered_promoters_list?combine_1=&items_per_page=All"
AJAX_URL = "https://www.rera.delhi.gov.in/visitor/ajax"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL
}

def format_date(date_str):
    if not date_str:
        return None
    date_str = date_str.strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str

def clean_text(text):
    if not text:
        return None
    return text.strip().title()

def extract_pin(text):
    match = re.search(r'\b\d{6}\b', text)
    return match.group() if match else None

def parse_project_table(html, nid_lookup=None):
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.select("table.views-table tbody tr")
    data, reg_nos = [], []

    for row in rows:
        promoter_td = row.select_one('td.views-field-php-1')
        project_td = row.select_one('td.views-field-field-project-address')
        reg_td = row.select_one('td.views-field-field-rera-registrationno')

        promoter_name = clean_text(promoter_td.find('strong', string=re.compile("Name")).next_sibling)
        promoters_address = clean_text(promoter_td.find('strong', string=re.compile("Address")).next_sibling)
        promoter_pin = extract_pin(promoters_address)

        project_name = clean_text(project_td.find('strong', string=re.compile("Name")).next_sibling)
        project_address_match = re.search(r"Location :\s*(.*?)<", str(project_td), re.DOTALL)
        project_address = clean_text(project_address_match.group(1)) if project_address_match else None
        project_pin = extract_pin(project_address or "")

        reg_no = clean_text(reg_td.find('strong', string=re.compile("Registration No")).next_sibling)
        reg_nos.append(reg_no)

        status_label = reg_td.find('strong', string=re.compile("Construction Status", re.I))
        project_status = clean_text(status_label.next_sibling) if status_label else None

        pdf_link_tag = reg_td.select_one('a[href$=".pdf"]')
        view_link = pdf_link_tag['href'] if pdf_link_tag else None

        project = {
            'projectCin': None,
            'promoterCin': None,
            'projectName': project_name,
            'promoterName': promoter_name,
            'acknowledgementNumber': None,
            'projectRegistrationNo': reg_no.upper(),
            'reraRegistrationDate': None,
            'projectProposeCompletionDate': None,
            'projectStatus': project_status,
            'projectType': None,
            'promoterType': None,
            'projectStateName': 'Delhi',
            'projectPinCode': project_pin,
            'projectDistrictName': None,
            'projectVillageName': None,
            'projectAddress': project_address,
            'totalLandArea': None,
            'promotersAddress': promoters_address,
            'landownerTypes': None,
            'promoterPinCode': promoter_pin,
            'longitude': None,
            'latitude': None,
            #'viewLink': view_link,
            'viewLink': ""
        }

        if nid_lookup:
            nid_info = nid_lookup.get(reg_no, {})
            project.update({
                'projectCin': nid_info.get('project_cin'),
                'promoterCin': nid_info.get('promoter_cin'),
                'acknowledgementNumber': nid_info.get('ack_no'),
                'reraRegistrationDate': format_date(nid_info.get('registration_date')),

                'projectProposeCompletionDate': format_date(nid_info.get('propose_date')),
                'projectType': clean_text(nid_info.get('project_type')),
                'promoterType': clean_text(nid_info.get('promoter_type')),
                'projectDistrictName': clean_text(nid_info.get('district_name')),
                'projectVillageName': clean_text(nid_info.get('village')),
                'projectAddress': clean_text(nid_info.get('project_address', project_address)),
                'projectPinCode': nid_info.get('project_pin_code', project_pin),
                'totalLandArea': nid_info.get('total_land_area'),
                'landownerTypes': clean_text(nid_info.get('land_owner_type')),
                'latitude': nid_info.get('latitude'),
                'longitude': nid_info.get('longitude'),
                'viewLink': "https://www.rera.delhi.gov.in/project_page/" + str(nid_info.get('url', ''))
            })

        data.append(project)

    return data, reg_nos

def fetch_nid_batch(batch):
    payload = {"mod": "get_project_nid", "data": json.dumps(batch)}
    try:
        res = requests.post(AJAX_URL, headers=HEADERS, data=payload, timeout=15, verify=False)
        return res.json() if res.ok else ["" for _ in batch]
    except Exception as e:
        print(f"❌ NID fetch error: {e}")
        return ["" for _ in batch]

def fetch_project_nid_data_sequential(reg_nos, batch_size=10):
    all_nids = []
    for i in range(0, len(reg_nos), batch_size):
        batch = reg_nos[i:i+batch_size]
        nids = fetch_nid_batch(batch)
        all_nids.extend(nids)
        time.sleep(0.3)  # optional delay between batches
    return all_nids

def get_project_details(url):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.rera.delhi.gov.in/"
    }
    session.get("https://www.rera.delhi.gov.in/", headers=headers, verify=False)
    try:
        res = session.get(url, headers=headers, timeout=20, verify=False)
        if res.status_code != 500:
            raise Exception(f"Status {res.status_code}")
    except Exception as e:
        raise Exception(f"Timeout/Fail for {url}: {e}")

    soup = BeautifulSoup(res.text, "html.parser")
    def get_text_date(label):
        for div in soup.select("div.row, div.row.mb-3"):
            label_div = div.select_one("div.col-md-3 span")
            value_div = div.select_one("div.col-md-9")
            if label_div and label in label_div.text and value_div:
                return value_div.get_text(strip=True)
        return None



    def get_text(label):
        for div in soup.select("div.row.mb-3"):
            if label in div.text:
                parts = div.find_all("div")
                return parts[1].text.strip() if len(parts) > 1 else None
        return None

    location = clean_text(get_text("Location"))
    return {
        "projectAddress": location,
        "projectDistrictName": clean_text(get_text("District")),
        "projectPinCode": extract_pin(location or ""),
        "totalLandArea": clean_text(get_text("Land Area")),
        "projectType": clean_text(get_text("Project Type")),
        "latitude": clean_text(get_text("Latitude")),
        "longitude": clean_text(get_text("Longitude")),
        "reraRegistrationDate": format_date(get_text("Start Date")),
        "projectProposeCompletionDate": format_date(get_text_date("End Date"))
    }

def enrich_and_save_data(projects):
    # with open(output_file, 'w', encoding='utf-8') as f:
        for idx, project in enumerate(projects, 1):
            url = project.get('viewLink')
            if url:
                try:
                    details = get_project_details(url)
                    for k, v in details.items():
                        if v:
                            project[k] = v
                except Exception as e:
                    print(f"❌ Error fetching details for {url}: {e}")

            #project.pop('url_code', None)
            # json_data = json.dumps(project, ensure_ascii=False)
            print(project)
            write_to_MargeFile(project,"Delhi")
            # f.write(json_data + '\n')

            if idx % 5 == 0 or idx == len(projects):
                print(f"✅ Processed {idx}/{len(projects)} projects.")

    # print(f"\n✅ All data printed and saved to {output_file}")

def rera_delhi():
    res = requests.get(BASE_URL, verify=False)
    if res.status_code == 500 or res.status_code == 200:
        print("✔️ Parsing base project data...")
        base_data, reg_nos = parse_project_table(res.text)
        print(f"✔️ Found {len(reg_nos)} projects. Fetching NID codes sequentially...")
        url_codes = fetch_project_nid_data_sequential(reg_nos)
        nid_lookup = {reg: {'url': code} for reg, code in zip(reg_nos, url_codes)}
        enriched_data, _ = parse_project_table(res.text, nid_lookup=nid_lookup)
        enrich_and_save_data(enriched_data)
    else:
        print(f"❌ Initial GET failed: {res.status_code}")

# if __name__ == "__main__":
#     rera_delhi()
