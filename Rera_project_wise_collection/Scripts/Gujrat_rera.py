import requests
import ssl
from requests.adapters import HTTPAdapter
from datetime import datetime
import json
from Scripts.write_to_txt_file import write_to_MargeFile

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.load_verify_locations(r"D:\Rera_project\Reraproject\rera_scraping_app\security\___.gujarat.gov.in.crt")
        context.options |= ssl.OP_LEGACY_SERVER_CONNECT
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)


# def write_to_MargeFile(newline):
#     file_path = r"D:\\Rera_new_collection\\New_Rera_gujrat.txt"
#     with open(file_path, 'a', encoding='utf-8') as text_file:
#         json_line = json.dumps(newline, ensure_ascii=False)
#         text_file.write(json_line)
#         text_file.write(",\n")


def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except:
        return None


def convert_date_format(date_str):
    try:
        # Handles formats like '2023-03-17T00:00:00.000+0530'
        return datetime.strptime(date_str.split('T')[0], "%Y-%m-%d").strftime("%Y-%m-%d")
    except:
        return None


def get_final_payload(projectdetails, promoterdetails, promoterID):
    reraRegistrationDate = convert_date_format(projectdetails.get('startDate'))
    projectProposeCompletionDate = convert_date_format(projectdetails.get('completionDate'))

    project_data = {
        'projectCin': None,
        'promoterCin': None,
        'projectName': projectdetails.get('projectName'),
        'promoterName': promoterdetails.get('promoterName'),
        'acknowledgementNumber': promoterID.get("projectAckNo"),
        'projectRegistrationNo': promoterID.get("projRegNo"),
        'reraRegistrationDate': reraRegistrationDate,
        'projectProposeCompletionDate': projectProposeCompletionDate,
        'projectStatus': projectdetails.get('projectStatus'),
        'projectType': projectdetails.get('projectType'),
        'promoterType': promoterdetails.get('promoterType'),
        'projectStateName': projectdetails.get('stateName'),
        'projectPinCode': projectdetails.get('pinCode'),
        'projectDistrictName': projectdetails.get('distName'),
        'projectVillageName': projectdetails.get('subDistName'),
        'projectAddress': projectdetails.get('projectAddress'),
        'totalLandArea': projectdetails.get('totAreaOfLand'),
        'promotersAddress': promoterdetails.get('address2'),
        'landownerTypes': None,
        'promoterPinCode': promoterdetails.get('pinCode'),
        'longitude': None,
        'latitude': None,
        'viewLink': f"https://gujrera.gujarat.gov.in/#/",
    }

    return project_data


def get_promoterdetailsID(projectId, session):
    projectdetails_url = "https://gujrera.gujarat.gov.in/project_reg/public/alldatabyprojectid/" + str(projectId)
    projectdetails_res = session.get(projectdetails_url)
    data = projectdetails_res.json()
    # print("=====get_promoterdetails======",data["data"])
    return data["data"]


def get_promoterdetails(promotorID, session):
    projectdetails_url = "https://gujrera.gujarat.gov.in/user_reg/promoter/promoter" + str(promotorID)
    projectdetails_res = session.get(projectdetails_url)
    data = projectdetails_res.json()
    # print("=====get_promoterdetails======",data)
    return data


def get_projectdetails(projectId, session):
    projectdetails_url = "https://gujrera.gujarat.gov.in/project_reg/public/getproject-details/" + str(projectId)
    projectdetails_res = session.get(projectdetails_url)
    data = projectdetails_res.json()
    # print(data)
    # print("=====get_projectdetails======",data["data"]["projectDetail"])
    return data["data"]["projectDetail"]


def rera_gujarat():
    session = requests.Session()
    session.mount('https://', SSLAdapter())
    url = "https://gujrera.gujarat.gov.in/project_reg/public/global-search"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://gujrera.gujarat.gov.in",
        "Referer": "https://gujrera.gujarat.gov.in/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }

    payload = {
        "query": "Ltd",
        "startWith": 0,
        "dataSize": 25
    }

    response = session.post(url, headers=headers, json=payload)

    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    alldata = response.json()['data']
    for data in alldata:
        if data["entityType"] == "PROJECT":
            # print("====data===",data)
            projectdetails = get_projectdetails(data['entityId'], session)
            promoterID = get_promoterdetailsID(data['entityId'], session)
            promoterdetails = get_promoterdetails(promoterID['promoterId'], session)
            final_data = get_final_payload(projectdetails, promoterdetails, promoterID)
            print(final_data)
            write_to_MargeFile(final_data,"Gujarat")


# rera_gujarat()