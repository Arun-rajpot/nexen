from bs4 import BeautifulSoup
import requests
import unidecode
import pandas as pd
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload




def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string in value.title():
                #----------------Application_date----------------------------------
                Application_date = dictionary.get("Application Date")
                Application_date = pd.to_datetime(Application_date, errors='coerce', format='%d-%m-%Y', dayfirst=True)
                if pd.isna(Application_date):
                    Application_date = None
                else:
                    Application_date = Application_date.strftime("%Y-%m-%d")

                #----------------order_date----------------------------------
                order_date_value = dictionary.get("Disposed Date") or dictionary.get("Order Date")
                order_date = pd.to_datetime(order_date_value, errors='coerce', format='%d-%m-%Y', dayfirst=True)
                if pd.isna(order_date):
                    order_date = None
                else:
                    order_date = order_date.strftime("%Y-%m-%d")

                final_payload = {
                    'Estate': "Real Estate Regulatory Authority Madhya Pradesh",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': unidecode.unidecode(dictionary.get("Complainant Name").replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip().title()),
                    'Respondent': unidecode.unidecode(dictionary.get("Non-Applicant Name").replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip().title()),
                    'Complaint_Number':dictionary.get("Registration Number"),
                    'Project_Registration_Number': None,            
                    'Application_date': Application_date,
                    'order_date': order_date,
                    'project_name': None, 
                    'Order_Under_Section': None,
                    'district':None,
                    'status':None,
                    'Remarks': None,
                    'other_detail':None,
                    'pdf_link': dictionary.get("pdf_link")
                }
                return final_payload
    return None

def rera_MP():
    url_list =["https://www.rera.mp.gov.in/complaint-listing-loop.php?show=20&pagenum=1&search_txt=&type=MN&_=1715323726396","https://www.rera.mp.gov.in/complaint-listing-adj-loop.php?show=20&pagenum=1&search_txt=&_=1715323858017","https://www.rera.mp.gov.in/final-disposed-by-ao-loop.php?show=20&pagenum=1&search_txt=&_=1715323949249","https://www.rera.mp.gov.in/complaint-listing-interim-loop.php?show=20&pagenum=1&search_txt=&type=MN&_=1715324030906","https://www.rera.mp.gov.in/complaint-listing-loop.php?show=20&pagenum=1&search_txt=&type=40&_=1715324115096","https://www.rera.mp.gov.in/complaint-listing-loop.php?show=20&pagenum=1&search_txt=&type=MRC&_=1715324182734","https://www.rera.mp.gov.in/complaint-listing-interim-loop.php?show=20&pagenum=1&search_txt=&type=40&_=1715324242180","https://www.rera.mp.gov.in/complaint-listing-interim-loop.php?show=20&pagenum=1&search_txt=&type=MRC&_=1715324299367"]
    for url in url_list:
        headers = {
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate, br, zstd',
            'Accept-Language':'en-US,en;q=0.9',
            'Cookie':'PHPSESSID=hc2r4g8ri8ip8vll5phfsrfn97; laguagecookie=1',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        
        response_post = requests.get(url, headers=headers)
        html_data = response_post.text
        soup = BeautifulSoup(html_data, 'html.parser')
        
        headers = [th.text.strip() for th in soup.find_all('th')[1:-1]]
        headers.append('pdf_link')
        
        # Extracting table rows
        rows = []
        for tr in soup.find_all('tr')[1:]:  # Start from the second row
            row = [td.text.strip() for td in tr.find_all('td')[1:-1]]
            # Extracting PDF link if available
            last_td = tr.find_all('td')[-1]
            pdf_link = last_td.find('a')['href'] if last_td.find('a') else None
            row.append(pdf_link)
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
                    print("Resulting dictionary:", sdata)
                    write_to_MargeFile(sdata,"MP")
                    
                
            else:
                print("None of the target strings found in the dictionary.")
        
