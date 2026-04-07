from django.http import HttpResponse
from bs4 import BeautifulSoup
import requests
import json
import re
from datetime import datetime
import pandas as pd
from Scripts.Write_to_txt import write_to_MargeFile


# def write_to_MargeFile(newline):
#     state_name = "bihar"  # Example, change as needed
#     base_path = r"D:\RERA"  # Base directory
#     current_file = f"{base_path}\\{state_name}_data_{get_first_day_current_month()}.txt"
#     with open(current_file, 'a', encoding='utf-8') as text_file:
#         json_line = json.dumps(newline, ensure_ascii=False)
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
                Application_date = dictionary.get("Date of Notice")
                converted_date = convert_date(Application_date)
                final_payload = {
                    'Estate': "Bihar Real Estate Regulatory Authority",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get("Complainant"),
                    'Respondent': dictionary.get("Respondent"),
                    'Complaint_Number':dictionary.get("order_no"),
                    'Project_Registration_Number':None,            
                    'Application_date': None,
                    'order_date': converted_date,
                    'project_name': None , 
                    'Order_Under_Section':None,
                    'district':None,
                    'status':None,
                    'Remarks': None,
                    'other_detail':None,
                    'pdf_link': dictionary.get('Description')
                }
                return final_payload
    return None

def rera_bihar():
    def order_no_logic_1(subject):
        order_no = subject.split("Complainant")[0] if "Complainant" in subject else None
        if order_no:
            if 'ORDER' in order_no:
                order_no = order_no.split("ORDER")[1].replace(":", '').strip()
                if "Case No" in order_no:
                    order_no = order_no.split("Case No")[1]
            else:
                if 'order' in order_no:
                    order_no = order_no.split("order")[1].replace(":", '').strip()
                    if "Case No" in order_no:
                        order_no = order_no.split("Case No")[1]
        return order_no

    def order_no_logic_2(subject):
        order_no = subject.split("Complainant")[0] if "Complainant" in subject else None
        if order_no:
            if 'PROCEEDING' in order_no:
                order_no = order_no.split("PROCEEDING")[1].replace(":", '').strip()
                if "Case No" in order_no:
                    order_no = order_no.split("Case No")[1]
            else:
                if 'Proceeding' in order_no:
                    order_no = order_no.split("Proceeding")[1].replace(":", '').strip()
                    if "Case No" in order_no:
                        order_no = order_no.split("Case No")[1]
        return order_no

    def Rera_bihar(url, order_no_logic):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        
        response_post = requests.get(url, headers=headers, verify=False)
        if response_post:
            html_data = response_post.text
            soup = BeautifulSoup(html_data, 'html.parser')
            table = soup.find('table', id='ContentPlaceHolder1_GridView1')

            # Extract headers
            headers = [th.text.strip() for th in table.find('tr').find_all('th')]
            # Initialize data list
            data = []
            
            # Extract rows from the remaining tr tags
            rows = table.find_all('tr')[1:]  # Skip the header row
            for row in rows:
                row_data = {}
                cells = row.find_all('td')
                for i in range(len(headers)):
                    cell = cells[i]
                    # Check if cell contains an 'a' tag
                    a_tag = cell.find('a')
                    if a_tag and 'href' in a_tag.attrs:
                        # Extract href attribute
                        row_data["subject"] = a_tag.text.strip()
                        cell_value = "http://rera.bihar.gov.in/" + a_tag['href']
                    else:
                        # Extract cell text value if no 'a' tag is present
                        cell_value = cell.text.strip()
                    row_data[headers[i]] = cell_value
                # Append row data to the list
                data.append(row_data)
            
            # Print the extracted data
            targets = ["Ltd", "Llp", "Limited", "Bank"]
            result_data = []
            for item in data:
                subject = item["subject"]
                # Extract Respondent and Complainant
                Respondent = subject.split("Respondent")[1].replace("M/s", "").replace(":", "").strip() if "Respondent" in subject else None
                Complainant = subject.split("Complainant")[1] if "Complainant" in subject else None
                Complainant = Complainant.split("Respondent")[0].replace("M/s", "").replace(":", "").strip() if "Complainant" in subject else None

                # Extract order_no based on logic
                order_no = order_no_logic(subject)

                if order_no and "," in order_no:
                    order_no = order_no.lstrip(",.").strip()
                    order_no = order_no.split(",")[0]

                item.pop('subject')
                item["Complainant"] = Complainant.replace('\r', '').replace('\n', '').lstrip("-;)").strip().title() if Complainant else None
                item["Respondent"] = Respondent.replace('\r', '').replace('\n', '').lstrip("-;)").strip().title() if Respondent else None
                item["order_no"] = order_no.replace('\r', '').replace('\n', '').replace('cases Nos-', '').lstrip("'s.'-") if order_no else None
                for key in item:
                    if item[key] == '_' or item[key] == '':
                        item[key] = None
                result = find_strings_in_dict(item, targets)

                if result is not None:
                    split_data = []
                    split_data.extend(split_payload(result))
                    for sdata in split_data:
                        result_data.append(sdata)
                        print("At least one target string found in the dictionary.")
                        print("Resulting dictionary:", sdata)
                        write_to_MargeFile(sdata,"Bihar")
            return result_data
        return []

    # URL list
    urls = [
        ("https://rera.bihar.gov.in/InterimOrd.aspx", order_no_logic_1),
        ("https://rera.bihar.gov.in/ProceedingOrder.aspx", order_no_logic_2),
        ("https://rera.bihar.gov.in/publicorder.aspx", order_no_logic_1)
    ]

    # Extract data for each URL
    all_data = []
    for url, logic in urls:
        all_data.extend(Rera_bihar(url, logic))
    
    # return HttpResponse("Scraped data for bihar has been saved to file.")

# def bihar_main():
#     scrape_bihar()
    # # Define file paths
    # state_name = "bihar"  # Example, change as needed
    # base_path = r"D:\RERA"  # Base directory
    # unique_data = r"D:\RERA\unique_file"
    # current_file = f"{base_path}\\{state_name}_data_{get_first_day_current_month()}.txt"
    # previous_file = f"{base_path}\\{state_name}_data_{get_first_day_previous_month()}.txt"
    # output_file = f"{unique_data}\\{state_name}_unique_data_{get_first_day_current_month()}.txt"
    #
    # # Call the comparison function
    # compare_files(current_file, previous_file, output_file)
    