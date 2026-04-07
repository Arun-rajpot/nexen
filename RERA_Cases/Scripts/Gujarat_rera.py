import json
import requests
import ssl
from requests.adapters import HTTPAdapter
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload


class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.load_verify_locations(r"D:\Rera_project\Reraproject\rera_scraping_app\security\___.gujarat.gov.in.crt")  # Load your specific certificate
        context.options |= ssl.OP_LEGACY_SERVER_CONNECT  # Enable legacy renegotiation
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)





def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string in value.title():

                final_payload = {
                    'Estate': "Gujarat Real Estate Regulatory Authority",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get("complaintant_fname").replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip() if dictionary.get("complaintant_fname") else None,
                    'Respondent': dictionary.get("res_respondent_fname").replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip() if dictionary.get("res_respondent_fname") else None,
                    'Complaint_Number': dictionary.get("aknowledgement_no"),
                    'Project_Registration_Number': dictionary.get("proj_reg_no") or dictionary.get("projRegNo"),
                    'Application_date': None,
                    'order_date': dictionary.get("judg_pub_date") or dictionary.get("sch_date"),
                    'project_name': dictionary.get("projectName") or dictionary.get("projName"),
                    'Order_Under_Section': None,
                    'district':dictionary.get("project_distric") or dictionary.get("dist"),
                    'status':dictionary.get("judge_type") or dictionary.get("currentStatus"),
                    'Remarks': dictionary.get("remarks"),
                    'other_detail':None,
                    'pdf_link': None
                }
                if final_payload['Applicant'] or final_payload['Respondent'] is not None:
                    return final_payload
    return None

def rera_Gujarat():
    session = requests.Session()
    session.mount('https://', SSLAdapter())

    urls = [
        "https://gujrera.gujarat.gov.in/complain/ecourt/public/find-all/complaints/null",
        "https://gujrera.gujarat.gov.in/complain/find-all-hearing-details/ALL/ALL/null/null"
    ]
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }
    
    for url in urls:
        response = session.get(url, headers=headers)
        print(response.status_code)
        if response.status_code == 200:
            r_json = response.text
            r_data = json.loads(r_json)
            targets = ['Ltd', 'Limited', 'Llp', 'LTD', 'LLP', 'LIMITED']
            datas = r_data['data']

            for data in datas:
                res_respondent_fname = data.get("res_respondent_fname")

                # Check if there is a comma in res_respondent_fname
                if res_respondent_fname and "," in res_respondent_fname:
                    res_list = res_respondent_fname.split(",")

                    # Filter the list to keep only those items that contain any of the target words
                    filtered_res_list = [res.strip() for res in res_list if any(target in res for target in targets)]

                    # Join the filtered list back into a single string and store it in data["res_respondent_fname"]
                    data["res_respondent_fname"] = ", ".join(filtered_res_list)
                # print(data)
                result = find_strings_in_dict(data, targets)
                if result is not None:
                    split_data = split_payload(result)
                    for sdata in split_data:
                        print("At least one target string found in the dictionary.")
                        print("Resulting dictionary:", sdata)
                        write_to_MargeFile(sdata,"Gujarat")




