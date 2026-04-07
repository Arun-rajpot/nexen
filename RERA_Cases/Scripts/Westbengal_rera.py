from bs4 import BeautifulSoup
import requests
import os
import ssl
from requests.adapters import HTTPAdapter
import tabula
import pandas as pd
import requests
from tempfile import NamedTemporaryFile
from datetime import datetime
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload




class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.load_verify_locations(r"D:\Rera_project\Reraproject\rera_scraping_app\security\_.wb.gov.in.crt")  # Load your specific certificate
        context.options |= ssl.OP_LEGACY_SERVER_CONNECT  # Enable legacy renegotiation
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)



def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string in value.title():

                formatted_date = dictionary.get('Date')
                if formatted_date :
                    formatted_date = datetime.strptime(formatted_date, "%d.%m.%Y")
    
                    # Convert back to desired format
                    formatted_date = formatted_date.strftime("%Y-%m-%d")


                final_payload = {
                    'Estate': "West Bengal Real Estate Regulatory Authority",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get("Applicant /Complainant").replace('M/s.', '').replace('M/S', '').replace('\r', ' ').strip() if dictionary.get("Applicant /Complainant") else None,
                    'Respondent': dictionary.get("Respondent").replace('M/s.', '').replace('M/S', '').replace('\r', ' ').strip() if dictionary.get("Respondent") else None,
                    'Complaint_Number': dictionary.get("Application/ Complaint\rNo.").replace('\r', ' ').strip()  if dictionary.get("Application/ Complaint\rNo.") else None or dictionary.get("Application/\rComplaint No.").replace('\r', ' ').strip() ,
                    'Project_Registration_Number': None,
                    'Application_date': None,
                    'order_date': formatted_date ,
                    'project_name': None,
                    'Order_Under_Section': None,
                    'district':None,
                    'status':None,
                    'Remarks': dictionary.get("Remarks"),
                    'other_detail':None,
                    'pdf_link': dictionary.get("pdf_link")
                }
                if final_payload['Applicant'] or final_payload['Respondent'] is not None:
                    return final_payload
    return None

def Westbengal_rera():
    url = "https://rera.wb.gov.in/cause_list.php"
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Host": "rera.wb.gov.in",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
    
    session = requests.Session()
    session.mount('https://', SSLAdapter())
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    rows = soup.select("#agentDataTable tbody tr")
    data_list = []
    for row in rows:
        columns = row.find_all("td")
        if len(columns) == 4:
            entry = {
                "Download Link": columns[3].find("a")["href"] if columns[3].find("a") else None
            }
            data_list.append(entry)
    
    for pdf_url in data_list:
        pdf_link = pdf_url['Download Link']
        print(f"Processing PDF: {pdf_link}")
        try:
            response = requests.get(pdf_link)
            if response.status_code == 200:
                with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                    temp_file_path = temp_pdf.name
                    temp_pdf.write(response.content)
                    temp_pdf.flush()

                tables = tabula.read_pdf(temp_file_path, pages='all', multiple_tables=True)

                headers = None  # To store headers of the first table
                
                for i, table in enumerate(tables):

                    if i == 0:
                        # Capture headers from the first table
                        headers = table.columns.tolist()
                    else:
                        # Apply headers to subsequent tables if missing
                        if table.columns[0] != headers[0]:  # Check if headers are missing
                            table.columns = headers

                    # print(f"Table {i + 1}:\n")
                    # print(table)

                    dict_list = table.to_dict(orient="records")
                    targets = ['Ltd', 'Limited', 'Llp', 'LTD', 'LLP', 'LIMITED']
                    for data in dict_list:
                        data['pdf_link'] = pdf_link
                        result = find_strings_in_dict(data, targets)
                        if result is not None:
                            split_data = split_payload(result)
                            for sdata in split_data:
                                print("At least one target string found in the dictionary.")
                                print("Resulting dictionary:", sdata)
                                write_to_MargeFile(sdata,"Westbengal")
                os.remove(temp_file_path)
            else:
                print(f"Failed to download PDF. HTTP status code: {response.status_code}")
        except Exception as e:
            print(f"Error reading PDF: {e}")
            
            
            


