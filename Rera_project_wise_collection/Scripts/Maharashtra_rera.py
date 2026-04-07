import requests
from bs4 import BeautifulSoup
import json
from Scripts.write_to_txt_file import write_to_MargeFile




def get_deatls(project_ids, userProfileId, main_url):
    login_url = "https://maharerait.maharashtra.gov.in/api/maha-rera-login-service/login/authenticatePublic"

    # Define headers for the login request
    login_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "Content-Type": "application/json"
    }

    # Define login payload with encrypted username and password
    login_payload = {
        "userName": "U2FsdGVkX18FBgXEF4XRNf+gGFv8PlfIVqYtmbpvY/B5qY1VlwFM+ZzSR9kbvi94",
        "password": "U2FsdGVkX19lXke2ksIFRN1dinwxW6NdTBqTGUXr4rg="
    }
    # Send login request to get access token
    response = requests.post(login_url, json=login_payload, headers=login_headers, verify=False)
    response.raise_for_status()

    # Extract access token from the response
    access_token = response.json().get('responseObject', {}).get('accessToken')

    if not access_token:
        raise Exception("Failed to retrieve access token")

    # Now, use the access token for the next API request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Define the payload for the latitude and longitude request
    project_payload = {
        "projectId": project_ids,
        "userProfileId": userProfileId
    }

    # Send request to get project latitude and longitude details
    response_1 = requests.post(main_url, json=project_payload, headers=headers, verify=False)
    response_1.raise_for_status()

    # Parse and print the project details
    data_1 = response_1.json().get('responseObject', {})

    return data_1


def get_project_details(project_ids):
    url_1 = "https://maharerait.maharashtra.gov.in/api/maha-rera-project-registration-service/projectregistartion/getProjectGeneralDetailsByProjectId"
    url_2 = "https://maharerait.maharashtra.gov.in/api/maha-rera-project-registration-service/projectregistartion/getProjectAndAssociatedPromoterDetails"

    final_data = []

    for project_id in project_ids:
        payload = {"projectId": project_id}

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            }

            # -----------------------------------Request for general project details------------------------------------
            response_1 = requests.post(url_1, json=payload, headers=headers, verify=False, timeout=10)
            response_1.raise_for_status()
            data_1 = response_1.json().get('responseObject', {})

            # -------------------------Request for promoter details------------------------------------
            response_2 = requests.post(url_2, json=payload, headers=headers, verify=False, timeout=10)
            response_2.raise_for_status()
            data_2 = response_2.json().get('responseObject', {})
            # print(data_2)
            # ---------------------------------get Promoter Type -----------------------------------------
            userProfileId = data_1["userProfileId"]
            Promoter_Type_url = "https://maharerait.maharashtra.gov.in/api/maha-rera-promoter-management-service/promoter/fetchPromoterGeneralDetails"
            data_3 = get_deatls(project_id, userProfileId, Promoter_Type_url)
            # print(data_3)

            # ---------------------------------get latitude_longitude -----------------------------------------
            latitude_longitude_url = "https://maharerait.maharashtra.gov.in/api/maha-rera-project-registration-service/projectregistartion/getProjectLegalGeoTaggingDetailByProjectId"
            data_4 = get_deatls(project_id, userProfileId, latitude_longitude_url)
            print(data_4)

            # ---------------------------------get totalLandArea -----------------------------------------
            totalLandArea_url = "https://maharerait.maharashtra.gov.in/api/maha-rera-project-registration-service/projectregistartion/getProjectLandHeaderDetails"
            data_5 = get_deatls(project_id, userProfileId, totalLandArea_url)
            # print(data_5)

            project_data = {
                'projectCin':None,
                'promoterCin': None,
                'projectName': data_1.get('projectName', None),
                'promoterName': data_2.get('promoterDetails', {}).get('promoterName', None),
                'acknowledgementNumber': data_1.get('acknowledgementNumber', None),
                'projectRegistrationNo': data_1.get('projectRegistartionNo', None),
                'reraRegistrationDate': data_1.get('reraRegistrationDate', None),
                'projectProposeCompletionDate': data_1.get('projectProposeComplitionDate', None),
                'projectStatus': data_1.get('projectStatusName', None),
                'projectType': data_1.get('projectTypeName', None),
                'promoterType': data_3.get('userProfileTypeName', None),
                'projectStateName': data_2.get('projectDetails', {}).get('projectLegalLandAddressDetails', {}).get(
                    'stateName', None),
                'projectPinCode': data_2.get('projectDetails', {}).get('projectLegalLandAddressDetails', {}).get(
                    'pinCode', None),
                'projectDistrictName': data_2.get('projectDetails', {}).get('projectLegalLandAddressDetails', {}).get(
                    'districtName', None),
                'projectVillageName': data_2.get('projectDetails', {}).get('projectLegalLandAddressDetails', {}).get(
                    'villageName', None),
                'projectAddress': data_2.get('projectDetails', {}).get('projectLegalLandAddressDetails', {}).get(
                    'addressLine', None),
                'totalLandArea': data_5.get('landAreaSqmts', None),
                # 'promotersStateName':data_2.get('promoterDetails', {}).get('stateName', None),
                'promotersAddress': data_2.get('promoterDetails', {}).get('districtName', None),
                'landownerTypes': None,
                'promoterPinCode': str(data_2.get('promoterDetails', {}).get('pincode', '')) if data_2.get('promoterDetails', {}).get('pincode') is not None else None,
                'longitude': data_4.get('longitude', None),
                'latitude': data_4.get('latitude', None),
                'viewLink': f"https://maharerait.maharashtra.gov.in/project/view/{project_id}"
            }

            final_data.append(project_data)

        except requests.exceptions.RequestException as err:
            print(f"Request error for projectId {project_id}: {err}")
        except KeyError as err:
            print(f"Key error for projectId {project_id}: Missing key {err}")

    return final_data


def rera_maharashtra():
    url = "https://maharera.maharashtra.gov.in/projects-search-result"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    project_names = ["Ltd", "Limited", "Llp", "Bank"]

    for projectName in project_names:
        page_count = 1

        while True:
            params = {
                "project_name": projectName,
                "project_state": "27",
                "project_district": "0",
                "page": str(page_count),
                "op": "Search"
            }

            try:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code != 200:
                    print(f"Failed to retrieve data. Status Code: {response.status_code}")
                    break

                soup = BeautifulSoup(response.content, "html.parser")
                projects = soup.find_all("div", class_="row shadow p-3 mb-5 bg-body rounded")

                if not projects:
                    break  # No more projects found, exit loop

                project_ids = []

                for project in projects:
                    project_id_elem = project.find("a", title="View Details")
                    if project_id_elem and "href" in project_id_elem.attrs:
                        project_id = project_id_elem["href"].split("/")[-1].strip()
                        project_ids.append(project_id)

                if project_ids:
                    final_data = get_project_details(project_ids)
                    for data in final_data:
                        print(data)
                        write_to_MargeFile(data,"Maharashtra")

                page_count += 1  # Move to the next page

            except requests.exceptions.RequestException as err:
                print(f"Error fetching project data: {err}")
                break  # Stop if an error occurs



# rera_maharashtra()
