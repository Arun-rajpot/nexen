import json
from bs4 import BeautifulSoup
import requests
import pandas as pd
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload



def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string.lower() in value.lower():
                #----------------Application_date----------------------------------
                Application_date = dictionary.get("Date of Decision")
                if Application_date:
                    # Split to get the formatted date part and parse it
                    Application_date = pd.to_datetime(Application_date.split(" ")[1], errors='coerce', format='%d-%b-%Y')
                    if not pd.isna(Application_date):
                        Application_date = Application_date.strftime('%Y-%m-%d')
                        # Manually remove leading zeros by converting to integer
                        Application_date_parts = Application_date.split("-")
                        Application_date = f"{Application_date_parts[0]}-{int(Application_date_parts[1])}-{int(Application_date_parts[2])}"
                    else:
                        Application_date = None

                #----------------Judgement Uploading Date------------------
                judgement_uploading_date_value = dictionary.get("Judgement Uploading Date")
                if judgement_uploading_date_value:
                    # Split to get the formatted date part and parse it
                    judgement_uploading_date = pd.to_datetime(judgement_uploading_date_value.split(" ")[1], errors='coerce', format='%d-%b-%Y')
                    if not pd.isna(judgement_uploading_date):
                        judgement_uploading_date = judgement_uploading_date.strftime('%Y-%m-%d')
                        # Manually remove leading zeros by converting to integer
                        judgement_uploading_date_parts = judgement_uploading_date.split("-")
                        judgement_uploading_date = f"{judgement_uploading_date_parts[0]}-{int(judgement_uploading_date_parts[1])}-{int(judgement_uploading_date_parts[2])}"
                    else:
                        judgement_uploading_date = None
                else:
                    judgement_uploading_date = None

                final_payload = {
                    'Estate': "HARYANA REAL ESTATE REGULATORY AUTHORITY",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': (dictionary.get('Appellant Name') or dictionary.get('Complainant Name') or None).replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip(),
                    'Respondent': dictionary.get('Respondent Name').replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip(),
                    'Complaint_Number':dictionary.get('Appeal No.') or dictionary.get('Complaint No.'),
                    'Project_Registration_Number': None,            
                    'Application_date': Application_date,
                    'order_date': judgement_uploading_date,
                    'project_name': None, 
                    'Order_Under_Section': None,
                    'district':None,
                    'status':None,
                    'Remarks': None,
                    'other_detail':None,
                    'pdf_link': dictionary.get("View Judgement")
                }
                return final_payload
    return None

def rera_Haryana():
    urls = ["https://haryanarera.gov.in/admincontrol/judgements/1","https://haryanarera.gov.in/admincontrol/judgements/2","https://haryanarera.gov.in/admincontrol/judgements/3"]
    for url in urls:    
        headers = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding':'gzip, deflate, br, zstd',
            'Accept-Language':'en-US,en;q=0.9',
            'Cookie':'122.161.69.216=122.161.69.216; ci_session=5Y0YKZ12vs0J0PcYDdMQa5BEoc9TDOK8TeFby2kouw5eXNWCdxuzjPvREW9um7BdjIpab%2B7T1seujxBKd8M%2BIuZnHtdrVQ3E5VzFfEIQje7tFohFGkLTaYYQlYt1ukV%2FFfksmGc3m7sHFNeGPxQWxw9lcKZ4rslyCmSKfaia3HnnOzfiMLs2qspDQhorNL9RIfSGtIxilAlbFAJcOckt6AB85SU55PgGInDM6y6lhE6dA%2BZKsg6IwFRZd9XwfTqCnsqIp0bba%2Bbv2dJDLjNsKwPCtr0knAFvwFqb1q%2F24XhPu%2ByjH4Y7x3kNL7QkKxQxEc2NDt4txdGNzWkVbAfE1GwOvoQDSUdO4nxdj3%2FSKeoadmKGo%2FhXMk6SGZO9G6ZxVMa0g5CRciG%2BgedB%2FPC3gW04X6OEzGdA%2BdltJDiikFMKet2pB%2BsyZgfHb%2FWFk2ggIODTstKK1IdA1tG8WpYJCrxqpjnb%2B8KH5FUwa9AY3EMwzrsCxh6iqwI4VLVOJ3ur; PHPSESSID=ch0kn5a7rajk6tcc351sm1rn3u; qwerty_=3c01da1863fbf891b0b2053151276f0a; digit=sT3T1e',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        
        response_post = requests.get(url, headers=headers)
        html_data = response_post.text
        soup = BeautifulSoup(html_data, 'html.parser')

        table = soup.find('table', {'id': 'compliant_hearing'})
        
        # Extracting table headers
        headers = [header.text.strip() for header in table.find_all('th')]
        
        datas = []
        
        # Extracting table rows
        for row in table.find_all('tr'):
            row_data = {}
            cells = row.find_all('td')
            if len(cells) == len(headers):  # Making sure it's a data row, not header/footer
                for i in range(len(cells)):
                    cell_data = cells[i].text.strip()
                    if cell_data == '---':
                        cell_data = None
                    elif i == len(headers) - 2:  # If it's the second last column with a hyperlink
                        link = cells[i].find('a')
                        if link:
                            cell_data = link['href']  # Extracting href attribute
                    row_data[headers[i]] = cell_data
                datas.append(row_data)
        
        
        for item in datas:
            # print(item)
            targets = ["Ltd", "Llp", "Limited", "Bank"]
            result = find_strings_in_dict(item, targets)
            if result is not None:
                split_data =[]
                split_data.extend(split_payload(result))
                for sdata in split_data:
                    print("At least one target string found in the dictionary.")
                    print("Resulting dictionary:", sdata)
                    write_to_MargeFile(sdata,"Haryana")


    
    

            

