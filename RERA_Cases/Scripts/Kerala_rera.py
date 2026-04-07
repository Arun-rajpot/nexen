from django.http import HttpResponse
from bs4 import BeautifulSoup
import requests
import json
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload




def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string in value.title():
               
                final_payload = {
                    'Estate': "Kerala Real Estate Regulatory Authority",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get("Complainant Name").replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip(),
                    'Respondent': dictionary.get("Respondent Name").replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip(),
                    'Complaint_Number':dictionary.get("Complaint No"),
                    'Project_Registration_Number':None,            
                    'Application_date': None,
                    'order_date': None,
                    'project_name': dictionary.get('Project Name'), 
                    'Order_Under_Section': None,
                    'district':None,
                    'status':None,
                    'Remarks': None,
                    'other_detail':dictionary.get('Order Detail'),
                    'pdf_link': dictionary.get("pdf_link")
                }
                return final_payload
    return None



def rera_kerala():
    payload = {'ruling_by': 'Judgements%20by%20Adjudicating%20Officers',
            'sort': 'newest',
            'page': None
            }
    url = "https://rera.kerala.gov.in/complaint-list"
    # for index, url in enumerate(urls):
    for page in range(1,500):

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        payload["page"] = page

        # if index == 0:
        #     url = url + str(page)
        #     response_post = requests.get(url, headers=headers, verify=False,timeout=1000)
        # else:
        response_post = requests.get(url, headers=headers, params=payload, verify=False,timeout=1000)


        if response_post:
            html_data = response_post.text
            soup = BeautifulSoup(html_data, 'html.parser')

            # Find the table based on the class 'w-full'
            table = soup.find('table', class_='w-full')

            if table:
                # Extract headers from the table
                thead = table.find('thead')
                table_headers = [th.text.strip() for th in thead.find_all('th')]

                # Initialize data list
                data = []

                # Extract rows from tbody
                rows = table.find('tbody').find_all('tr')
                for row in rows:
                    row_data = {}
                    cells = row.find_all('td')
                    for i in range(len(table_headers)):
                        cell = cells[i]
                        # Check if cell contains an 'a' tag
                        a_tag = cell.find('a')
                        if a_tag and 'href' in a_tag.attrs:
                            # Extract href attribute
                            cell_value = "https://rera.kerala.gov.in" + a_tag['href']
                        else:
                            # Extract cell text value if no 'a' tag is present
                            cell_value = cell.text.strip()
                        row_data[table_headers[i]] = cell_value
                    # Append row data to the list
                    data.append(row_data)

                targets = ["Ltd", "Llp", "Limited","Bank"]
                for item in data:
                    # print(item)
                    item['pdf_link'] = item.pop('')
                    for key in item:
                        if item[key] == '_' or item[key] == '':
                            item[key] = None
                    result = find_strings_in_dict(item, targets)

                    if result is not None:
                        split_data =[]
                        split_data.extend(split_payload(result))
                        for sdata in split_data:
                            print("At least one target string found in the dictionary.")
                            print("Resulting dictionary:", sdata)
                            write_to_MargeFile(sdata,"Kerala")


            else:
                print("Table not found")
                break
        else:
            print("Failed to retrieve the webpage")
            break

