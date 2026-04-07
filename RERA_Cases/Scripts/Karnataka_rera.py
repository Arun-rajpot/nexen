import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload


current_date = datetime.now().strftime("%d/%m/%Y")




def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string in value.title():
                # For first structure
                if "APPEAL NO" in dictionary:
                    Application_date = dictionary.get("K-RERA JUDGMENT DATE")
                    if Application_date:
                        Application_date = pd.to_datetime(Application_date, errors='coerce', format='%d-%m-%Y')
                        if not pd.isna(Application_date):
                            Application_date = Application_date.strftime('%Y-%m-%d')
                        else:
                            Application_date = None

                    final_payload = {
                        'Estate': "Karnataka Real Estate Regulatory Authority",
                        'Applicant_Cin': None,
                        'Respondent_Cin': None,
                        'Applicant': dictionary.get("PETITIONER NAME").replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip(),
                        'Respondent': dictionary.get("RESPONDENT NAME").replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip(),
                        'Complaint_Number': dictionary.get("APPEAL NO"),
                        'Project_Registration_Number': dictionary.get("FR NO") if dictionary.get("FR NO") else None,
                        'Application_date': Application_date,
                        'order_date': None,
                        'project_name': dictionary.get("COMPLAINT CATEGORY"),
                        'Order_Under_Section': None,
                        'district':None,
                        'status':None,
                        'Remarks': None,
                        'other_detail':None,
                        'pdf_link': "https://rera.karnataka.gov.in/" + dictionary.get('K-RERA JUDGMENT COPY')
                    }
                    if final_payload['Applicant'] or final_payload['Respondent'] is not None:
                        return final_payload

                # For second structure
                elif "COMPLAINANT NO" in dictionary:
                    Application_date = dictionary.get("COMPLAINT DATE")
                    if Application_date:
                        Application_date = pd.to_datetime(Application_date, errors='coerce', format='%d/%m/%Y')
                        if not pd.isna(Application_date):
                            Application_date = Application_date.strftime('%Y-%m-%d')
                        else:
                            Application_date = None

                    order_date = dictionary.get("HEARING DATE")
                    if order_date:
                        order_date = pd.to_datetime(order_date, errors='coerce', format='%d/%m/%Y')
                        if not pd.isna(order_date):
                            order_date = order_date.strftime('%Y-%m-%d')
                        else:
                            order_date = None

                    final_payload = {
                        'Estate': "Karnataka Real Estate Regulatory Authority",
                        'Applicant_Cin': None,
                        'Respondent_Cin': None,
                        'Applicant': dictionary.get("COMPLAINANT NAME").strip(),
                        'Respondent': dictionary.get("RESPONDENT NAME").strip(),
                        'Complaint_Number': dictionary.get("COMPLAINANT NO"),
                        'Project_Registration_Number': dictionary.get("PROJECT REGISTRATION NUMBER") if dictionary.get("PROJECT REGISTRATION NUMBER") else None,
                        'Application_date': Application_date,
                        'order_date': order_date,
                        'project_name': dictionary.get("PROJECT NAME"),
                        'Order_Under_Section': None,
                        'district':None,
                        'status':None,
                        'Remarks': None,
                        'other_detail':None,
                        'pdf_link': None  # Assuming the second payload has no PDF link
                    }
                    if final_payload['Applicant'] or final_payload['Respondent'] is not None:
                        return final_payload
    return None



def rera_Karnataka():

    urls = [
        {"url": "https://rera.karnataka.gov.in/authorityCauseList", "method": "POST"},
        {"url": "https://rera.karnataka.gov.in/tribunalDisposedList", "method": "GET"}
    ]
    
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cookie': 'JSESSIONID=D69222670C2164B3384EF9ED806A1E67',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }
   
    payload = {
        'fromdate': '01/01/2021',
        'todate': current_date,
        'bench': '0',
        'btn1': 'Filter'
    }
    
    for item in urls:
        url = item["url"]
        method = item["method"]

        if method == "POST":
            # Use POST method for the first URL
            response = requests.post(url, data=payload, headers=headers,verify=False)
        else:
            # Use GET method for the second URL
            response = requests.get(url, headers=headers,verify=False)
    
        html_data = response.text
        soup = BeautifulSoup(html_data, 'html.parser')
        
        # Find the table by id 'kreatList' or 'causeList'
        table = soup.find('table', id='kreatList') or soup.find('table', id='causeList')
    
        if table:
            # Extract headers
            table_headers = [th.text.strip() for th in table.find_all('th')]
            
            # Initialize data list
            data = []
            
            # Check if the table is from 'causeList'
            is_cause_list = table.get('id') == 'causeList'
            
            # Extract rows from tbody
            rows = table.find('tbody').find_all('tr')
            for row in rows:
                row_data = {}
                cells = row.find_all(['td', 'th'])
                for i in range(len(table_headers)):
                    cell = cells[i]
                    # If not from 'causeList', check for 'a' tag
                    if not is_cause_list:
                        a_tag = cell.find('a')
                        if a_tag and 'href' in a_tag.attrs:
                            # Extract href attribute
                            cell_value = a_tag['href']
                        else:
                            # Extract cell text value if no 'a' tag is present
                            cell_value = cell.text.strip()
                    else:
                        # Directly extract the text for 'causeList'
                        cell_value = cell.text.strip()
            
                    row_data[table_headers[i]] = cell_value
                # Append row data to the list
                data.append(row_data)
            
            # Print the data
            for item in data:
                # print(item)
                targets = ["Ltd", "Llp", "Limited", "Bank"]
                result = find_strings_in_dict(item, targets)
                if result is not None:                    
                    split_data = split_payload(result)
                    for sdata in split_data:
                        print("At least one target string found in the dictionary.")
                        print("Resulting dictionary:", sdata)
                        write_to_MargeFile(sdata,"Karnataka")
    


