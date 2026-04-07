import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from Scripts.write_to_txt_file import write_to_MargeFile



def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except:
        try:
            return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
        except:
            return None

def get_final_payload(data, ViewProjectDetail,project_url):
    general = ViewProjectDetail.get("general_info", {})
    project_info = ViewProjectDetail.get("project_info", {})
    location = ViewProjectDetail.get("location_info", {})
    promoter = ViewProjectDetail.get("promoter_info_other_than_individual", {})
    address = promoter.get("official_address", {})

    # Final mapped data
    project_data = {
        'projectCin': None,
        'promoterCin': None,
        'projectName': general.get("project_name"),
        'promoterName': general.get("promoter_name"),
        'acknowledgementNumber': None,
        'projectRegistrationNo': general.get("certificate_no"),
        'reraRegistrationDate': convert_date_format(general.get("last_modified_date")),
        'projectProposeCompletionDate': convert_date_format(project_info.get("proposed_completion")),
        'projectStatus': data.get("status"),
        'projectType': general.get("project_type"),
        'promoterType': promoter.get("org_type"),
        'projectStateName': location.get("state", "KERALA"),
        'projectPinCode': location.get("pin_code"),
        'projectDistrictName': location.get("district"),
        'projectVillageName': location.get("taluk"),
        'projectAddress': f"{address.get('house_no', '')}, {address.get('street_name', '')}, {address.get('locality', '')}, {address.get('landmark', '')}".strip(', '),
        'totalLandArea': project_info.get("total_land_area"),
        'promotersAddress': f"{address.get('house_no', '')}, {address.get('street_name', '')}, {address.get('locality', '')}, {address.get('landmark', '')}".strip(', '),
        'landownerTypes': None,
        'promoterPinCode': address.get("pin_code"),
        'longitude': None,
        'latitude': None,
        'viewLink': project_url,
    }

    return project_data

def get_label_value(soup, label_text):
    label = soup.find(lambda tag: tag.name == "label" and label_text in tag.text)
    if label and label.next_sibling:
        return label.next_sibling.strip()
    return None

def get_col_value(soup,label_text):
    div = soup.find(lambda tag: tag.name == "label" and label_text in tag.text)
    if div and div.parent:
        return div.parent.text.replace(label_text, "").strip()
    return None



def rera_kerala():
    page = 1
    while True:
        url = f"https://rera.kerala.gov.in/explore-projects?page={page}"
        print(f"Scraping Page: {page} -> {url}")
        time.sleep(0.5)
        res = requests.get(url,timeout=100)
        soup = BeautifulSoup(res.text, "html.parser")
        data_tag = soup.find('div', class_="mt-10 flex w-full flex-col gap-10")

        if not data_tag:
            print("No data section found. Ending pagination.")
            break

        filnd_projects = data_tag.find_all("a",
                                           class_="flex w-full cursor-pointer flex-wrap rounded-xl bg-primary-50 p-3 text-black shadow outline-8 hover:shadow-xl md:p-10")
        if not filnd_projects:
            print("No more projects found. Ending pagination.")
            break

        for a_tag in filnd_projects:
            try:

                rera_id_span = next((span.text.strip() for span in a_tag.find_all('span') if 'K-RERA' in span.text),
                                    None)
                status = a_tag.find('span', class_="bg-gray-500").text.strip() if a_tag.find('span', class_="bg-gray-500") else None
                result = {
                    "project_name": a_tag.find('h1').text.strip(),
                    "rera_id": rera_id_span,
                    "status": status,
                    # "location": a_tag.find_all('b')[1].text.strip(),
                    # "proposed_completion": a_tag.find(string="Proposed Completion On").find_next('b').text.strip(),
                    # "total_area": a_tag.find(string="Total Area").parent.text.strip(),
                    "href": "https://rera.kerala.gov.in" + a_tag.get('href')
                }

                get_project_url = result['href']
                time.sleep(0.5)
                print("get_project_url====",get_project_url)
                res_project_url = requests.get(get_project_url,timeout=100)
                project_url_soup = BeautifulSoup(res_project_url.text, 'html.parser')
                preview_link_tag = project_url_soup.find('a', string="Complete Project Details") or project_url_soup.find('a', string="COMPLETE PROJECT DETAILS")
                # print("preview_link_tag=====",preview_link_tag)
                if not preview_link_tag:
                    print(f"No 'Complete Project Details' found for {get_project_url}")
                    continue
                time.sleep(0.5)
                final_res = requests.get(preview_link_tag.get('href'),timeout=100)
                project_soup = BeautifulSoup(final_res.text, 'html.parser')

                # General Info
                data = {
                    'certificate_no': get_label_value(project_soup, 'Certificate No'),
                    'project_name': get_label_value(project_soup, 'Project Name'),
                    'promoter_name': get_label_value(project_soup, 'Promoter Name'),
                    'project_type': get_label_value(project_soup, 'Project Type'),
                    'last_modified_date': project_soup.select_one(
                        '#lbllastDate').text.strip() if project_soup.select_one('#lbllastDate') else None,
                    'project_status': project_soup.select_one(
                        'label:contains("Project Status") + span') and project_soup.select_one(
                        'label:contains("Project Status") + span').text.strip(),
                    'project_land_area': get_label_value(project_soup, 'Project Land Area')
                }

                # Project Info
                project_info = {
                    'proposed_commencement': get_label_value(project_soup, 'Proposed date of Commencement'),
                    'proposed_completion': get_label_value(project_soup, 'Proposed Date of Completion'),
                    'total_land_area': get_label_value(project_soup, 'Total Land Area'),
                }

                # Location Info
                location_info = {
                    'state': get_label_value(project_soup, 'State'),
                    'district': get_label_value(project_soup, 'District'),
                    'taluk': get_label_value(project_soup, 'Taluk'),
                    'village': get_label_value(project_soup, 'Village'),
                    'pin_code': get_label_value(project_soup, 'Pin Code'),
                }

                # Promoter Info
                promoter_info = {
                    'org_type': get_col_value(project_soup, 'Organization Type'),
                    'org_name': get_col_value(project_soup, 'Name of the Organization'),
                    'official_address': {
                        'house_no': get_col_value(project_soup, 'House Number/ Building Name'),
                        'street_name': get_col_value(project_soup, 'Street Name'),
                        'locality': get_col_value(project_soup, 'Locality'),
                        'landmark': get_col_value(project_soup, 'Landmark'),
                        'state': get_col_value(project_soup, 'State/ UT'),
                        'district': get_col_value(project_soup, 'District'),
                        'taluk': get_col_value(project_soup, 'Taluk'),
                        'municipality': get_col_value(project_soup, 'Panchayat/ Municipality/ Corporation'),
                        'pin_code': get_col_value(project_soup, 'Pin Code')
                    }
                }

                # Final Output
                full_project_data = {
                    'general_info': data,
                    'project_info': project_info,
                    'location_info': location_info,
                    'promoter_info_other_than_individual': promoter_info
                }

                final_data = get_final_payload(result, full_project_data, get_project_url)
                print(final_data)
                write_to_MargeFile(final_data,"Kerala")
                print("==========================================================================")

            except Exception as e:
                print(f"Error processing project: {e}")
                continue

        page += 1

# rera_kerala()
