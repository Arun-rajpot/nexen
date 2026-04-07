from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime
import pandas as pd
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload




def convert_date(date_str):
    """
    Convert date string from 'dd/mm/yyyy', 'yyyy-mm-dd', 'MMM dd yyyy hh:mmaa', or 'MMM dd yyyy' to 'yyyy-mm-dd' format.
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
                Application_date = dictionary.get("Date")
                converted_dates = convert_date(Application_date)
                final_payload = {
                    'Estate': "Jharkhand Real Estate Regulatory Authority",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get("Petitioner Name").replace('M/s.','').replace('M/S','').replace('M/s','').strip() if dictionary.get("Petitioner Name") else None,
                    'Respondent': dictionary.get("Respondant Name").replace('M/s.','').replace('M/S','').replace('M/s','').strip()if dictionary.get("Respondant Name") else None,
                    'Complaint_Number':dictionary.get("Case Number"),
                    'Project_Registration_Number':None,            
                    'Application_date': converted_dates,
                    'order_date': None,
                    'project_name': dictionary.get("Case Type") , 
                    'Order_Under_Section': None,
                    'district':None,
                    'status':dictionary.get('Stage'),
                    'Remarks': dictionary.get('Remarks'),
                    'other_detail':None,
                    'pdf_link': None
                }
                return final_payload
    return None




def rera_Jharkhand():
    urls = ["https://jharera.jharkhand.gov.in/Home/causelistB?page=","https://jharera.jharkhand.gov.in/Home/causelistAuthority?page="]
    for base_url in urls:
        page = 1
        while True:
            print("page==", page)
           
            
            # Concatenate base_url and the current page number
            url = base_url + str(page)
            print("url==", url)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
            }
            
            response_post = requests.get(url, headers=headers)
            
            if response_post:
                html_data = response_post.text
                soup = BeautifulSoup(html_data, 'html.parser')
                table = soup.find('table', class_="table table-striped table-bordered table-hover")
                
                if not table:
                    break  # Exit if no table is found
                
                headers = [th.text.strip() for th in table.find('tr').find_all('th')]
                
                # Initialize data list
                data = []
                
                # Extract rows from the remaining tr tags
                rows = table.find_all('tr')[1:]  # Skip the header row
                if rows:
                    page += 1  # Increment page number here after successfully fetching data
                    for row in rows:
                        row_data = {}
                        cells = row.find_all('td')
                        for i in range(len(headers)):
                            cell = cells[i]
                            # Check if cell contains an 'a' tag
                            a_tag = cell.find('a')
                            if a_tag and 'href' in a_tag.attrs:
                                # Extract href attribute
                                cell_value = "http://rera.bihar.gov.in/" + a_tag['href']
                                row_data["URL"] = cell_value
                            else:
                                # Extract cell text value if no 'a' tag is present
                                cell_value = cell.text.strip()
                                row_data[headers[i]] = cell_value
                        # Append row data to the list
                        data.append(row_data)
                    
                    # Print the extracted data
                    targets = ["Ltd", "Llp", "Limited", "Bank"]
                    for item in data:
                        # Clean up the item
                        for key in item:
                            if item[key] == '_' or item[key] == '':
                                item[key] = None
                        # Check for target strings in the dictionary
                        result = find_strings_in_dict(item, targets)
                        
                        if result is not None:
                            split_data = []
                            split_data.extend(split_payload(result))
                            for sdata in split_data:
                                print("At least one target string found in the dictionary.")
                                print("Resulting dictionary:", sdata)
                                write_to_MargeFile(sdata,"Jharkhand")
                else:
                    break  # Exit the loop if there are no rows
            else:
                break  # Exit if the response is not successful
        

# rera_Jharkhand()