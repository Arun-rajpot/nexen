import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import json
import  re

class DcourtScraper:
    def __init__(self, state):
        self.state = state
        self.session = requests.Session()

    def write_data_to_textfile(self, payload, year, state):
        try:
            post_data = json.dumps(payload)
            print(post_data)
            with open(f'{year}_{state}_data.txt', 'a') as f:
                f.write(post_data)
                f.write(',\n')
        except Exception as e:
            print(f"Exception occurred={e}")

    def process_data_payload(self, data_soup):
        try:
            print("-----------------------------------------------")
            scid_input = data_soup.find('input', {'name': 'scid'})
            scid = scid_input['value'] if scid_input and 'value' in scid_input.attrs else ''

            tok_value_input = data_soup.find('input', {'name': 'tok_6103fda595c61bd35c368044c273d01dece19e6f'})
            tok_value = tok_value_input['value'] if tok_value_input and 'value' in tok_value_input.attrs else ''

            captcha_image = data_soup.find('img', {'id': 'siwp_captcha_image_0'})
            captcha_src = captcha_image.get('src', '')
            print(captcha_src)

            time.sleep(5)
            print("Please enter the captcha manually since automatic conversion may not be accurate with background noise.")
            captcha_value = input("Enter the CAPTCHA value: ")

            return {
                'service_type': 'courtEstablishment',
                'litigant_name': None,
                'est_code': None,
                'reg_year': None,
                'case_status': 'B',
                'scid': scid,
                'tok_6103fda595c61bd35c368044c273d01dece19e6f': tok_value,
                'siwp_captcha_value': captcha_value,
                'es_ajax_request': '1',
                'submit': 'Search',
                'action': 'get_parties',
                "page": None,
                "loadmore_clicked": None
            }
        except Exception as e:
            print(f"Exception occurred={e}")
            return None

    def last_post_payload(self, data_cno):
        return {
            "cino": data_cno,
            "action": "get_cnr_details",
            "es_ajax_request": 1
        }

    def extract_table_data(self, tables):
        table_data = {}
        for table in tables:
            caption = table.find('caption').text.strip()
            headers = [th.text.strip() for th in table.find_all('th')]
            rows = table.find_all('tr')
            data = []
            for row in rows[1:]:
                cells = [td.text.strip() for td in row.find_all('td')]
                if len(cells) == len(headers):
                    data.append(dict(zip(headers, cells)))
            table_data[caption] = data
        return table_data

    def convert_date(self, date_str, date_format):
        try:
            return pd.to_datetime(date_str, format=date_format, errors='coerce').strftime("%Y-%m-%d")
        except Exception as e:
            print(f"Date conversion error: {e}")
            return None

    def return_data_payload(self, content, court_name, est_code_option, district):
        soup = BeautifulSoup(content, 'html.parser')
        tables = soup.find_all('table', {'class': 'data-table-1'})

        table_data = self.extract_table_data(tables)

        case_details = next(iter(table_data.get('Case Details', [])), {})
        case_status = next(iter(table_data.get('Case Status', [])), {})
        acts = next(iter(table_data.get('Acts', [])), {})

        case_link = None
        for table in tables:
            caption = table.find('caption')
            if caption and  any(kw in caption.text.strip() for kw in ['Order', 'Orders', 'Final Order']):
                print("Processing 'Orders' table...")
                hyperlinks = table.find_all('a', href=True)
                for hyperlink in hyperlinks:
                    case_link = hyperlink.get('href')
                    print("Case Link Found:", case_link)
                break

        def get_value(data_dict, key):
            return data_dict.get(key, None)

        case_date_str = get_value(case_details, 'Filing Date')
        next_hearing_date_str = get_value(case_status, 'Next Hearing Date')

        case_date = self.convert_date(case_date_str, '%d-%m-%Y') if case_date_str else None
        next_hearing = self.convert_date(next_hearing_date_str, '%d-%B-%Y') if next_hearing_date_str else None

        return {
            "petitionerCin": None,
            "respondentCin": None,
            "petitionerName": None,
            "respondentName": None,
            "petitionerAdv" : None,
            "respondentAdv" : None,
            "caseDate": case_date,
            "nextHearing": next_hearing,
            "caseDetails": get_value(case_details, 'Case Details'),
            "courtName": court_name.title(),
            "caseStatus": get_value(case_status, 'Case Status'),
            "caseCategory": get_value(acts, 'Under Act(s)'),
            "caseSubCategory": get_value(acts, 'Under Section(s)'),
            "cnrNumber": get_value(case_details, 'CNR Number'),
            'casePaperType': None,
            "courtEstablishment": est_code_option.text.strip(),
            "caseLink": case_link
        }

    def fetch_case_details(self, post_url, payload, page_count, year, district, court_name, est_code_option,state):
        try:
            if page_count > 1:
                print(page_count)
                page_payload = {
                    "page": page_count,
                    "loadmore_clicked": 1
                }
                payload.update(page_payload)
                response_post = self.session.post(post_url, data=payload, verify=False, timeout=60)
                print("Response status code:", response_post.status_code)
                result = response_post.json()
                html_data = result['data']
                soup = BeautifulSoup(html_data, 'html.parser')
                check_tag = soup.find('div', class_='notfound')

                if check_tag and check_tag.get_text(strip=True) == "No records found":
                    return "stop"

                case_rows = soup.find_all('tr')
                for row in case_rows[1:]:
                    self.process_case_row(post_url, row, year, district, court_name, est_code_option,state)
            else:
                print(page_count)
                response_post = self.session.post(post_url, data=payload, verify=False, timeout=60)
                print("Response status code:", response_post.status_code)
                result = response_post.json()
                html_data = result['data']
                message = '{"message":"The captcha code entered was incorrect."}'
                if html_data == message:
                    return "invalid captcha"
                soup = BeautifulSoup(html_data, 'html.parser')
                case_rows = soup.find_all('tr')
                for row in case_rows[1:]:
                    self.process_case_row(post_url, row, year, district, court_name, est_code_option,state)
            return True
        except Exception as e:
            print("========fetch_case_details=============")
            print("Exception occurred:", e)
            return False

    def process_case_row(self, post_url, row, year, district, court_name, est_code_option,state):
        try:
            third_column = row.select_one('td:nth-of-type(3)')
            petitioner_respondent = third_column.get_text(strip=True) if third_column else None
            caseDetails = row.select_one('td:nth-of-type(2)')
            caseDetails_value = caseDetails.get_text(strip=True) if caseDetails else None
            print(caseDetails_value)

            link_tag = row.select_one('td:nth-of-type(4) a')
            data_cno = link_tag['data-cno'] if link_tag else None
            final_payload = self.last_post_payload(data_cno)
            response_post = self.session.post(post_url, data=final_payload, verify=False, timeout=60)
            final_response = response_post.json()
            final_html_data = final_response['data']

            parties = self.extract_names(final_html_data)
            my_data = self.return_data_payload(final_html_data, court_name, est_code_option, district)
            my_data["caseDetails"] = caseDetails_value

            for party in parties:
                my_data['petitionerName'] = party["petitioner"]
                my_data['respondentName'] = party["respondent"]
                my_data['petitionerAdv'] = party["petitionerAdv"]
                my_data['respondentAdv'] = party["respondentAdv"]
                self.write_data_to_textfile(my_data, year, state)
            # petitioner_name, respondent_name = self.extract_names( final_html_data)
            # my_data = self.return_data_payload(final_html_data, court_name, est_code_option, district)
            # my_data['petitionerName'] = petitioner_name
            # my_data['respondentName'] = respondent_name
            # my_data["caseDetails"] = caseDetails_value
            # self.write_data_to_textfile(my_data, year, district)
        except Exception as e:
            print("========process_case_row=============")
            print("Exception occurred:", e)

    def extract_names(self , final_html_data):
        data_list = []

        soup = BeautifulSoup(final_html_data, 'html.parser')
        petitioner_respondent_div = soup.find('div', class_='border box bg-white')

        def clean_name(raw):
            raw = re.sub(r'^\s*\d+\s*[\).]?\s*', '', raw)
            raw = raw.replace("M/S", "").replace("M/s", "").replace("M/S.", "").replace("M/s.", "")
            raw = raw.replace("Ms", "").strip()
            return raw.title()

        def extract_entries(section_div):
            entries = []
            if section_div:
                for li in section_div.find_all('li'):
                    name_tag = li.find('p')
                    name = clean_name(name_tag.text if name_tag else li.text)
                    text = li.get_text(separator="|").replace("\n", "").strip()
                    advocate = None
                    for part in text.split("|"):
                        if "Advocate" in part:
                            advocate = part.replace("Advocate", "").replace("-", "").strip().title()
                    entries.append({"name": name, "advocate": advocate})
            return entries

        petitioner_entries = extract_entries(petitioner_respondent_div.find('div', class_='Petitioner'))
        respondent_entries = extract_entries(petitioner_respondent_div.find('div', class_='respondent'))

        for petitioner in petitioner_entries:
            for respondent in respondent_entries:
                data_list.append({
                    "petitioner": petitioner["name"],
                    "respondent": respondent["name"],
                    "petitionerAdv": petitioner["advocate"],
                    "respondentAdv": respondent["advocate"]
                })

        return data_list
    # def extract_names(self, petitioner_respondent, final_html_data):
    #     petitioner_name, respondent_name = None, None
    #     if "Versus" in petitioner_respondent:
    #         petitioner_respondent = petitioner_respondent.split("Versus")
    #         petitioner_name = petitioner_respondent[0].strip().replace("M/S", "").replace("M/S.", "").replace("M/s.", "").replace("M/s", "").replace("Ms", "").lstrip(".").strip().title()
    #         respondent_name = petitioner_respondent[1].strip().replace("M/S", "").replace("M/S.", "").replace("M/s.", "").replace("M/s", "").replace("Ms", "").lstrip(".").strip().title()
    #     else:
    #         soup = BeautifulSoup(final_html_data, 'html.parser')
    #         petitioner_respondent_div = soup.find('div', class_='border box bg-white')
    #         petitioner_ul = petitioner_respondent_div.find('div', class_='Petitioner').ul
    #         for li in petitioner_ul.find_all('li'):
    #             li_content = li.p.text.strip()
    #             petitioner_name = li_content.replace("M/S", "").replace("M/s", "").replace("M/S.", "").replace("M/s.", "").strip("1234567890)").replace("Ms", "").lstrip(".").strip().title()
    #             break
    #
    #         respondent_ul = petitioner_respondent_div.find('div', class_='respondent').ul
    #         for li in respondent_ul.find_all('li'):
    #             li_content = li.p.text.strip()
    #             respondent_name = li_content.replace("M/S", "").replace("M/s", "").replace("M/S.", "").replace("M/s.", "").strip("1234567890)").replace("Ms", "").lstrip(".").strip().title()
    #             break
    #     return petitioner_name, respondent_name

    def scrape(self):
        try:
            print("-------------------", self.state, "----------------------------")

            district_url = f"https://ecourts.gov.in/ecourts_home/index.php?p=dist_court/{self.state}"
            district_response = self.session.get(district_url, timeout=300, verify=False)

            district_soup = BeautifulSoup(district_response.text, 'html.parser')
            ul_soup = district_soup.find('ul', {'class': 'state-district'})
            links = ul_soup.find_all('a')
            district_list = [link['href'].replace("/", "") for link in links if link.has_attr('href')]
            print(district_list)

            cp_call = 1

            for district in district_list:
                print(f"------------------- {district} ----------------------------")
                district = district.replace("https:", "").strip()
                data_url = f"https://{district}/case-status-search-by-petitioner-respondent/"
                print(data_url)
                try:
                    data_response = self.session.get(data_url, verify=False, timeout=80)
                except Exception as e:
                    print(f"Exeption occurred for {district}",{e})
                    continue
                data_soup = BeautifulSoup(data_response.text, 'html.parser')
                court_name = data_soup.find('span', class_='site_name_english').get_text(strip=True)

                form_soup = data_soup.find('form', {'id': 'ecourt-services-case-status-party-name'})
                pr_names = ["Ltd", "Limited", "Llp", "Bank"]
                years = ["2025"]
                est_code_options = form_soup.find('select', {'id': 'court_establishment'}).find_all('option')[1:]
                if cp_call == 1:
                    payload = self.process_data_payload(data_soup)
                    cp_call += 1

                for est_code_option in est_code_options:
                    for year in years:
                        for pr_name in pr_names:
                            payload["reg_year"] = year
                            payload["litigant_name"] = pr_name
                            payload["est_code"] = est_code_option['value']
                            payload["page"] = 1
                            payload["loadmore_clicked"] = 1
                            print(payload)
                            with ThreadPoolExecutor(max_workers=1) as executor:
                                page_count = 1
                                while True:
                                    post_url = f"https://{district}/wp-admin/admin-ajax.php"
                                    future = executor.submit(self.fetch_case_details, post_url, payload, page_count, year, district, court_name, est_code_option,state)
                                    result = future.result()
                                    if result == "invalid captcha":
                                        print(result)
                                        break
                                    if result == "stop":
                                        print("No more records found, moving to the next court establishment.")
                                        break
                                    page_count += 1
        except Exception as e:
            print(f"Exception occurred: {e}")
        finally:
            self.session.close()

if __name__ == "__main__":
    state = input("Enter state name: ")
    scraper = DcourtScraper(state)
    scraper.scrape()
