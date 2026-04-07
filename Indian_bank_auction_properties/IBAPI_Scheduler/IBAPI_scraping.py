import requests
import time
import json
from bs4 import BeautifulSoup
import yaml
from datetime import datetime,timedelta
import re
import create_unique

today = datetime.now()
def get_previous_date_file(Bank):

    return f"D:\\IBAPI\\IBAPI_project\\Old_Data\\{Bank}.txt"

def get_current_date_file(Bank):

    return f"D:\\IBAPI\\IBAPI_project\\IBAPI_Data\\{Bank}_{today}.txt"
def write_data_to_textfile(payload,Bank):

    try:
        post_data = payload
        print(post_data)
        with open(f"D:\\IBAPI\\IBAPI_project\\Data\\{Bank}_{today.strftime('%Y-%m-%d')}.txt", 'a') as f:
            f.writelines(str(post_data))
            f.writelines(',')
            f.writelines('\n')
    except Exception as e:
        print("Exception occurred={}".format(e))


def final_payloads(data_payload):
    final_data = {
        "BANK_CIN": None,
        "BORROWER_CIN": None,
        "PROPERTY_ID": data_payload.get("PROPERTY_ID"),
        "BANK_NAME": data_payload.get("BANK_NAME"),
        "IFSC_CODE": data_payload.get("IFSC_CODE"),
        "BRANCH_NAME": data_payload.get("BRANCH_NAME"),
        "BORROWER_NAME": data_payload.get("BORROWER_NAME"),
        "BORROWER_CIF": data_payload.get("BORROWER_CIF"),
        "OWNER_NAME": data_payload.get("OWNER_NAME"),
        "CITY": data_payload.get("CITY"),
        "RESERVE_PRICE": data_payload.get("RESERVE_PRICE"),
        "EMD": data_payload.get("EMD"),
        "STATE_CODE": data_payload.get("STATE_CODE"),
        "STATE_NAME": data_payload.get("STATE_NAME"),
        "DISTRICT_CODE": data_payload.get("DISTRICT_CODE"),
        "DISTRICT_NAME": data_payload.get("DISTRICT_NAME"),
        "PINCODE": data_payload.get("PINCODE"),
        "OWNERSHIP_CODE": data_payload.get("OWNERSHIP_CODE"),
        "OWNERSHIP": data_payload.get("OWNERSHIP"),
        "TYPE_OF_TITLE_DEED": data_payload.get("DEED_NAME"),
        "PROPERTY_CODE": data_payload.get("PROPERTY_CODE"),
        "PROPERTY_NAME": data_payload.get("PROPERTY_NAME"),
        "PROPERTY_CODE1": data_payload.get("PROPERTY_CODE1"),
        "PROPERTY_SUB_TYPE_NAME": data_payload.get("PROPERTY_SUB_TYPE_NAME"),
        "ADDRESS": data_payload.get("ADDRESS"),
        "AUCTION_OPEN_DATE": data_payload.get("AUCTION_OPEN_DATE"),
        "AUCTION_CLOSE_DATE": data_payload.get("AUCTION_CLOSE_DATE"),
        "EMD_LAST_DATE": data_payload.get("EMD_LAST_DATE"),
        "STATUS_OF_POSSESSION": data_payload.get("POSSESSION_NAME"),
        "SEALED_BID_LASTDATE": data_payload.get("SEALED_BID_LASTDATE"),
        "SEALED_BID_EXTENDED_DATE": data_payload.get("SEALED_BID_EXTENDED_DATE"),
        "SUMMARY_DESCRIPTION": data_payload.get("SUMMARY_DESC"),
        "MSTC_STATUS": data_payload.get("MSTC_STATUS"),
        "NEAREST_AIR_RLY_BUS": data_payload.get("NEAREST_AIR_RLY_BUS"),
        "COORDINATE_LONGITUDE": data_payload.get("COORDINATE_LONGITUDE"),
        "COORDINATE_LATITUDE": data_payload.get("COORDINATE_LATITUDE"),
        "AUTHORISED_OFFICER": data_payload.get("AO_DETAIL"),
        "BIDDING_URL": data_payload.get("BIDDING_URL"),
        "PDF_LINK": data_payload.get("pdf_link")
    }
    return final_data


def make_request(url, headers, payload=None, method='POST', retries=3, backoff_factor=1):
    for attempt in range(retries):
        try:
            if method == 'POST':
                response = requests.post(url, headers=headers, json=payload, verify=False, timeout=120)
            else:
                response = requests.get(url, headers=headers, verify=False, timeout=120)
            response.raise_for_status()
            return response
        except (requests.RequestException, ConnectionResetError) as e:
            if attempt < retries - 1:
                time.sleep(backoff_factor * (2 ** attempt))
                continue
            else:
                print(f"Error occurred during request to {url}: {e}")
                return None


def IBAPI_Scraping():

    url = "https://ibapi.in/Sale_Info_Home.aspx/Button_search_Click"
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://ibapi.in',
        'Referer': 'https://ibapi.in/sale_info_home.aspx',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }

    response_post = make_request(url, headers)
    if not response_post:
        return

    html_data = response_post.text
    soup = BeautifulSoup(html_data, 'html.parser')

    # Find all the option tags within the select tag
    option_tags = soup.find('select', {'name': 'DropDownList_Bank'}).find_all('option')

    # Extract and store the text content in a list
    options_list = [f"'{option.text}'" for option in option_tags]
    Banks_list = options_list[1:]
    print("Banks_list",Banks_list)
    for bank in Banks_list:

        post_url = "https://ibapi.in/Sale_Info_Home.aspx/Button_search_Click"
        payload = {
            "key_val": [["Bank", bank]]
        }

        post_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://ibapi.in',
            'Referer': 'https://ibapi.in/sale_info_home.aspx',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }

        response_post = make_request(post_url, post_headers, payload)
        if not response_post:
            continue

        result = response_post.json()
        data = result['d']
        data = yaml.safe_load(data)

        for my_data in data:
            Property = my_data['Property ID']
            soup = BeautifulSoup(Property, 'html.parser')
            extracted_text = soup.a.text
            url = "https://ibapi.in/Sale_Info_Home.aspx/bind_modal_detail"
            payload = {
                'prop_id': extracted_text
            }
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': 'https://ibapi.in',
                'Referer': 'https://ibapi.in/sale_info_home.aspx',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            }

            response_post = make_request(url, headers, payload)
            if not response_post:
                continue

            result = response_post.json()
            data = result['d']
            data = yaml.safe_load(data)
            final_payload = data[0]

            url = "https://ibapi.in/Sale_Info_Home.aspx/getCarouselData"
            payload = {
                'prop_id': extracted_text
            }
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': 'https://ibapi.in',
                'Referer': 'https://ibapi.in/sale_info_home.aspx',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            }

            response_post = make_request(url, headers, payload)
            if response_post:
                result = response_post.json()
                data = result['d']
                data = yaml.safe_load(data)
                pattern = r'D:\\IBAPI(\\upload_saleinfo\\{}\\[^\\]+\.pdf)'.format(extracted_text)

                # Find all matches in the input string
                matches = re.findall(pattern, data)
                if matches:
                    pdf_link = "https:\\ibapi.in" + matches[0]
                else:
                    pdf_link = None
                final_payload["pdf_link"] = pdf_link
            else:
                final_payload["pdf_link"] = None

            AUCTION_OPEN_DATE = final_payload['AUCTION_OPEN_DATE']
            AUCTION_CLOSE_DATE = final_payload['AUCTION_CLOSE_DATE']

            # Convert the string to a datetime object
            if AUCTION_CLOSE_DATE != "NA":
                date_object = datetime.strptime(AUCTION_CLOSE_DATE, "%d/%b/%Y %I:%M:%S %p")
                AUCTION_CLOSE_DATE = date_object.strftime("%Y-%m-%d")
                final_payload['AUCTION_CLOSE_DATE'] = AUCTION_CLOSE_DATE

            if AUCTION_OPEN_DATE != "NA":
                date_object = datetime.strptime(AUCTION_OPEN_DATE, "%d/%b/%Y %I:%M:%S %p")
                AUCTION_OPEN_DATE = date_object.strftime("%Y-%m-%d")
                final_payload['AUCTION_OPEN_DATE'] = AUCTION_OPEN_DATE

                # Replace "NA" or "" with None
            for key, value in final_payload.items():
                if value == "NA" or value == "" or value == " ":
                    final_payload[key] = None

            final_data = final_payloads(final_payload)
            add_keys = json.dumps(final_data)
            write_data_to_textfile(add_keys, bank)
            time.sleep(0.1)
        time.sleep(0.1)


        # create unique file
        # previous_file = get_previous_date_file(bank)
        # current_file = get_current_date_file(bank)
        #
        # output_directory = "D:\\IBAPI\\IBAPI_project\\unique_data"
        # create_unique.compare_datewise_files(previous_file, current_file, output_directory,bank)



