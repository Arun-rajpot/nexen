import json
import requests
from bs4 import BeautifulSoup
import pandas as pd # type: ignore
from django.http import HttpResponse
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload
from datetime import datetime


def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string in value.title():
                Application_date = dictionary.get("Date of Final Order")
                if Application_date:
                    # Convert the date format from 'dd.mm.yyyy' to 'yyyy-mm-dd'
                    Application_date = pd.to_datetime(Application_date, errors='coerce', format='%d.%m.%Y')
                    if not pd.isna(Application_date):
                        Application_date = Application_date.strftime('%Y-%m-%d')
                    else:
                        Application_date = None
                        
                CNo = "C.No."
                CCPNo = "CCP No."
                Complaint_Number = dictionary.get("Compensation Claim Petition No.") or dictionary.get("Complaint No.")
                if CNo in Complaint_Number:
                    Complaint_Number =  Complaint_Number.split(CNo)[-1]
                elif CCPNo in Complaint_Number:
                    Complaint_Number =  Complaint_Number.split(CCPNo)[-1] 
                final_payload = {
                    'Estate': "TAMIL NADU REAL ESTATE REGULATORY AUTHORITY",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get("Complainant") or dictionary.get("Complainant/Petitioner"),
                    'Respondent': dictionary.get("Respondent") or dictionary.get("Respondent/Complainant"),
                    'Complaint_Number': Complaint_Number ,
                    'Project_Registration_Number':None,
                    'Application_date': Application_date,
                    'order_date': None,
                    'project_name': dictionary.get("Project"),
                    'Order_Under_Section': None,
                    'district':None,
                    'status':None,
                    'Remarks': None,
                    'other_detail':None,
                    'pdf_link': dictionary.get('Order')
                }
               
                return final_payload
    return None

def Rera_Tamilnadu():
    # Define the headers dictionary for the HTTP request
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }
    
    # Base URLs
    urls = [
        "https://rera.tn.gov.in/cms/tnrera_judgements/",        
        "https://rera.tn.gov.in/cms/smb_judgements/",
        "https://rera.tn.gov.in/cms/adjudicating_judgements/"    
    ]
    
    # List of years

    years = [str(datetime.now().year)]
    
    # Iterate through each base URL
    for base_url in urls:
        # Iterate through each year
        for year in years:
            # Construct the full URL by appending the year
            url = f"{base_url}{year}.php"
            print("url====", url)
            response_post = requests.get(url, headers=headers, verify=False)
            if response_post:
                html_data = response_post.text
                soup = BeautifulSoup(html_data, 'html.parser')
                table = soup.find('table', id='example') 
                if table:
                    # Extract headers from the table
                    thead = table.find('thead')
                    table_headers = [th.text.strip() for th in thead.find_all('td')]
                    print(table_headers)
                    # Initialize data dictionary
                    data = []        
                    # Extract rows from tbody
                    rows = table.find('tbody').find_all('tr')
                    for row in rows:
                        row_data = {}
                        cells = row.find_all(['td', 'tr'])
                        for i in range(len(table_headers)):
                            cell = cells[i]
                            # Check if cell contains an 'a' tag
                            a_tag = cell.find('a')
                            if a_tag and 'href' in a_tag.attrs:
                                # Extract href attribute
                                cell_value = a_tag['href']
                            else:
                                # Extract cell text value if no 'a' tag is present
                                cell_value = cell.text.strip()
                            row_data[table_headers[i]] = cell_value
                        # Append row data to the list
                        data.append(row_data)
                    
                    # Print the data
                    for item in data:
                        targets = ["Ltd", "Llp", "Limited", "Bank"]
                        result = find_strings_in_dict(item, targets)
                        if result is not None:
                            split_data = []
                            split_data.extend(split_payload(result))
                            for sdata in split_data:
                                sdata['Applicant'] = sdata['Applicant'].replace('M/s.', '').replace('M/S', '').replace(', and', '').lstrip('12345)(),./\\').replace('2)', '').replace(', 2)', '').replace('3)', '').replace('4)', '').strip()
                                sdata['Respondent'] = sdata['Respondent'].replace('M/s.', '').replace('M/S', '').replace(', and', '').lstrip('12345)(),./\\').replace('1)', '').replace('2)', '').replace(', 2)', '').replace('3)', '').replace('4)', '').strip()
                                print("At least one target string found in the dictionary.")
                                print("Resulting dictionary:", sdata)
                                write_to_MargeFile(sdata,"Tamilnadu")
                                
