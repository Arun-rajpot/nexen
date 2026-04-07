from django.http import HttpResponse
import json
from bs4 import BeautifulSoup
import requests
import datetime
import re
from .create_unique_file import compare_files ,get_first_day_current_month,get_first_day_previous_month



def write_to_MargeFile(newline):
    state_name = "odisha"  # Example, change as needed
    base_path = r"D:\RERA"  # Base directory
    current_file = f"{base_path}\\{state_name}_data_{get_first_day_current_month()}.txt"
    text_file = open(current_file, 'a')
    text_file.write((json.dumps(newline)))
    text_file.write(",")
    text_file.write("\n")
    text_file.close()

def split_payload(payload):
          
    result = []
    keys_to_check = ['Applicant', 'Respondent']
    substrings = ['Ltd', 'Limited', 'Llp','LTD','LLP','LIMITED']
    
    for key in keys_to_check:
        if key in payload:
            for substring in substrings:
                if substring in payload[key]:
                    parts = payload[key].split(substring)
                    for part in parts:
                        part = part.strip('.').replace("M/s.","").replace("M/s","").replace("M/s.","").strip()
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
    Convert date string from 'dd-mm-yyyy hh:mm AM/PM' to 'yyyy-mm-dd' format.
    If the date format is unrecognized, return None.
    """
    try:
        # Check if the date is in 'dd-mm-yyyy hh:mm AM/PM' format
        if re.match(r'\d{2}-\d{2}-\d{4} \d{2}:\d{2} [APM]{2}', date_str):
            date_obj = datetime.datetime.strptime(date_str, '%d-%m-%Y %I:%M %p')
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
                date = dictionary.get('Next Date') if dictionary.get('Next Date') else None
                if date :
                    date =convert_date(date)                

                final_payload = {
                    'Estate': "Real Estate Regulatory Authority Odisha",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get("Complainant").replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip(),
                    'Respondent': dictionary.get("Respondent").replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip(),
                    'Complaint_Number':dictionary.get("Case No."),
                    'Project_Registration_Number': None,            
                    'Application_date': None,
                    'order_date': date,
                    'project_name': None, 
                    'Order_Under_Section': None,
                    'district':None,
                    'status':dictionary.get('Status'),
                    'Remarks': dictionary.get('Complaint Before'),
                    'other_detail':dictionary.get('Property & Address'),
                    'pdf_link': dictionary.get("Remarks") if dictionary.get("Remarks") else None
                }
                return final_payload
    return None

def scrape_and_save_odisha():
    urls = ["https://rera.odisha.gov.in/complaint-status/?complaint_type=&keyword=" ,"https://rera.odisha.gov.in/daily-cause-list/"] 
    
    for url in urls:      
        headers = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding':'gzip, deflate, br, zstd',
            'Accept-Language':'en-US,en;q=0.9',
            'Cookie':'qtrans_front_language=en',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        
        response_post = requests.get(url, headers=headers)
        html_data = response_post.text
        soup = BeautifulSoup(html_data, 'html.parser')
        # print(soup)
        table = soup.find('table', {'class': "table table-bordered rera-table"})
        head = table.find('thead')
        # Extracting table headers
        headers = [header.text.strip() for header in head.find_all('th')]
        # print(headers)
        datas = []
        
        # Extracting table rows
        for row in table.find_all('tr'):
            row_data = {}
            cells = row.find_all('td')
            if len(cells) == len(headers):  # Making sure it's a data row, not header/footer
                for i in range(len(cells)):
                    cell_data = cells[i].text.strip()
                    if cell_data == None:
                        cell_data = None
                    elif i == len(headers) - 1:  # If it's the second last column with a hyperlink
                        link = cells[i].find('a')
                        if link:
                            cell_data = link['href']  # Extracting href attribute
                    row_data[headers[i]] = cell_data
                datas.append(row_data)
        for data in datas:
            print(data)
            targets = ["Ltd", "Llp", "Limited", "Bank"]
            result = find_strings_in_dict(data, targets)
            if result is not None:
                split_data =[]
                split_data.extend(split_payload(result))
                for sdata in split_data:
                    print("At least one target string found in the dictionary.")
                    print("Resulting dictionary:", sdata)
                    write_to_MargeFile(sdata)
            
    return HttpResponse("Scraped data for odisha has been saved to file.")

def odisha_main():
    scrape_and_save_odisha()

    state_name = "odisha"  # Example, change as needed
    base_path = r"D:\RERA"  # Base directory
    unique_data = r"D:\RERA\unique_file"
    current_file = f"{base_path}\\{state_name}_data_{get_first_day_current_month()}.txt"
    previous_file = f"{base_path}\\{state_name}_data_{get_first_day_previous_month()}.txt"
    output_file = f"{unique_data}\\{state_name}_unique_data_{get_first_day_current_month()}.txt"

    # Call the comparison function
    compare_files(current_file, previous_file, output_file)
