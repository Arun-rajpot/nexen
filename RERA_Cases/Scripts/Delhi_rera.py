from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
from datetime import datetime
from Scripts.Write_to_txt import write_to_MargeFile


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
    Convert date string from 'dd/mm/yyyy', 'yyyy-mm-dd', 'MMM dd yyyy hh:mmaa', 'MMM dd yyyy', or 'dd MMM yyyy' to 'yyyy-mm-dd' format.
    If the date format is unrecognized, return None.
    """
    try:
        # Check if the date is in 'dd/mm/yyyy' format
        if re.match(r'\d{2}/\d{2}/\d{4}', date_str):
            date_obj = pd.to_datetime(date_str, errors='coerce', format='%d/%m/%Y')
            if not pd.isna(date_obj):
                return date_obj.strftime('%Y-%m-%d')
        
        # Check if the date is in 'yyyy-mm-dd' format
        elif re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            return date_str
        
        # Check if the date is in 'MMM dd yyyy hh:mmaa' format (e.g., 'Aug 29 2023 12:00AM')
        elif re.match(r'\w{3} \d{2} \d{4} \d{2}:\d{2}[APMapm]{2}', date_str):
            date_obj = datetime.strptime(date_str, '%b %d %Y %I:%M%p')
            return date_obj.strftime('%Y-%m-%d')
        
        # Check if the date is in 'MMM dd yyyy' format (e.g., 'Aug 29 2023')
        elif re.match(r'\w{3} \d{2} \d{4}', date_str):
            date_obj = datetime.strptime(date_str, '%b %d %Y')
            return date_obj.strftime('%Y-%m-%d')

        # Check if the date is in 'dd MMM yyyy' format (e.g., '24 Mar 2023')
        elif re.match(r'\d{2} \w{3} \d{4}', date_str):
            date_obj = datetime.strptime(date_str, '%d %b %Y')
            return date_obj.strftime('%Y-%m-%d')
        
        else:
            # If the date format is not recognized, return None
            return None
    except Exception as e:
        # Handle any unexpected errors
        print(f"Error processing date: {date_str}, Error: {e}")
        return None

def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string in value.title():
                order_date = dictionary.get("Next Date of Hearing") or dictionary.get("Date of Disposal")
                order_date = order_date.split(" ")[0] if order_date else None
                order_date = convert_date(order_date)

                Application_date = dictionary.get("Complaint Filed on (Date)")
                converted_date = convert_date(Application_date)
                final_payload = {
                    'Estate': "Delhi Real Estate Regulatory Authority",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get("Complainant(s)"),
                    'Respondent': dictionary.get("Respondent(s)"),
                    'Complaint_Number': dictionary.get("Case No.") or dictionary.get("Case Number"),
                    'Project_Registration_Number': None,
                    'Application_date': converted_date,
                    'order_date': order_date,
                    'project_name': None,
                    'Order_Under_Section': None,
                    'district':None,
                    'status':None,
                    'Remarks': None,
                    'other_detail':None,
                    'pdf_link': dictionary.get('Judgement(s) / Order(s)')
                }
                
                return final_payload
    return None

def rera_delhi():
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }
    
    urls = [
        "https://rera.delhi.gov.in/all-ongoing-complaints-stats?page=",
        "https://rera.delhi.gov.in/all-disposed-off-complaints-stats?page="
    ]
    
    try:
        
        for base_url in urls:
            page = 0
            while True:
                url = f"{base_url}{page}"
                print(url)
                response = requests.get(url, headers=headers,verify=False)
                html_data = response.text
                soup = BeautifulSoup(html_data, 'html.parser')
                table = soup.find('table', {'class': "views-table cols-9"}) or soup.find('table', {'class': "views-table cols-7"})
                if table:
                    page += 1
                    thead = table.find('tr')
                    table_headers = [header.text.strip() for header in thead.find_all('th')]
                    datas = []
                    
                    for row in table.find_all('tr'):
                        row_data = {}
                        cells = row.find_all('td')
                        if len(cells) == len(table_headers):
                            for i in range(len(cells)):
                                cell_data = cells[i].text.strip()
                                if cell_data in ["---", "--", ""]:
                                    cell_data = None
                                elif cells[i].find('a'):
                                    link = cells[i].find('a')
                                    if link:
                                        cell_data = link['href']
                                row_data[table_headers[i]] = cell_data
                            datas.append(row_data)
                    targets = ["Ltd", "Llp", "Limited", "Bank"]
                    for item in datas:
                        result = find_strings_in_dict(item, targets)
                        if result is not None:
                            split_data = []
                            split_data.extend(split_payload(result))
                            for sdata in split_data:
                                print("At least one target string found in the dictionary.")
                                print("Resulting dictionary:", sdata)
                                write_to_MargeFile(sdata,"Delhi")
                else:
                    page = 0
                    break
    except requests.RequestException as e:
        print(f"An error occurred: {e}")

# def delhi_main():
#     delhi_rera()
#
#     state_name = "delhi"  # Example, change as needed
#     base_path = r"D:\RERA"  # Base directory
#     unique_data = r"D:\RERA\unique_file"
#     current_file = f"{base_path}\\{state_name}_data_{get_first_day_current_month()}.txt"
#     previous_file = f"{base_path}\\{state_name}_data_{get_first_day_previous_month()}.txt"
#     output_file = f"{unique_data}\\{state_name}_unique_data_{get_first_day_current_month()}.txt"
#
#     # Call the comparison function
#     compare_files(current_file, previous_file, output_file)