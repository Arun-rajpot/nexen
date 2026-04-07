import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import ssl
from requests.adapters import HTTPAdapter
from Scripts.Write_to_txt import write_to_MargeFile

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.load_verify_locations(r"D:\Rera_project\Reraproject\rera_scraping_app\security\_.assam.gov.in.crt")  # Load your specific certificate
        context.options |= ssl.OP_LEGACY_SERVER_CONNECT  # Enable legacy renegotiation
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

# def write_to_MargeFile(newline):
#     state_name = "assam"  # Example, change as needed
#     base_path = r"D:\RERA"  # Base directory
#     current_file = f"{base_path}\\{state_name}_data_{get_first_day_current_month()}.txt"
#     with open(current_file, 'a', encoding='utf-8') as text_file:
#         json_line = json.dumps(newline)
#         text_file.write(json_line)
#         text_file.write(",\n")




def split_payload(payload):
    result = []
    keys_to_check = ['Applicant', 'Respondent']
    substrings = ['Ltd', 'Limited', 'Llp', 'LTD', 'LLP', 'LIMITED']
    
    for key in keys_to_check:
        if key in payload and payload[key]:  # Check if the key exists and the value is not None
            for substring in substrings:
                if substring in payload[key]:
                    parts = payload[key].split(substring)
                    for part in parts:
                        part = part.strip('.').replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip()
                        if part.strip():
                            new_payload = payload.copy()
                            if part.strip() + ' ' + substring in payload[key]:
                                new_payload[key] = part.strip() + ' ' + substring
                                result.append(new_payload)
                    break
    if not result:
        result.append(payload)
    
    return result

def convert_date(date_str):
    """
    Convert date from 'dd-mm-yyyy' or '30th May 2024' format to 'yyyy-mm-dd' format.
    
    Parameters:
    date_str (str): Date string in either 'dd-mm-yyyy' or '30th May 2024' format.
    
    Returns:
    str: Date string in 'yyyy-mm-dd' format.
    """
    if date_str:
        try:
            # Try to parse the date in 'dd-mm-yyyy' format
            date_obj = datetime.strptime(date_str, '%d-%m-%Y')
        except ValueError:
            try:
                # If the first format fails, try '30th May 2024' format
                date_obj = datetime.strptime(date_str, '%dth %B %Y')
            except ValueError:
                try:
                    # Try to handle other similar formats like '30th May, 2024'
                    date_obj = datetime.strptime(date_str, '%dth %B, %Y')
                except ValueError as e:
                    return None
        
        # Convert to the new format 'yyyy-mm-dd'
        new_date_str = date_obj.strftime('%Y-%m-%d')
        
        return new_date_str

def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string in value.title():
                Application_date_1 = dictionary.get("Approved Date")
                converted_date_1 = convert_date(Application_date_1)

                Application_date_2 = dictionary.get("Expiry Date") or dictionary.get('Date of Order')
                converted_date_2 = convert_date(Application_date_2)

                final_payload = {
                    'Estate': "Assam Real Estate Regulatory Authority",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get("Promoter") or dictionary.get("Applicant"),
                    'Respondent': dictionary.get('Registered With') or dictionary.get('Respondent'),
                    'Complaint_Number': dictionary.get("Registration Certificate Number") or dictionary.get('Case No'),
                    'Project_Registration_Number': dictionary.get("Project ID").lstrip("-") if dictionary.get("Project ID") else None,            
                    'Application_date': converted_date_1,
                    'order_date': converted_date_2,
                    'project_name': None, 
                    'Order_Under_Section': None,
                    'district':dictionary.get("Project District"),
                    'status':dictionary.get("STATUS"),
                    'Remarks': None,
                    'other_detail':dictionary.get("Project Location"),
                    'pdf_link': dictionary.get('View Certificate') or ("https://reat.assam.gov.in" + dictionary.get("Download") if dictionary.get("Download") else None)
                }
                return final_payload
    return None

def process_datas_1(datas_1):
    targets = ["Ltd", "Llp", "Limited", "Bank"]
    for item in datas_1:
        for key in item:
            if item[key] == '_' or item[key] == '' or item[key] == "Na":
                item[key] = None
        result = find_strings_in_dict(item, targets)
        if result is not None:
            split_data = []
            split_data.extend(split_payload(result))
            for sdata in split_data:
                print("At least one target string found in the dictionary from URL 1.")
                print("Resulting dictionary:", sdata)
                write_to_MargeFile(sdata,"Aasam")

def process_datas_2(datas_2):
    targets = ["Ltd", "Llp", "Limited", "Bank"]
    for item in datas_2:
       
        case_No = item['Case No']
        if "In" in case_No:
            case_No = case_No.split("In")[0].rstrip("[").replace("(Condonation Petn)", "").replace("of", "/").strip()
        elif "IN" in case_No:
            case_No = case_No.split("IN")[0].rstrip("[").replace("(Condonation Petn)", "").replace("of", "/").strip()
        case_No = case_No.replace("of", "/").replace("OF", "/")
        item['Case No'] = case_No
        
        parties = item["Parties"]
        if "-Vs-" in parties:
            parties = parties.split("-Vs-")
            if len(parties) == 2:
                item['Applicant'] = parties[0].strip()
                item['Respondent'] = parties[1].strip()
        elif "-vs-" in parties:
            parties = parties.split("-vs-")
            if len(parties) == 2:
                item['Applicant'] = parties[0].strip()
                item['Respondent'] = parties[1].strip()
                
        for key in item:
            if item[key] == '_' or item[key] == '' or item[key] == "Na":
                item[key] = None
        result = find_strings_in_dict(item, targets)
        if result is not None:
            split_data = []
            split_data.extend(split_payload(result))
            for sdata in split_data:
                print("At least one target string found in the dictionary from URL 2.")
                print("Resulting dictionary:", sdata)
                write_to_MargeFile(sdata,"Assam")

def rera_Aasam():
    
    session = requests.Session()
    session.mount('https://', SSLAdapter())
    
    # url_1 = "https://rera.assam.gov.in/admincontrol/registered_projects/1"
    url_2 = "https://reat.assam.gov.in/judgement-and-order-of-reat-assam/"
    # url_2 = "https://reat.assam.gov.in/judgements-and-orders"

    headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding':'gzip, deflate, br, zstd',
        'Accept-Language':'en-US,en;q=0.9',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }
    
    # response_post_1 = session.get(url_1, headers=headers)
    # html_data_1 = response_post_1.text
    # soup_1 = BeautifulSoup(html_data_1, 'html.parser')
    # table_1 = soup_1.find('table', {'class': "table table-striped table-bordered"})
    # head_1 = table_1.find('thead')
    # headers_1 = [header.text.strip() for header in head_1.find_all('th')]
    # datas_1 = []
    #
    # for row in table_1.find_all('tr'):
    #     row_data = {}
    #     cells = row.find_all('td')
    #     if len(cells) == len(headers_1):
    #         for i in range(len(cells)):
    #             cell_data = cells[i].text.strip()
    #             if cell_data == "---" or cell_data == "--":
    #                 cell_data = None
    #             elif headers_1[i] == 'Project ID':
    #                 cell_data = cells[i].text.strip()
    #             elif cells[i].find('a'):
    #                 link = cells[i].find('a')
    #                 if link:
    #                     cell_data = link['href']
    #             row_data[headers_1[i]] = cell_data
    #         datas_1.append(row_data)
    #
    # process_datas_1(datas_1)


    # requeste for secound url ===========================

    try:
       print("============= assam 2nd Api=================")
       response_post_2 = session.get(url_2, headers=headers)
       print(response_post_2.text)

       html_data_2 = response_post_2.text
       soup_2 = BeautifulSoup(html_data_2, 'html.parser')
       table_2 = soup_2.find('table', {'class': "tablepress tablepress-id-7"})
       if table_2:
           head_2 = table_2.find('thead')
           headers_2 = [header.text.strip() for header in head_2.find_all('th')]
           datas_2 = []

           for row in table_2.find_all('tr'):
               row_data = {}
               cells = row.find_all('td')
               if len(cells) == len(headers_2):
                   for i in range(len(cells)):
                       cell_data = cells[i].text.strip()
                       if cell_data == "---" or cell_data == "--":
                           cell_data = None
                       elif cells[i].find('a'):
                           link = cells[i].find('a')
                           if link:
                               cell_data = link['href']
                       row_data[headers_2[i]] = cell_data
                   datas_2.append(row_data)

           process_datas_2(datas_2)

       # print(response_post_2.text)

    except Exception as e:
        print("request 2nd Api ==",e)



rera_Aasam()

# def assam_main():
#     Rera_assam()
#
#     state_name = "assam"  # Example, change as needed
#     base_path = r"D:\RERA"  # Base directory
#     unique_data = r"D:\RERA\unique_file"
#     current_file = f"{base_path}\\{state_name}_data_{get_first_day_current_month()}.txt"
#     previous_file = f"{base_path}\\{state_name}_data_{get_first_day_previous_month()}.txt"
#     output_file = f"{unique_data}\\{state_name}_unique_data_{get_first_day_current_month()}.txt"
#
#     # Call the comparison function
#     compare_files(current_file, previous_file, output_file)