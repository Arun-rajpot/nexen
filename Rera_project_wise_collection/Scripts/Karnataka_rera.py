import requests
from bs4 import BeautifulSoup
import random
import time
import json
from datetime import datetime
from Scripts.write_to_txt_file import write_to_MargeFile


# def write_to_MargeFile(newline):
#     file_path = r"D:\\Rera_new_collection\\New_Rera_karnataka.txt"
#     with open(file_path, 'a', encoding='utf-8') as text_file:
#         json_line = json.dumps(newline, ensure_ascii=False)
#         text_file.write(json_line)
#         text_file.write(",\n")

def convert_date_format(date_str):
    return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
def get_final_payload(data, ViewProjectDetail):

    if data.get('Approved On'):
        reraRegistrationDate =  convert_date_format(data.get('Approved On'))
    else:
        reraRegistrationDate = None

    if data.get('Proposed Completion Date') :
        projectProposeCompletionDate = convert_date_format(data.get('Proposed Completion Date'))
    else:
        projectProposeCompletionDate = None

    project_data = {
        'projectCin': None,
        'promoterCin': None,
        'projectName': data.get('Project Name'),
        'promoterName': data.get('Promoter Name'),
        'acknowledgementNumber': data.get('Acknowledgement No'),
        'projectRegistrationNo': data.get('Registration No'),
        'reraRegistrationDate': reraRegistrationDate,
        'projectProposeCompletionDate': projectProposeCompletionDate,
        'projectStatus': data.get('Status'),
        'projectType': data.get('Project Type'),
        'promoterType': ViewProjectDetail['Promoter Details'].get('Promoter Type', None),
        'projectStateName': "Karnataka",
        'projectPinCode': ViewProjectDetail['Project Details'].get('Pin Code', None),
        'projectDistrictName': data.get('District'),
        'projectVillageName': data.get('Taluk'),
        'projectAddress': ViewProjectDetail['Project Details'].get('Project Address', None),
        'totalLandArea': ViewProjectDetail['Project Details'].get('Total Area Of Land (Sq Mtr)', None),
        'promotersAddress': ViewProjectDetail['Promoter Details'].get('Address', None),
        'landownerTypes': None,
        'promoterPinCode': ViewProjectDetail['Promoter Details'].get('PIN Code', None),
        'longitude': ViewProjectDetail['Project Details'].get('East Longitude', None),
        'latitude': ViewProjectDetail['Project Details'].get('South Latitude', None),
        'viewLink': "https://rera.karnataka.gov.in",
    }

    return project_data


def get_project_details(project_id):
    # Define the URL and headers
    url = "https://rera.karnataka.gov.in/projectDetails"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Define the payload (Project ID)
    payload = {"action": project_id}

    # Send the POST request
    response = requests.post(url, headers=headers, data=payload, verify=False,timeout=1000)

    # Check if request was successful
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        promoter_details = {}
        promoter_section = soup.find("div", class_="tab-content").find("div", id="home")
        if promoter_section:
            rows = promoter_section.find_all("div", class_="row")
            for row in rows:
                columns = row.find_all("p")
                if len(columns) >= 2:
                    key = columns[0].get_text(strip=True).replace(":", "").strip()
                    value = columns[1].get_text(strip=True).strip()
                    promoter_details[key] = value

        #  Extract certificate link
        cert_link = promoter_section.find("a", href=True)
        if cert_link:
            promoter_details["Certificate"] = "https://rera.karnataka.gov.in" + cert_link["href"]

        #  Extract project members
        project_members = []
        project_member_section = promoter_section.find("h1",
                                                       string=lambda text: "Project Member" in text if text else False)
        if project_member_section:
            member_rows = project_member_section.find_next("div", class_="inner_wrapper").find_all("div", class_="row")
            for i in range(0, len(member_rows), 3):
                member_info = {
                    "Name": member_rows[i].find_all("p")[1].text.strip(),
                    "Type": member_rows[i + 1].find_all("p")[1].text.strip(),
                    "Address": member_rows[i + 2].find_all("p")[1].text.strip(),
                    "Pin Code": member_rows[i + 2].find_all("p")[3].text.strip()
                }
                # Extract photograph link
                photo_link = member_rows[i + 3].find("a", href=True)
                if photo_link:
                    member_info["Photograph"] = "https://rera.karnataka.gov.in" + photo_link["href"]
                project_members.append(member_info)

        promoter_details["Project Members"] = project_members

        # Extract Project Details
        project_details = {}
        project_section = soup.find("div", class_="tab-content").find("div", id="menu2")

        # Check if `menu2` contains the `<h1>Project <span> Details</span></h1>` tag
        if project_section and project_section.find("h1",
                                                    string=lambda text: "Project Details" in text if text else False):
            print(" Extracting Project Details from `menu2`")
        else:
            # If `menu2` is not found or does not contain the `Project Details` tag, check `menu1`
            project_section = soup.find("div", class_="tab-content").find("div", id="menu1")
            print(" Extracting Project Details from `menu1`")

        if project_section:
            rows = project_section.find_all("div", class_="row")
            for row in rows:
                columns = row.find_all("p")
                if len(columns) >= 2:
                    key = columns[0].get_text(strip=True).replace(":", "").strip()
                    value = columns[1].get_text(strip=True).strip()
                    project_details[key] = value

        #  Extract Latitude and Longitude **Correctly**
        lat_lon_data = {}
        lat_lon_pairs = ["North", "East", "West", "South"]

        for row in project_section.find_all("div", class_="row"):
            columns = row.find_all("p")
            if len(columns) == 4:
                lat_label = columns[0].get_text(strip=True).replace(":", "").strip()
                lat_value = columns[1].get_text(strip=True).strip()
                lon_label = columns[2].get_text(strip=True).replace(":", "").strip()
                lon_value = columns[3].get_text(strip=True).strip()

                if any(direction in lat_label for direction in lat_lon_pairs):
                    lat_lon_data[lat_label] = lat_value
                    lat_lon_data[lon_label] = lon_value

        #  Add the correct latitude/longitude pairs to project details
        project_details.update(lat_lon_data)

        extracted_data = {
            "Promoter Details": promoter_details,
            "Project Details": project_details
        }

        return extracted_data


# Define Base URL
BASE_URL = "https://rera.karnataka.gov.in/projectViewDetails"

# User-Agents for rotation (prevents blocking)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0",
]

# Create a session
session = requests.Session()

# Project name filters to search
PROJECT_NAMES = ["Ltd", "Limited", "Llp", "Bank"]
# PROJECT_NAMES = ["Ltd"]


def get_districts():
    """Fetch district names by sending a POST request with the same payload used for project search."""

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": BASE_URL,
        "Origin": BASE_URL,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Send a POST request with "Ltd" as the project name
    payload = {
        "project": "Ltd",
        "firm": "",
        "appNo": "",
        "regNo": "",
        "district": "0",
        "subdistrict": "0",
        "btn1": "Search"
    }

    response = session.post(BASE_URL, data=payload, headers=headers, timeout=1000, verify=False)

    if response.status_code != 200:
        print(f" Failed to fetch districts. Status Code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the district dropdown
    district_dropdown = soup.find("select", {"id": "projectDist"})

    if not district_dropdown:
        print(" District dropdown not found. The site structure may have changed.")
        return []

    # Extract district options (skip first one)
    districts = [option.text.strip() for option in district_dropdown.find_all("option") if option["value"] != "0"]

    if not districts:
        print("District list is empty. JavaScript might be loading it dynamically.")
        return []

    print(f"Found {len(districts)} districts: {districts}")
    return districts


def get_project_detail(district, project_name):
    """Fetch all project details for a given district and project name."""
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": BASE_URL,
        "Origin": BASE_URL,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {
        "project": project_name,
        "firm": "",
        "appNo": "",
        "regNo": "",
        "district": district,
        "subdistrict": "0",
        "btn1": "Search"
    }

    response = session.post(BASE_URL, data=payload, headers=headers, verify=False,timeout=1000)

    if response.status_code != 200:
        print(f" Failed to fetch projects for {district} - {project_name}. Status Code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    project_details = []

    table = soup.find("table", {"id": "approvedTable"})
    if not table:
        print(f" No projects found for {district} - {project_name}")
        return []

    rows = table.find_all("tr")[1:]  # Skip header row

    for row in rows:
        cols = row.find_all("td")
        if len(cols) > 16:
            project_id = cols[3].find("a")["id"] if cols[3].find("a") and cols[3].find("a").has_attr("id") else "N/A"
            certificate_link = "https://rera.karnataka.gov.in" + cols[16].find("a")["href"] if cols[16].find("a") and \
                                                                                               cols[16].find(
                                                                                                   "a").has_attr(
                                                                                                   "href") else "N/A"
            complaint_link = "https://rera.karnataka.gov.in" + cols[20].find("a")["href"] if cols[20].find("a") and \
                                                                                             cols[20].find(
                                                                                                 "a").has_attr(
                                                                                                 "href") else "N/A"

            data = {
                "S.No": cols[0].text.strip(),
                "Acknowledgement No": cols[1].text.strip(),
                "Registration No": cols[2].text.strip(),
                "Project ID": project_id,
                "Promoter Name": cols[4].text.strip(),
                "Project Name": cols[5].text.strip(),
                "Status": cols[6].text.strip(),
                "District": cols[7].text.strip(),
                "Taluk": cols[8].text.strip(),
                "Project Type": cols[9].text.strip(),
                "Approved On": cols[10].text.strip(),
                "Proposed Completion Date": cols[11].text.strip(),
                "Completion Date (Registration)": cols[12].text.strip(),
                "Covid-19 Extension Date": cols[13].text.strip(),
                "Section 6 Extension Date": cols[14].text.strip(),
                "Further Extension Date": cols[15].text.strip(),
                "Certificate Link": certificate_link,
                "Complaint Link": complaint_link,
            }

            if project_id == 'N/A' or project_id == None:
                continue
            ViewProjectDetail = get_project_details(project_id)
            final_data = get_final_payload(data, ViewProjectDetail)
            print(final_data)
            write_to_MargeFile(final_data,"Karnataka")

    print(f" Found {len(project_details)} projects for {district} - {project_name}")



# **Main Execution**
def rera_karnataka():
    all_districts = get_districts()

    if all_districts:

        for district in all_districts:

            for project in PROJECT_NAMES:

                get_project_detail(district, project)


    else:
        print("No districts retrieved.")
