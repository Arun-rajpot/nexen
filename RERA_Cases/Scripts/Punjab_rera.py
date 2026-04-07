from django.http import HttpResponse
from bs4 import BeautifulSoup
import requests
import json
import pandas as pd  # type: ignore
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload




def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string in value.title():
                #----------------Application_date----------------------------------
                Order_date = dictionary.get("Date of Decision")
                if Order_date:
                    Order_date = pd.to_datetime(Order_date, errors='coerce', format='%d/%m/%Y')
                    if not pd.isna(Order_date):
                        Order_date = Order_date.strftime('%Y-%m-%d')
                    else:
                        Order_date = None
                rajister_num = dictionary.get("Complaint Number") or dictionary.get("Application Number")
                if rajister_num :
                    rajister_num = rajister_num.replace("of","/").replace(" ","").replace("AppealNo","").strip('.')
                final_payload = {
                    'Estate': "Real Estate Regulatory Authority Punjab",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get("Complainant Name") or dictionary.get("Appellant Name") or dictionary.get("Applicant Name"),
                    'Respondent': dictionary.get("Respondent Name").replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip(),
                    'Complaint_Number':rajister_num,
                    'Project_Registration_Number':None,            
                    'Application_date': None,
                    'order_date': Order_date,
                    'project_name': None, 
                    'Order_Under_Section': None,
                    'district':None,
                    'status':None,
                    'Remarks': None,
                    'other_detail':None,
                    'pdf_link': dictionary.get("pdf_link" )
                }
                return final_payload
    return None

def rera_punjab():
    url_links = ["https://rera.punjab.gov.in/orders-judgements.html","https://rera.punjab.gov.in/orders-judgements-ao.html","https://rera.punjab.gov.in/judgments-appellate-tribunal.html"]

    for url in url_links:
        headers = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding':'gzip, deflate, br, zstd',
            'Accept-Language':'en-US,en;q=0.9',
            'Cookie':'ASP.NET_SessionId=qfscepkybuihx2pd2om2051v; __RequestVerificationToken_L3JlcmFpbmRleA2=TGYS2vJE2_hwrv7jXZycaMW3-84LNZTRsjcUNS0HNkqOh3V4MVL7NUmilAAPxmHTADMQQlpZeZE5Va9wEZm7xzVmm4ckwb1F-icuFKor3lU1',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        
        response_post = requests.get(url, headers=headers)
        html_data = response_post.text
        soup = BeautifulSoup(html_data, 'html.parser')
        # table = soup.find('table', {'id': 'dataTable'})
        headers = [th.text.strip() for th in soup.find_all('th')[1:5]]
        headers.append('pdf_link')
        
        # Extracting table rows
        rows = []
        for tr in soup.find_all('tr')[1:]:  # Start from the second row
            row = [td.text.strip() for td in tr.find_all('td')[:-1]]
            # Extracting PDF link if available
            last_td = tr.find_all('td')[-1]
            pdf_link = last_td.find('a')['href'] if last_td.find('a') else None
            row.append('https://rera.punjab.gov.in/' + pdf_link)
            rows.append(row)
        
        # Building dictionary
        data = []
        for row in rows:
            if row:  # Skip empty rows
                data.append(dict(zip(headers, row)))
        
        targets = ["Ltd", "Llp", "Limited","Bank"]
        for d in data:
            result = find_strings_in_dict(d, targets) 

            if result is not None:
                split_data =[]
                split_data.extend(split_payload(result))
                for sdata in split_data:
                    print("At least one target string found in the dictionary.")
                    if sdata['Applicant']:
                        sdata['Applicant'] = sdata['Applicant'].replace('M/s.', '').replace('M/S', '').replace(', and', '').lstrip('12345)(),./\\').replace('2)', '').replace(', 2)', '').replace('3)', '').replace('4)', '').strip()
                    if sdata['Respondent']:
                        sdata['Respondent'] = sdata['Respondent'].replace('M/s.', '').replace('M/S', '').replace(', and', '').lstrip('12345)(),./\\').replace('1)', '').replace('2)', '').replace(', 2)', '').replace('3)', '').replace('4)', '').strip()
                    print("Resulting dictionary:", sdata)
                    write_to_MargeFile(sdata,"Punjab")
            

