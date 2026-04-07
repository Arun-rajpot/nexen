import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime
import os
import traceback
from Scripts.write_to_txt_file import write_to_MargeFile

session = requests.Session()

BASE_URL = "https://rera.ap.gov.in/RERA/Views/Reports/ApprovedProjects.aspx"
DETAILS_BASE_URL = "https://rera.ap.gov.in/RERA/Views/QprPreview.aspx??"

CHECKPOINT_FILE = r"D:\\New_Rera\\New_rera_project\\checkpoint.txt"

def convert_to_iso(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None

def title_or_none(text):
    return text.strip().title() if text else None

def clean(val):
    return val.strip() if val and val.strip() else None

def get_hidden_fields(soup):
    hidden_inputs = soup.find_all("input", type="hidden")
    return {i.get("name"): i.get("value", "") for i in hidden_inputs if i.get("name")}

def format_ctl(row_index):
    ctl_num = row_index + 2
    return f"ctl0{ctl_num}" if ctl_num < 10 else f"ctl{ctl_num}"

def get_promoter_name(detail_url):
    try:
        r = session.get(detail_url, timeout=200)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            tag = soup.find(id="lblPromoterName")
            return tag.text.strip() if tag and tag.text.strip() else None
        return None
    except Exception:
        return None

headers_approval = {
    "User-Agent": "Mozilla/5.0",
}

session.headers.update(headers_approval)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return int(f.read().strip())
    return 0

def save_checkpoint(row_num):
    with open(CHECKPOINT_FILE, "w") as f:
        f.write(str(row_num))

def get_rows_and_fields():
    resp = session.get(BASE_URL)
    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find("table", {"id": "ContentPlaceHolder1_gvApprovedProject"})
    rows = table.find_all("tr")[1:] if table else []
    hidden_fields = get_hidden_fields(soup)
    return rows, hidden_fields

def refresh_hidden_fields():
    # Call GET to get fresh hidden fields
    resp = session.get(BASE_URL)
    soup = BeautifulSoup(resp.text, 'html.parser')
    return get_hidden_fields(soup)

def main(start_row_1, rows):
    hidden_fields = refresh_hidden_fields()
    for row_num, row in enumerate(rows):
        if row_num < start_row_1:
            continue

        print(f"\n🔵 Processing row {row_num + 1}/{len(rows)}...")
        cols = [clean(td.text) for td in row.find_all("td")]
        ctl_str = format_ctl(row_num)
        event_target = f"ctl00$ContentPlaceHolder1$gvApprovedProject${ctl_str}$lnkview"

        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            time.sleep(random.uniform(1, 3))
            post_data = hidden_fields.copy()
            post_data.update({
                "__EVENTTARGET": event_target,
                "__EVENTARGUMENT": "",
            })

            try:
                response = session.post(BASE_URL, data=post_data, timeout=200)
                text = response.text

                enc_start = text.find("enc=")
                if enc_start != -1:
                    enc_end_single = text.find("'", enc_start)
                    enc_end_double = text.find('"', enc_start)
                    enc_end = min(
                        enc_end_single if enc_end_single != -1 else len(text),
                        enc_end_double if enc_end_double != -1 else len(text)
                    )
                    enc_param = text[enc_start:enc_end]
                    detail_url = DETAILS_BASE_URL + enc_param

                    promoter_name = get_promoter_name(detail_url)

                    mapped = {
                        'projectCin': None,
                        'promoterCin': None,
                        'projectName': title_or_none(clean(cols[2]) if len(cols) > 2 else None),
                        'promoterName': title_or_none(promoter_name),
                        'acknowledgementNumber': None,
                        'projectRegistrationNo': clean(cols[1]) if len(cols) > 1 else None,
                        'reraRegistrationDate': convert_to_iso(cols[6]) if len(cols) > 6 else None,
                        'projectProposeCompletionDate': convert_to_iso(cols[7]) if len(cols) > 7 else None,
                        'projectStatus': title_or_none(clean(cols[5]) if len(cols) > 5 else None),
                        'projectType': title_or_none(clean(cols[4]) if len(cols) > 4 else None),
                        'promoterType': None,
                        'projectStateName': "Andhra Pradesh",
                        'projectPinCode': None,
                        'projectDistrictName': None,
                        'projectVillageName': None,
                        'projectAddress': title_or_none(clean(cols[3]) if len(cols) > 3 else None),
                        'totalLandArea': None,
                        'promotersAddress': None,
                        'landownerTypes': None,
                        'promoterPinCode': None,
                        'longitude': None,
                        'latitude': None,
                        'viewLink': "https://rera.ap.gov.in/RERA/Views/Reports/ApprovedProjects.aspx"
                    }

                    print(mapped)
                    write_to_MargeFile(mapped,"AP")

                    # Update hidden fields for next iteration
                    soup = BeautifulSoup(text, 'html.parser')
                    hidden_fields = get_hidden_fields(soup)

                    save_checkpoint(row_num + 1)
                    break
                else:
                    print("No enc= URL found, refreshing hidden fields...")
                    hidden_fields = refresh_hidden_fields()
                    save_checkpoint(row_num + 1)
                    break

            except requests.RequestException as e:
                retry_count += 1
                print(f"Error (Attempt {retry_count}): {e}")
                if retry_count < max_retries:
                    print("Retrying after 10 seconds...")
                    time.sleep(10)
                else:
                    print("Max retries reached. Waiting after some time before continuing...")
                    time.sleep(300)
                    hidden_fields = refresh_hidden_fields()
                    save_checkpoint(row_num)
                    break

def rera_AP():
    while True:
        try:
            start_row = load_checkpoint()
            print(f"Resuming from row {start_row + 1}")
            rows, _ = get_rows_and_fields()
            main(start_row, rows)
            print("All rows processed successfully. Exiting.")
            break
        except Exception as e:
            print("Fatal error encountered. Restarting script after some time...")
            print(traceback.format_exc())
            time.sleep(30)




