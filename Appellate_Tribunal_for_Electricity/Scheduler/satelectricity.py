import requests
from bs4 import BeautifulSoup
import json
import html
import calendar
from datetime import datetime, timedelta
from datetime import date
import time

today = date.today()
def write_data_to_textfile(data,year):
    try:
        post_data = json.dumps(data)
        with open("D:\\SATElectricity\\Data\\elctricitydata_" + str(year) + "_{}.txt".format(today), 'a') as f:
            f.writelines(post_data)
            f.writelines(',')
            f.writelines('\n')
    except Exception as e:
        print(f"Exception occurred while writing data: {e}")


def final_data(data):
    print("data====",data)
    
    order_date = data["Date of Order"]
    if order_date:
        formatted_date = datetime.strptime(order_date, '%d/%m/%Y').strftime('%Y-%m-%d')
        # data["Date of Order"] = formatted_date
        
    app_res = data["PARTY DETAIL"].split("Vs")
    if len(app_res) == 2 or any(x in app_res.title() for x in ["Ltd", "Limited", "Llp"]):   
        app = app_res[0].replace("M/s.","").strip()
        res = app_res[1].replace("M/s.","").strip()
        filanl_paylod= {
            "Appellant_cin":None,
            "Respondent_cin":None,
            "Dfr_no":data["DFR No."], 
            "Case_no": data["CASE No."], 
            "Appellant_name": app, 
            "Respondent_name":res, 
            "date_of_order":formatted_date, 
            "Order_file": data["Orders File"]
                        }
        return filanl_paylod
    else:
        return None
def satelectricity():
    
    # url = "https://aptel.gov.in/en/dailyorder/tab3?ajax_form=1&_wrapper_format=drupal_ajax"
    
    reqheaders = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Content-Length': '538',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Host': 'aptel.gov.in',
    'Origin': 'https://aptel.gov.in',
    'Referer': 'https://aptel.gov.in/en/dailyorder/tab3',
    'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
    }
    payload = {
    'form_build_id': 'form-lEK5ISMHrDu53l6kX5VTtH4gGVhqR2naDs_r1XRUBQs',
    'form_id': 'daily_order_date_wise_form',
    'from_date': None,
    'to_date': None,
    '_triggering_element_name': 'op',
    '_triggering_element_value': 'Submit',
    '_drupal_ajax': '1',
    'ajax_page_state[theme]': 'delhi_gov',
    'ajax_page_state[theme_token]': '',
    'ajax_page_state[libraries]': 'eJxdj2EOwjAIhS_UrUdqsMVaw2BCtzlPb101Gv-Q974HBCKB2e5PYOhi1xOaQUZrviBXKwnDClQS1CIcrrcFdfdxHbsa31mbF0WfdJmBRrjCvYPCFZUberefRaeecFNt9oEuIV1KyLL6THICGqzuVDg7As4hqcxJNvYvN3zccCya28mbaArIUfe5-n_gDEHj5ecD38nwJW4tuJk_6jhJWgifRpNuPg'
    }
    query_params = {
    'ajax_form': 1,
    '_wrapper_format': 'drupal_ajax'
   }
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    for year in [current_year]:  # Only the current year
        for month in range(max(1, current_month - 3), current_month + 1):
            
            # Get the first and last day of the month
            _, last_day = calendar.monthrange(year, month)
            start_date = datetime(year, month, 1).strftime('%Y-%m-%d')  # Start date is the 1st
            end_date = datetime(year, month, last_day).strftime('%Y-%m-%d')  # End date is the last day
            
            # Create a new payload with updated dates
            updated_payload = payload.copy()  # Create a copy to avoid mutating the base payload
            updated_payload['from_date'] = start_date
            updated_payload['to_date'] = end_date
            print(updated_payload)
    
            response = requests.post('https://aptel.gov.in/en/dailyorder/tab3', params=query_params, headers=reqheaders, data=updated_payload,timeout=1200)

            # Print response content for debugging
            decoded_content = html.unescape(response.text)
            # print("Full Response:\n", decoded_content)  # Print full decoded response

            try:
                json_data = json.loads(decoded_content)
                # print("Decoded JSON Data:\n", json.dumps(json_data, indent=4))  # Pretty-print JSON

                # Loop through JSON data and look for 'data' in the 'insert' command
                for item in json_data:
                    if item.get('command') == 'insert':
                        print("Found insert command")
                        if 'data' in item:
                            if item['data']:
                                data = item['data']
                                # print(data[0:2000])
                                soup = BeautifulSoup(data, 'html.parser')
                                table = soup.find('table')
                                # Extract the table headers
                                table = soup.find('table')

                                # Extract table headers
                                headers = [th.text.strip() for th in table.find('tr').find_all('th')]

                                # Initialize data list
                                datas = []

                                # Extract rows from the remaining tr tags
                                rows = table.find_all('tr')[1:]  # Skip the header row
                                if rows:
                                    for row in rows:
                                        row_data = {}
                                        cells = row.find_all('td')

                                        # Loop through each header and corresponding cell
                                        for i in range(len(headers)):
                                            cell = cells[i]
                                            # Check if cell contains an 'a' tag
                                            a_tag = cell.find('a')
                                            if a_tag and 'href' in a_tag.attrs:
                                                # Construct the full URL
                                                cell_value =  a_tag['href']  # Adjust base URL as needed
                                                row_data[headers[i]] = cell_value  # Assign URL to the corresponding header
                                            else:
                                                # Extract cell text value if no 'a' tag is present
                                                cell_value = cell.text.strip()
                                                row_data[headers[i]] = cell_value  # Assign text value to the corresponding header
                                        
                                        # Append row data to the list
                                        datas.append(row_data)
                                for d in datas:
                                    final_datas = final_data(d)
                                    if final_datas:
                                         write_data_to_textfile(final_datas,year)                                    
                                    
                            else:
                                print("Data is None")
                        else:
                            print("'data' key not found in 'insert' command")
                    time.sleep(3)
            except json.JSONDecodeError:
                print("Response is not a valid JSON")
            time.sleep(5)

# Call the function
# satelectricity()

