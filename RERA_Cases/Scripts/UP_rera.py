from django.http import HttpResponse
import requests
from bs4 import BeautifulSoup
import json
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload




def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string in value.title():
                final_payload = {
                    'Estate': "Uttar Pradesh Real Estate Regulatory Authority",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get("Promoter Name").replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip() if dictionary.get("Promoter Name") else None,
                    'Respondent': "Uttar Pradesh Real Estate Regulatory Authority",
                    'Complaint_Number': None,
                    'Project_Registration_Number': dictionary.get("Project Registration No"),
                    'Application_date': None,
                    'order_date': None,
                    'project_name': dictionary.get("Project name"),
                    'Order_Under_Section': None,
                    'district':dictionary.get("Project District"),
                    'status':None,
                    'Remarks': None,
                    'other_detail':None,
                    'pdf_link': dictionary.get('Rera Order')
                }
                return final_payload
    return None

def process_data(data):
    for item in data:
        
        targets = ["Ltd", "Llp", "Limited", "Bank"]
        result = find_strings_in_dict(item, targets)
        if result is not None:
            split_data = []
            split_data.extend(split_payload(result))
            for sdata in split_data:
                sdata['Applicant'] = sdata['Applicant'].replace('M/s.', '').replace('M/S', '').replace(', and', '').lstrip('12345)(),./\\').replace('2)', '').replace(', 2)', '').replace('3)', '').replace('4)', '').strip()
                print("At least one target string found in the dictionary.")
                print("Resulting dictionary:", sdata)
                write_to_MargeFile(sdata,"UP")

def rera_up_1():
    url = "https://www.up-rera.in/DefaulterList"
    response = requests.get(url)
    
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', id='ctl00_ContentPlaceHolder1_grd_black')
    
    headers = [th.text.strip() for th in table.find('tr').find_all('th')]
    data = []
    rows = table.find_all('tr')[1:]
    for row in rows:
        row_data = {}
        cells = row.find_all('td')
        for i in range(len(headers)):
            cell = cells[i]
            a_tag = cell.find('a')
            if a_tag and 'href' in a_tag.attrs:
                cell_value = "https://www.up-rera.in/" + a_tag['href']
            else:
                cell_value = cell.text.strip()
            row_data[headers[i]] = cell_value
        data.append(row_data)
    
    process_data(data)

def rera_up_2():
    url = "https://www.up-rera.in/WebService1.asmx/loadwithdrawnproject"
    headers = {
        "Content-Type": "application/json; charset=UTF-8"
    }
    
    data = {}
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        json_data = json.loads(response.text)
        data = json_data["d"]
        soup = BeautifulSoup(data, 'html.parser')
        
        headers = [th.text.strip() for th in soup.find('tr').find_all('th')]
        data = []
        rows = soup.find_all('tr')[1:]
        for row in rows:
            row_data = {}
            cells = row.find_all('td')
            for i in range(len(headers)):
                cell = cells[i]
                a_tag = cell.find('a')
                if a_tag and 'href' in a_tag.attrs:
                    cell_value = "https://www.up-rera.in/" + a_tag['href']
                else:
                    cell_value = cell.text.strip()
                row_data[headers[i]] = cell_value
            data.append(row_data)
        
        process_data(data)
    else:
        print("Failed to retrieve data")

def rera_UP():
    print("Processing Defaulter List...")
    rera_up_1()
    print("Processing Withdrawn Project List...")
    rera_up_2()
    
