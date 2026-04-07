import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import json
from datetime import datetime
from Scripts.write_to_txt_file import write_to_MargeFile



def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
    except Exception:
        return None
def final_payload(project_data_1, project_data_2, project_data_3):
    reg_date =project_data_2.get('Project Registration Date')
    if reg_date:
        reg_date = convert_date_format(reg_date)

    comp_date = project_data_2.get('Declared Date Of Completion') or project_data_3.get('Proposed Completion Date')
    if comp_date:
        comp_date = convert_date_format(comp_date)
    return {
        'projectCin': None,
        'promoterCin': None,
        'projectName': project_data_1.get('project_name') or project_data_2.get('Project Name') or project_data_3.get('Project Name'),
        'promoterName': project_data_1.get('promoter') or project_data_2.get('Name'),
        'acknowledgementNumber': None,
        'projectRegistrationNo': project_data_1.get('rera_reg_no') or project_data_2.get('Registration Number'),
        'reraRegistrationDate': reg_date,
        'projectProposeCompletionDate': comp_date,
        'projectStatus': project_data_2.get('Project Type'),
        'projectType': project_data_3.get('Project Category') or project_data_1.get('project_type'),
        'promoterType': project_data_2.get('Applicant Type'),
        'projectStateName': project_data_2.get('State') or 'Uttar Pradesh',
        'projectPinCode': None,
        'projectDistrictName': project_data_2.get('District') or project_data_1.get('district'),
        'projectVillageName': project_data_3.get('Village/Locality/Sector etc.'),
        'projectAddress': project_data_2.get('Project Address') or project_data_3.get('Address') ,
        'totalLandArea': project_data_3.get('Total area in round figure (Sq.mt.)'),
        'promotersAddress': project_data_2.get("Promoter's Address"),
        'landownerTypes': None,
        'promoterPinCode': None,
        'longitude': project_data_3.get('Longtitude') or project_data_3.get('Longitude'),
        'latitude': project_data_3.get('Latitude'),
        'viewLink': project_data_1.get('details_url'),
    }



def rera_up():
    session = requests.Session()
    url = "https://www.up-rera.in/projects"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "Referer": "https://www.up-rera.in/index",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1"
    }
    response = session.get(url, headers = headers, timeout = 1200)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find('table' , id="grdPojDetail")
    # project_data = []
    base_url = "https://www.up-rera.in/"

    for row in table.find_all('tr')[1:]:  # Skip header
        cols = row.find_all('td')
        if len(cols) >= 9:
            project_data = {
                "sno": cols[0].text.strip(),
                "promoter": cols[1].get_text(strip=True),
                "project_name": cols[2].get_text(strip=True),
                "rera_reg_no": cols[3].get_text(strip=True),
                "project_type": cols[4].get_text(strip=True),
                "district": cols[5].get_text(strip=True),
                "start_date": cols[6].get_text(strip=True),
                "end_date": cols[7].get_text(strip=True),
                "details_url": base_url + cols[8].find('a')['href'] if cols[8].find('a') else None
            }

        # print(project_data)
        if project_data['details_url']:
            deatilresponse = session.get(project_data['details_url'], headers=headers, timeout=1200)
            print("Status Code:", deatilresponse.status_code)
            soup = BeautifulSoup(deatilresponse.text, 'html.parser')
            project_data_2 = {}

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if "mapview_project.aspx?form=" in href:
                    parsed_url = urlparse(href)
                    form_value = parse_qs(parsed_url.query).get('form', [None])[0]
                    print("Found form ID:", form_value)
            # Go through all rows containing project details
            for row in soup.select('div._xymns .row, .xyz-dialog .row'):
                columns = row.find_all('div', class_='col-sm-4') or row.find_all('div', class_='col-sm-6')
                values = row.find_all('div', class_='col-sm-8') or row.find_all('div', class_='col-sm-6')[1:]

                if columns and values:
                    key = columns[0].get_text(strip=True).replace(':', '')
                    value = values[0].get_text(strip=True)
                    if key:  # Only add if key is not empty
                        project_data_2[key] = value
            # print(project_data_2)


            if form_value:

                projecturl = "https://www.up-rera.in/viewprojects?id={}".format(form_value)
                projectresponse = session.get(projecturl, headers=headers, timeout=1200)
                # print(projectresponse.text)
                soup = BeautifulSoup(projectresponse.text, "html.parser")


                panel_div = soup.find("div", id="ctl00_ContentPlaceHolder1_PanelBasicDetails")

                # Step 2: Find the first table inside this panel
                table = panel_div.find("table")

                # Step 3: Parse key-value pairs
                project_deta_3 = {}

                for row in table.find_all("tr"):
                    cells = row.find_all("td")
                    for i in range(0, len(cells) - 1, 2):  # every key-value pair is 2 cells
                        key = cells[i].get_text(strip=True)
                        value_cell = cells[i + 1]

                        # Check if value is in input tag
                        input_tag = value_cell.find("input")
                        if input_tag and input_tag.has_attr("value"):
                            value = input_tag["value"].strip()
                        else:
                            # Remove colon if present (e.g., ": value")
                            value = value_cell.get_text(strip=True).lstrip(":").strip()

                        if key:
                            project_deta_3[key] = value

                # print(project_deta_3)
                final_data = final_payload(project_data,project_data_2,project_deta_3)
                print(final_data)
                for key, value in final_data.items():
                    if value == '':
                        final_data[key] = None
                write_to_MargeFile(final_data,"UP")

# up_rera()