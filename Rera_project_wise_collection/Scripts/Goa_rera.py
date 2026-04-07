import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import json
from Scripts.write_to_txt_file import write_to_MargeFile


# def write_to_MargeFile(newline):
#     file_path = r"D:\\Rera_new_collection\\New_Rera_Goa.txt"
#     with open(file_path, 'a', encoding='utf-8') as text_file:
#         json.dump(newline, text_file, ensure_ascii=False)
#         text_file.write(",\n")


# =========================== Helpers ===========================
def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
    except Exception:
        return None


def final_payload(result, project_details):
    return {
        'projectCin': None,
        'promoterCin': None,
        'projectName': result.get('Project', '').replace('Project:', '').strip() or project_details.get('Project Name'),
        'promoterName': result.get('PROMOTER') or project_details.get('Promoter Name'),
        'acknowledgementNumber': None,
        'projectRegistrationNo': result.get('Reg No.') or project_details.get('RERA Registration No.'),
        'reraRegistrationDate': convert_date_format(project_details.get('Project Start Date')),
        'projectProposeCompletionDate': convert_date_format(project_details.get('Project End Date')),
        'projectStatus': result.get('STATUS') or project_details.get('Project Status'),
        'projectType': result.get('PROPERTY TYPE') or project_details.get('Project Type'),
        'promoterType': result.get('PROMOTER TYPE') or project_details.get('Registration Type'),
        'projectStateName': project_details.get('State') or "Goa",
        'projectPinCode': None,
        'projectDistrictName': project_details.get('District'),
        'projectVillageName': None if project_details.get('Village') == '' else project_details.get('Village'),
        'projectAddress': result.get('address') or project_details.get('Address'),
        'totalLandArea': result.get('TOTAL AREA') or project_details.get('Total Area of Project Land'),
        'promotersAddress': None,
        'landownerTypes': None,
        'promoterPinCode': None,
        'longitude': None,
        'latitude': None,
        'viewLink': result.get('Read More'),
    }


def get_project_details(view_url):
    detail_res = requests.get(view_url)
    detail_containt = detail_res.text
    soup = BeautifulSoup(detail_containt, "html.parser")

    result = {}

    # Extract main project name (col-md-9 h1)
    project_name_tag = soup.select_one('div.col-md-9 > h1')
    if project_name_tag:
        result['Project Name'] = project_name_tag.get_text(strip=True)

    # Extract address (first <p> inside col-md-9, cleaning whitespace and ignoring icons)
    address_tag = soup.select_one('div.col-md-9 > p')
    if address_tag:
        # Remove any span inside p (like map icon)
        for span in address_tag.find_all('span'):
            span.decompose()
        address = ' '.join(address_tag.get_text(separator=' ').split())
        result['Address'] = address

    # Extract RERA Registration No and Registration Type from spans with class reg
    for reg_span in soup.select('p > span.reg'):
        text = reg_span.get_text(separator=' ', strip=True)
        # Check if it contains registration no
        if "RERA Registration No." in text:
            # Extract the registration no from <b> tag if present
            b_tag = reg_span.find('b')
            if b_tag:
                result['RERA Registration No.'] = b_tag.get_text(strip=True)
            else:
                # fallback if no <b>
                result['RERA Registration No.'] = text.replace('RERA Registration No. :', '').strip()
        elif "Registration Type" in text:
            # Just get the text after the colon
            reg_type = text.split("Registration Type")[-1].replace(":", "").strip()
            if not reg_type:
                # fallback: get from direct text content excluding 'Registration Type :'
                reg_type = reg_span.get_text(separator=' ').replace('Registration Type :', '').strip()
            result['Registration Type'] = reg_type
        else:
            # For links like Registration Certificate, Extension Certificate
            a_tag = reg_span.find('a')
            if a_tag and a_tag.get_text(strip=True):
                link_text = a_tag.get_text(strip=True)
                link_url = a_tag['href']
                # Join base URL if needed (example assumes base URL here)
                base_url = 'https://rera.goa.gov.in'
                full_link = link_url if link_url.startswith('http') else base_url + link_url
                result[link_text] = full_link

    # Extract key-value pairs from profile_detail rows
    profile_rows = soup.select('div.row.profile_detail > div.row')
    for row in profile_rows:
        cols = row.select('div.col-md-3')
        if len(cols) >= 4:
            # Key on left (first col)
            key = cols[0].get_text(separator=' ', strip=True).rstrip(':').strip()
            # Value on second col
            value = cols[1].get_text(separator=' ', strip=True)
            result[key] = value

            # There can be another key-value pair in the same row (3rd and 4th cols)
            key2 = cols[2].get_text(separator=' ', strip=True).rstrip(':').strip()
            value2 = cols[3].get_text(separator=' ', strip=True)
            result[key2] = value2

    return result


def rera_goa():
    url = "https://rera.goa.gov.in/reraApp/search"
    base_url = "https://rera.goa.gov.in/reraApp/"

    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://rera.goa.gov.in",
        "Referer": "https://rera.goa.gov.in/",

    }

    searchTxts = ["Ltd", "Limited", "Llp"]

    for searchTxt in searchTxts:
        startFrom = 0

        while True:
            payload = {
                "startFrom": str(startFrom),
                "Regtype": "Project",
                "isPagination": "true",
                "projectDist": "0",
                "subDistrictId": "0",
                "villageId": "0",
                "typeOfLand": "0",
                "searchTxt": searchTxt,
                "captcha": "",
            }

            response = requests.post(url, headers=header, data=payload, verify=False)
            soup = BeautifulSoup(response.content, "html.parser")

            projects = soup.find_all('div', class_='col-md-9 no_pad_lft')

            if not projects:
                print(f"No more projects found for searchTxt='{searchTxt}' at startFrom={startFrom}. Stopping.")
                break

            for proj in projects:
                # Project name
                proj_name = proj.find('h1').get_text(strip=True).replace("Project: ", "").strip()

                # Address clean-up
                raw_address = proj.find_all('p')[0].get_text(" ", strip=True)
                address = ' '.join(raw_address.split())

                # Reg No.
                reg_no = proj.find_all('p')[1].get_text(strip=True).replace('Reg No. :', '').strip()

                # Read More link (correct selector)
                a_tag = proj.select_one('p.pull-right a')
                read_more_link = urljoin(base_url, a_tag['href']) if a_tag and a_tag.has_attr('href') else None

                # Table data
                table = proj.find('table')
                table_data = {}
                if table:
                    headers = [th.get_text(strip=True) for th in table.find_all('th')]
                    row = table.find('tbody').find('tr')
                    values = [' '.join(td.get_text(" ", strip=True).split()) for td in row.find_all('td')]
                    table_data = dict(zip(headers, values))

                # Build result

                result = {
                    "Project": proj_name,
                    "address": address,
                    "Reg No.": reg_no,
                    "Read More": read_more_link
                }
                result.update(table_data)
                # print("result=====",result)
                # get project details
                project_details = get_project_details(read_more_link)

                # print("project_details=====",project_details)
                print("=====" * 50)

                final_data = final_payload(result, project_details)
                print(final_data)
                write_to_MargeFile(final_data,"Goa")

            startFrom += 10


# function call ========

# rera_goa()
