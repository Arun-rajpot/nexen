import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from datetime import datetime
import re
from Scripts.write_to_txt_file import write_to_MargeFile


# =========================== Helpers ===========================
def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
    except Exception:
        return None


def normalize_key(text):
    # Remove extra spaces, colon, newlines, convert to snake_case
    text = text.strip().replace(":", "").replace("\n", " ")
    text = re.sub(r'\s+', '_', text.lower())
    return text


def extract_table_key_values(table):
    data = {}
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        # Process columns in steps of 3: Label, Colon, Value
        for i in range(0, len(cols), 3):
            if i + 2 < len(cols):
                key_text = cols[i].get_text(strip=True)
                value_text = cols[i + 2].get_text(strip=True)
                if key_text and value_text:
                    key_norm = normalize_key(key_text)
                    data[key_norm] = value_text
    return data


def extract_project_details(soup):
    project_info = {}
    project_location = {}
    fieldsets = soup.find_all("fieldset")
    for fs in fieldsets:
        legend = fs.find("legend")
        if legend:
            legend_text = legend.text.strip()
            if "Project Information" in legend_text:
                table = fs.find("table")
                if table:
                    project_info = extract_table_key_values(table)
            elif "Project Location Details" in legend_text:
                table = fs.find("table")
                if table:
                    project_location = extract_table_key_values(table)

    # print("project_info===",project_info)
    # print("project_location===",project_location)
    return project_info, project_location


# =========================== Final Formatter ===========================
def final_data(details):
    # print(details)

    return {
        'projectCin': None,
        'promoterCin': None,
        'projectName': details.get('project_name'),
        'promoterName': details.get('promoter_name'),
        'acknowledgementNumber': None,
        'projectRegistrationNo': details.get('registration_no') or details.get('project_registration_no'),
        'reraRegistrationDate': convert_date_format(
            details.get('registration_date') or details.get('rera_registration_date')),
        'projectProposeCompletionDate': convert_date_format(
            details.get('project_end_date') or details.get('proposed_completion_date')),
        'projectStatus': details.get('project_status'),
        'projectType': details.get('project_type'),
        'promoterType': details.get('promoter_type'),
        'projectStateName': "Bihar",
        'projectPinCode': None,
        'projectDistrictName': details.get('district_name') or details.get('project_district_name') or details.get(
            'district'),
        'projectVillageName': None,
        'projectAddress': details.get('project_address'),
        'totalLandArea': details.get('total_land_area') or details.get('total_area_of_land_(sq_mt)'),
        'promotersAddress': details.get('promoters_address') or details.get('project_address'),
        'landownerTypes': details.get('landowner_types'),
        'promoterPinCode': details.get('promoterPinCode'),
        'longitude': details.get('longitude_of_end_point_of_the_plot'),
        'latitude': details.get('latitude_of_end_point_of_the_plot'),
        'viewLink': details.get('view_link'),
    }


# =========================== Extractor ===========================
def extract_details_from_qrcode_page(html_content, view_url):
    soup = BeautifulSoup(html_content, "html.parser")
    data = {
        'view_link': view_url
    }

    # Extract dynamic project info and location info from tables inside fieldsets
    project_info, project_location = extract_project_details(soup)

    # Merge both dictionaries (location may overwrite keys in project_info if duplicates)
    data.update(project_info)
    data.update(project_location)

    # Also try to extract some common quick info outside tables (fallbacks)
    try:
        promoter_name = soup.find("span", {"id": "Label98"})
        if promoter_name:
            data.setdefault('promoter_name', promoter_name.get_text(strip=True))

        promoter_type = soup.find("span", {"id": "lblPromotertype"})
        if promoter_type:
            data.setdefault('promoter_type', promoter_type.get_text(strip=True))

        reg = soup.find("span", {"id": "lblRegNo"})
        if reg:
            reg_text = reg.get_text(strip=True)
            val = reg_text.split(":", 1)[-1].strip() if ":" in reg_text else reg_text
            data.setdefault('registration_no', val)

        regdate = soup.find("span", {"id": "lblRegDate"})
        if regdate:
            regdate_text = regdate.get_text(strip=True)
            val = regdate_text.split(":", 1)[-1].strip() if ":" in regdate_text else regdate_text
            data.setdefault('registration_date', val)

        promoterPinCode = soup.find("span", {"id": "Label90"})
        if promoterPinCode:
            promoterPinCode_text = promoterPinCode.get_text(strip=True)
            propin = promoterPinCode_text.split(":", 1)[
                -1].strip() if ":" in promoterPinCode_text else promoterPinCode_text
            data.setdefault('promoterPinCode', propin)

    except Exception as e:
        print(f"❌ Fallback parsing failed: {e}")

    return data


# =========================== Scraper ===========================
def rera_bihar():
    base_url = "https://rera.bihar.gov.in/"
    search_url = urljoin(base_url, "RERASearchPdistrictwise.aspx")
    session = requests.Session()

    # Step 1: GET initial page
    r = session.get(search_url)
    soup = BeautifulSoup(r.text, "html.parser")

    def get_hidden():
        try:
            return {
                "__VIEWSTATE": soup.find("input", id="__VIEWSTATE")["value"],
                "__VIEWSTATEGENERATOR": soup.find("input", id="__VIEWSTATEGENERATOR")["value"],
                "__EVENTVALIDATION": soup.find("input", id="__EVENTVALIDATION")["value"]
            }
        except Exception as e:
            print(f"❌ Failed to get hidden inputs: {e}")
            return {}

    hidden = get_hidden()

    # Step 2: Select Category -> Project (Category = 2)
    payload = {
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$ddlCategory",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        **hidden,
        "__VIEWSTATEENCRYPTED": "",
        "ctl00$ContentPlaceHolder1$ddlCategory": "2"
    }
    r = session.post(search_url, data=payload)
    soup = BeautifulSoup(r.text, "html.parser")
    hidden = get_hidden()

    # Step 3: Search for keyword "Ltd"
    txtsearches = ["Ltd", "Limited", "Llp"]
    ddlCategoryes = ["1", "2"]
    for ddlCategory in ddlCategoryes:
        for txtsearch in txtsearches:
            search_payload = {
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "__LASTFOCUS": "",
                **hidden,
                "__VIEWSTATEENCRYPTED": "",
                "ctl00$ContentPlaceHolder1$ddlCategory": ddlCategory,
                "ctl00$ContentPlaceHolder1$txtsearch": txtsearch,
                "ctl00$ContentPlaceHolder1$BtnSearch": "Search Now"
            }
            r = session.post(search_url, data=search_payload)
            soup = BeautifulSoup(r.text, "html.parser")

            # Step 4: Extract QR links and parse details
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if href.startswith("QRCODE.aspx?id="):
                    full_url = urljoin(base_url, href)
                    detail_resp = session.get(full_url)
                    data = extract_details_from_qrcode_page(detail_resp.text, full_url)
                    # print(data)
                    formatted = final_data(data)
                    print(formatted)
                    write_to_MargeFile(formatted,"Bihar")


# if __name__ == "__main__":
#
rera_bihar()
