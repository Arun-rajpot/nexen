import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from Scripts.write_to_txt_file import write_to_MargeFile


def convert_date_format(date_str):
    formats = [
        "%d-%m-%Y %I:%M:%S %p",  # e.g. 10-06-2019 03:45:39 AM
        "%d-%m-%Y",  # e.g. 31-03-2020
        "%Y-%m-%dT%H:%M:%S.%f%z"  # e.g. 2023-03-17T00:00:00.000+0530
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except:
            continue
    return None


def get_final_payload(data, combined_data):
    project_data = {
        'projectCin': None,
        'promoterCin': None,
        'projectName': data.get('Project Name'),
        'promoterName': data.get('Builder'),
        'acknowledgementNumber': data.get('Registration Certificate Number'),
        'projectRegistrationNo': data.get('Project ID_text'),
        'reraRegistrationDate': convert_date_format(combined_data.get("Submission Date", None)),
        'projectProposeCompletionDate': convert_date_format(
            combined_data.get("ii) Likely date of completing the project", None)),
        'projectStatus': combined_data.get("Project Type", None),
        'projectType': combined_data.get("Applicant Type", None),
        'promoterType': None,
        'projectStateName': "Haryana",
        'projectPinCode': None,
        'projectDistrictName': data.get('District'),
        'projectVillageName': data.get('Tehsil'),
        'projectAddress': data.get('Project Location', None),
        'totalLandArea': combined_data.get('1. Land area of the project', None),
        'promotersAddress': None,
        'landownerTypes': None,
        'promoterPinCode': None,
        'longitude': None,
        'latitude': None,
        'viewLink': data.get('Details of Project_link'),
    }
    return project_data


def rera_haryana():
    for sector in [1, 2]:
        url = "https://haryanarera.gov.in/admincontrol/registered_projects/" + str(sector)
        base_url = "https://haryanarera.gov.in"
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")

        # Extract the table with ID 'compliant_hearing'
        table = soup.find("table", {"id": "compliant_hearing"})

        # Extract table data with hyperlinks only where they exist
        if table:
            rows = table.find("tbody").find_all("tr")

            # Define table headers as keys
            headers = [
                "Serial No.", "Registration Certificate Number", "Project ID", "Project Name",
                "Builder", "Project Location", "Project District", "Registered With",
                "Details of Project", "Registration Up-to", "View Certificate",
                "View Quarterly Progress", "Monitoring Orders", "View OC/CC/PCC"
            ]

            # Extract data
            data = []
            for row in rows:
                cols = row.find_all("td")
                row_data = {}
                for i, col in enumerate(cols):
                    link = col.find("a")
                    if link and link.get("href"):
                        row_data[f"{headers[i]}_link"] = link["href"]
                        row_data[f"{headers[i]}_text"] = col.get_text(" ", strip=True)
                    else:
                        row_data[headers[i]] = col.get_text(" ", strip=True)
                data.append(row_data)

            # Print extracted data
            for d in data:
                # print(row)
                if d.get('Details of Project_link'):
                    details_url = d['Details of Project_link']
                    details_res = requests.get(details_url)
                    details_soup = BeautifulSoup(details_res.text, "html.parser")

                    tables = details_soup.find_all("table")
                    combined_data = {}

                    for table in tables:
                        rows = table.find_all("tr")
                        for row in rows:
                            cells = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"]) if
                                     cell.get_text(strip=True)]

                            if not cells:
                                continue

                            # Handle 2-column table: key and value
                            if len(cells) == 2:
                                key_text = cells[0]
                                value_text = cells[1]
                            # Handle 3-column table: key in 1st cell, value in 3rd
                            elif len(cells) == 3:
                                key_text = cells[0]
                                value_text = cells[2]
                            # Handle 1-column (probably heading)
                            elif len(cells) == 1:
                                key_text = cells[0]
                                value_text = None
                            else:
                                # More columns, join intelligently
                                key_text = " | ".join(cells[:-1])
                                value_text = cells[-1]

                            # Try to split key_text if colon exists
                            if ":" in key_text:
                                parts = key_text.split(":", 1)
                                key = parts[0].strip()
                                if value_text:
                                    value = value_text
                                else:
                                    value = parts[1].strip()
                            else:
                                key = key_text.strip()
                                value = value_text.strip() if value_text else None

                            combined_data[key] = value

                    final_data = get_final_payload(d, combined_data)
                    print(final_data)
                    write_to_MargeFile(final_data, "Haryana")

#
# if __name__ == "__main__":
#     rera_haryana()
