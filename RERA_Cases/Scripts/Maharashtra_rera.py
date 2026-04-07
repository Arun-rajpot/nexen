import json
import requests
from bs4 import BeautifulSoup
from django.http import HttpResponse
from datetime import datetime
import ssl
from requests.adapters import HTTPAdapter
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload



current_date = datetime.now().strftime("%d-%m-%Y")

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.load_verify_locations(r"D:\Rera_project\Reraproject\rera_scraping_app\security\maharera.maharashtra.gov.in.crt")  # Load your specific certificate
        context.options |= ssl.OP_LEGACY_SERVER_CONNECT  # Enable legacy renegotiation
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

session = requests.Session()
session.mount('https://', SSLAdapter())


def find_strings_in_dict(dictionary, target_strings, is_first_function=True):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string in value.title():
                if is_first_function:
                    final_payload = {
                        'Estate': "Maharashtra Real Estate Regulatory Authority",
                        'Applicant_Cin': None,
                        'Respondent_Cin': None,
                        'Applicant': dictionary.get('appellant_name').replace('M/s.','').replace('\n','').replace('M/S','').replace('M/s','').strip() if dictionary.get('appellant_name') else None,
                        'Respondent': dictionary.get('respondent_name').replace('M/s.','').replace('\n','').replace('M/S','').replace('M/s','').strip() if dictionary.get('respondent_name') else None,
                        'Complaint_Number': dictionary.get("appeal_no"),
                        'Project_Registration_Number': None,
                        'Application_date': dictionary.get('doc_upload_date'),
                        'order_date': dictionary.get('judgment_order_date'),
                        'project_name':None ,
                        'Order_Under_Section': None,
                        'district':None,
                        'status':None,
                        'Remarks': dictionary.get('judgment_order_type'),
                        'other_detail':dictionary.get('judgment_order_subject'),
                        'pdf_link': "https://mahareat.maharashtra.gov.in/online/judgements/tribunal"
                    }

                    return final_payload
    return None

def rera_MH_1():
    url = "https://mahareat.maharashtra.gov.in:8085/api/Public/Getjudgment_orderBySubjectDate"
    payload = {'_subject': None, '_fromdate': None, '_todate': None}
    
    response = requests.post(url, json=payload,verify=False)
    response_data = response.text

    json_data = json.loads(response_data)

    targets = ["Ltd", "Llp", "Limited", "Bank"]
    for data in json_data["result"]:
        # print(data)
        # break
        if data['appeal_no']:
            if "Appeal No." in data['appeal_no']:
                appeal_no = data['appeal_no'].split("Appeal No.")[1].strip()
                data['appeal_no'] = appeal_no
            else:
                appeal_no = None
                data['appeal_no'] = appeal_no
        else:
            appeal_no = None
            data['appeal_no'] = appeal_no

        for key in data:
            if data[key] == '-' or data[key] == '':
                data[key] = None
            
        result = find_strings_in_dict(data, targets, is_first_function=True)
        if result is not None:
            split_data = []
            split_data.extend(split_payload(result))
            for sdata in split_data:
                print("At least one target string found in the dictionary.")
                print("Resulting dictionary:", sdata)
                write_to_MargeFile(sdata,"Maharashtra")




def find_strings_in_dict_2(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string in value.title():


                final_payload = {
                    'Estate': "Maharashtra Real Estate Regulatory Authority",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get("Complainant Name") ,
                    'Respondent': dictionary.get("Respondent Name") ,
                    'Complaint_Number': dictionary.get("Complaint No.") ,
                    'Project_Registration_Number': dictionary.get("Project Registration No."),
                    'Application_date': None,
                    'order_date': dictionary.get("Next Hearing Date"),
                    'project_name': None, 
                    'Order_Under_Section': None,
                    'district':None,
                    'status':dictionary.get("Stage"),
                    'Remarks': None,
                    'other_detail':None,
                    'pdf_link': None
                }
                return final_payload
    return None

def mh_2():
    
    url = "https://maharera.maharashtra.gov.in/monthlys-cause-list"
    payload = {
        'from_date': '01-01-2021',
        'to_date': current_date,
        'op': 'Search',
        'form_build_id': 'form-31D8sjV3fK-Bd5hiIv9pgpx0KdhWBgWGiNo0tBwDGR4',
        'form_id': 'monthly_cause_list_form'
    }
    
    # Send GET request
    response = session.get(url, params=payload)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Locate and extract all table data
    all_data = []
    tables = soup.find_all('table', {'class': 'tableData responsiveTable tableScroll mb-5'})
    
    for table in tables:
        headers = [header.get_text(strip=True) for header in table.find_all('th')]
        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            if len(cells) == len(headers):
                row_data = {headers[i]: cells[i].get_text(strip=True) for i in range(len(headers))}
                all_data.append(row_data)

    
    # Print data for verification
    check_cname = ["Ltd", "Llp", "Limited", "Bank"]
    
    for item in all_data:
        orderdate = item["Next Hearing Date"].split(" ")[0] if  item["Next Hearing Date"] else None
        item["Next Hearing Date"] = orderdate
        for key in item:
            if item[key] == '-' :
                item[key] = None
        
        result = find_strings_in_dict_2(item, check_cname)
        if result is not None:
            split_data = split_payload(result)
            for sdata in split_data:
                print("At least one target string found in the dictionary.")
                print("Resulting dictionary:", sdata)
                write_to_MargeFile(sdata,"Maharashtra")

def rera_Maharashtra():
    print("Processing Defaulter List...")
    rera_MH_1()
    print("Processing Withdrawn Project List...")
    mh_2()

