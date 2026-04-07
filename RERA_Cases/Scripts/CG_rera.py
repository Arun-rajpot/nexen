from django.http import HttpResponse
from bs4 import BeautifulSoup
import requests
import json
import pandas as pd # type:ignore
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload
from ftfy import fix_text

# def write_to_MargeFile(newline):
#     state_name = "cg"  # Example, change as needed
#     base_path = r"D:\RERA"  # Base directory
#     current_file = f"{base_path}\\{state_name}_data_{get_first_day_current_month()}.txt"
#     with open(current_file, 'a', encoding='utf-8') as text_file:
#         json_line = json.dumps(newline, ensure_ascii=False)
#         text_file.write(json_line)
#         text_file.write(",\n")


# def split_payload(payload):
#     result = []
#     keys_to_check = ['Applicant', 'Respondent']
#     substrings = ['Ltd', 'Limited', 'Llp']
#
#     for key in keys_to_check:
#         if key in payload:
#             for substring in substrings:
#                 if substring in payload[key]:
#                     parts = payload[key].split(substring)
#                     for part in parts:
#                         part = part.strip('.')
#                         if part.strip():
#                             new_payload = payload.copy()
#                             if part.strip() + ' ' + substring in payload[key]:
#                                 new_payload[key] = part.strip() + ' ' + substring
#                                 result.append(new_payload)
#                     break
#     if not result:
#         result.append(payload)
#
#     return result

def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string.lower() in value.lower():
                #----------------Application_date----------------------------------
                Application_date = dictionary.get("Order Date")
                if Application_date:
                    # Parse the date from the format '21 Jun 2021' to '2021-06-21'
                    Application_date = pd.to_datetime(Application_date, errors='coerce', format='%d %b %Y')
                    if not pd.isna(Application_date):
                        Application_date = Application_date.strftime('%Y-%m-%d')
                        # Manually remove leading zeros by converting to integer and formatting back
                        Application_date_parts = Application_date.split("-")
                        Application_date = f"{Application_date_parts[0]}-{int(Application_date_parts[1]):02d}-{int(Application_date_parts[2]):02d}"
                    else:
                        Application_date = None

                final_payload = {
                    'Estate': "Real Estate Regulatory Authority Chhattisgarh",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get('Applicant').replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip(),
                    'Respondent': dictionary.get('Respondent').replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip(),
                    'Complaint_Number':dictionary.get('Complaint Number'),
                    'Project_Registration_Number': dictionary.get("Project Registration No"),            
                    'Application_date': None,
                    'order_date': Application_date,
                    'project_name': fix_text(dictionary.get("Project Name")).replace('“', '"').replace('”', '"') if dictionary.get("Project Name") else None,
                    'Order_Under_Section': dictionary.get("Order Under Section"),
                    'district':None,
                    'status':None,
                    'Remarks': dictionary.get('Remark'),
                    'other_detail':None,
                    'pdf_link': dictionary.get("pdf_link")
                }
                return final_payload
    return None


def rera_CG():
    ulr_list = ["https://rera.cgstate.gov.in/ComplaintDocs_final_order_section_all.aspx","https://rera.cgstate.gov.in/ComplaintDocs_interim_order.aspx"]
    for url in ulr_list: # = "https://rera.cgstate.gov.in/ComplaintDocs_final_order_section_all.aspx"        
        headers = {
            'Accept':'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate, br, zstd',
            'Accept-Language':'en-US,en;q=0.9',
            'Cookie':'Color_Change_Status=Color_Change_Status=0; Language_Change_Status=Language_Change_Status=0; ASP.NET_SessionId=jvilctw4g3jjd1olvvvzxiam',
            'Referer':'https://rera.cgstate.gov.in/ComplaintDocs_final_order_section_all.aspx',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        
        response_post = requests.get(url, headers=headers, verify=False)
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
            row.append('https://rera.cgstate.gov.in/' + pdf_link)
            rows.append(row)
        
        # Building dictionary
        data = []
        for row in rows:
            if row:  # Skip empty rows
                data.append(dict(zip(headers, row)))
        
        # Print dictionary
        targets = ["Ltd", "Llp", "Limited", "Bank"]
        for d in data:
            result = find_strings_in_dict(d, targets)        

            if result is not None:
                for key in result:
                    if result[key] == '-':
                        result[key] = None
                print("="*50)
                split_data =[]
                split_data.extend(split_payload(result))
                for sdata in split_data:
                    print("At least one target string found in the dictionary.")
                    print("Resulting dictionary:", sdata)
                    write_to_MargeFile(sdata,"CG")
                
            else:
                print("None of the target strings found in the dictionary.")
        
    return HttpResponse("Scraped data for chhattishgrah has been saved to file both links.")

# def rera_CG():
#     scrape_and_save_cg()
#
#     state_name = "cg"  # Example, change as needed
#     base_path = r"D:\RERA"  # Base directory
#     unique_data = r"D:\RERA\unique_file"
#     current_file = f"{base_path}\\{state_name}_data_{get_first_day_current_month()}.txt"
#     previous_file = f"{base_path}\\{state_name}_data_{get_first_day_previous_month()}.txt"
#     output_file = f"{unique_data}\\{state_name}_unique_data_{get_first_day_current_month()}.txt"
#
#     # Call the comparison function
#     compare_files(current_file, previous_file, output_file)
#