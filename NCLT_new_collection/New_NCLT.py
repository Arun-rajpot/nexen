import requests
import json
import time
import logging
from datetime import datetime,timedelta

# Setup logging
logging.basicConfig(filename="nclt_debug.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Function to write data to a file
def write_to_MargeFile(newline, year):
    file_path = f"D:\\for_test\\New_nclt_Data_21-02-2025_clint_2.txt"

    with open(file_path, 'a', encoding='utf-8') as text_file:
        json_line = json.dumps(newline, ensure_ascii=False)
        text_file.write(json_line)
        text_file.write(",\n")

# Function to process and structure the data into a final payload
def final_payload(data):
    dateOfOrder = data.get("date_of_filing")
    if dateOfOrder:
        date_obj = datetime.strptime(dateOfOrder, "%d-%m-%Y")
        dateOfOrder = date_obj.strftime("%Y-%m-%d")
    nextDate = data.get("next_list_date")
    if nextDate:
        date_obj = datetime.strptime(nextDate, "%d-%m-%Y")
        nextDate = date_obj.strftime("%Y-%m-%d")
    
    final_data = {
        "petitionerCin": None,
        "respondentCin": None,
        "petitioners": data.get("case_title1"),
        "respondent": data.get("case_title2"),
        "type": data.get("case_type"), 
        "orderType": data.get("case_type_desc_cis"), 
        "bench": data.get("bench_location_name"),
        "cpNumber": data.get("case_no"),
        "section": None,
        "dateOfOrder": dateOfOrder, 
        "description": data.get("filing_no"), 
        "orderPassBy": None,
        "orderFileUrl": "https://efiling.nclt.gov.in/casehistorybeforeloginmenutrue.drt",
        "status": data.get("status"),
        "petitionerAdvocate": None, 
        "respondentAdvocate": None, 
        "nextDate": nextDate,
        "orderDescription": "NCLT", 
        "latestOrderFilePath": None, 
        "processingStatus": None
    }
    return final_data

# Function to send requests with retries
def send_request_with_retry(url, headers, payload, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=1200)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)  # Wait before retrying
            else:
                raise


# Main function to scrape NCLT data
def new_nclt():
    url = "https://efiling.nclt.gov.in/caseHistoryoptional.drt"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Host": "efiling.nclt.gov.in",
        "Origin": "https://efiling.nclt.gov.in",
        "Referer": "https://efiling.nclt.gov.in/casehistorybeforeloginmenutrue.drt",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    years = ["2025"]
    bench_id = ["10", "9", "13", "1", "12", "4", "8", "11", "2", "3", "5", "6", "7", "14", "15"]
    party_names = ["Lanco Infratech"]
   

    for year in years:
        for bench in bench_id:
            for party in party_names:
                payload = {
                    "bar_council_advocate": "",
                    "case_no": "",
                    "filing_no": "",
                    "i_adv_search": "E",
                    "i_bench_id": "0",
                    "i_bench_id_case_no": "0",
                    "i_bench_id_lawyer": "0",
                    "i_bench_id_party": bench,
                    "i_case_type_caseno": "0",
                    "i_case_year_caseno": "0",
                    "i_case_year_lawyer": "0",
                    "i_case_year_party": year,
                    "i_party_search": "W",
                    "party_lawer_name": "",
                    "party_name_party": party,
                    "party_type_party": "0",
                    "status_party": "0",
                    "wayofselection": "partyname"
                }

                try:
                    response = send_request_with_retry(url, headers, payload)
                    response_json = response.json()

                    if "mainpanellist" in response_json:
                        main_panel_list = response_json["mainpanellist"]
                        for item in main_panel_list:
                            item = {k: None if v in ("", "NA") else v for k, v in item.items()}
                            data = final_payload(item)
                            print(data)

                            # today = datetime.today()
                            # last_days = today - timedelta(days=18)
                            #
                            # # Convert dateOfOrder to datetime object
                            # order_date = datetime.strptime(data['dateOfOrder'], "%Y-%m-%d")
                            #
                            # # Condition to check if dateOfOrder is within the last 7 days
                            # if last_days <= order_date <= today:
                            write_to_MargeFile(data, year)
                            #     print("The date is within the last days.")
                            # else:
                            #     print("The date is outside the range.")
                            #     break
                    else:
                        print(f"No data found for year: {year}, bench: {bench}, party: {party}")
                except Exception as e:
                    logging.error(f"Failed to process payload for year: {year}, bench: {bench}, party: {party}. Error: {e}")
                finally:
                    time.sleep(1)  # Add delay to prevent server overload

# Run the script

if __name__ == "__main__":
    new_nclt()
