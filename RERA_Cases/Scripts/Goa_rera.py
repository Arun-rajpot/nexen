import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload



# def write_to_MargeFile(newline):
#     state_name = "goa"  # Example, change as needed
#     base_path = r"D:\RERA"  # Base directory
#     current_file = f"{base_path}\\{state_name}_data_{get_first_day_current_month()}.txt"
#     file_path = current_file
#     text_file = open(file_path, 'a')
#     text_file.write((json.dumps(newline)))
#     text_file.write(",")
#     text_file.write("\n")
#     text_file.close()

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
    # Remove ordinal suffixes like 'th', 'st', 'nd', 'rd'
    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

    # Define possible formats to try
    formats = [
        '%d-%m-%Y',  # Format: 'dd-mm-yyyy'
        '%d %B %Y',  # Format: '30 May 2024'
        '%d %B, %Y',  # Format: '30 May, 2024'
    ]

    for fmt in formats:
        try:
            # Try parsing the date with the current format
            date_obj = datetime.strptime(date_str, fmt)
            # Convert to the new format 'yyyy-mm-dd'
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue  # Try the next format if parsing fails

    # If all formats fail, return None
    return None
def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string in value.title():
                Application_date = dictionary.get('DATE OF COMPLAINT') or dictionary.get('DATE OF APPLICATION')
                converted_date = convert_date(Application_date)

                # Handle both sources of data
                applicant = None
                respondent = None

                # Case 1: Old link with 'COMPLAINT NAME' and 'RESPONDENT NAME'
                if dictionary.get("COMPLAINT NAME") and dictionary.get("RESPONDENT NAME"):
                    applicant = dictionary.get("COMPLAINT NAME").replace('M/s.', '').replace('\n', '').replace('M/S', '').replace('M/s', '').strip()
                    respondent = dictionary.get("RESPONDENT NAME").replace('M/s.', '').replace('\n', '').replace('M/S', '').replace('M/s', '').strip()

                # Case 2: New link with 'DETAILS' (format: "Applicant v/s Respondent")
                elif dictionary.get("DETAILS"):
                    details = dictionary.get("DETAILS")
                    if 'v/s' in details:
                        parts = details.split('v/s')
                        applicant = parts[0].strip()
                        respondent = parts[1].strip() if len(parts) > 1 else None
                        
                    elif ' by ' in details:
                        parts = details.split(' by ')
                        applicant = parts[0].strip()
                        respondent = parts[1].strip() if len(parts) > 1 else None
                        
                    elif 'V/s' in details:
                        parts = details.split('V/s')
                        applicant = parts[0].strip()
                        respondent = parts[1].strip() if len(parts) > 1 else None
                    elif ' Vs ' in details:
                        parts = details.split(' Vs ')
                        applicant = parts[0].strip()
                        respondent = parts[1].strip() if len(parts) > 1 else None
                        
                    elif ' By ' in details:
                        parts = details.split(' By ')
                        applicant = parts[0].strip()
                        respondent = parts[1].strip() if len(parts) > 1 else None

                # Handle Complaint Number from both fields
                complaint_number = dictionary.get("ORDER NO_content") or dictionary.get("FINAL ORDER DOCUMENT_content") or None

                final_payload = {
                    'Estate': "Goa Real Estate Regulatory Authority",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': applicant,
                    'Respondent': respondent,
                    'Complaint_Number': complaint_number,
                    'Project_Registration_Number': None,            
                    'Application_date': converted_date,
                    'order_date': None,
                    'project_name': None,
                    'Order_Under_Section': None,
                    'district':None,
                    'status':None,
                    'Remarks': None,
                    'other_detail':None,
                    'pdf_link': dictionary.get("FINAL ORDER DOCUMENT_link") or dictionary.get("ORDER NO_link")
                }
                
                return final_payload
    return None

def scrape_table(url, order_column, file_key):
    print("url===",url)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': "table table-bordered Approval"})
    thead = table.find('tr')
    headers = [header.text.strip() for header in thead.find_all('th')]
    datas = []
    
    for row in table.find_all('tr'):
        row_data = {}
        cells = row.find_all('td')
        if len(cells) == len(headers):
            for i in range(len(cells)):
                cell_data = cells[i].text.strip()
                if cell_data == "---" or cell_data == "--":
                    cell_data = None
                elif cells[i].find('a'):
                    link = cells[i].find('a')
                    if link:
                        text_content = link.text.strip()  # Text (e.g., order number)
                        link_url = "https://rera.goa.gov.in/" + link['href']  # Link
                        row_data[headers[i] + '_content'] = text_content
                        row_data[headers[i] + '_link'] = link_url
                    else:
                        row_data[headers[i]] = cell_data
                else:
                    row_data[headers[i]] = cell_data
            datas.append(row_data)

    targets = ["Ltd", "Llp", "Limited", "Bank"]
    for item in datas:
        for key in item:
            if item[key] == '_' or item[key] == '' or item[key] == "Na":
                item[key] = None
        result = find_strings_in_dict(item, targets)

        if result is not None:
            split_data = []
            split_data.extend(split_payload(result))
            for sdata in split_data:
                write_to_MargeFile(sdata,"Goa")
                print(f"Data saved for {file_key}: ", sdata)

def rera_Goa():
    # Scrape rulings data
    rulings_url = "https://rera.goa.gov.in/reraApp/rulings"
    scrape_table(rulings_url, "ORDER NO", "Rulings")
    
    # Scrape complaint order data
    complaint_url = "https://rera.goa.gov.in/reraApp/ComplaintOrderDetails"
    scrape_table(complaint_url, "FINAL ORDER DOCUMENT", "Complaint Orders")
    


# def goa_main():
#     Rera_goa()
#     # Define file paths
#     state_name = "goa"  # Example, change as needed
#     base_path = r"D:\RERA"  # Base directory
#     unique_data = r"D:\RERA\unique_file"
#     current_file = f"{base_path}\\{state_name}_data_{get_first_day_current_month()}.txt"
#     previous_file = f"{base_path}\\{state_name}_data_{get_first_day_previous_month()}.txt"
#     output_file = f"{unique_data}\\{state_name}_unique_data_{get_first_day_current_month()}.txt"
#
#     # Call the comparison function
#     compare_files(current_file, previous_file, output_file)