import json
import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload




def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value and target_string in value.title():
                order_date = dictionary.get("order_date")
                if order_date:
                    order_date = pd.to_datetime(order_date, errors='coerce')
                    if not pd.isna(order_date):
                        order_date = order_date.strftime('%Y-%m-%d')
                    else:
                        order_date = None

                final_payload = {
                    'Estate': "Rajasthan Real Estate Regulatory Authority",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get("app").replace('M/s.', '').replace('M/S', '').strip() if dictionary.get(
                        "app") else None,
                    'Respondent': dictionary.get("res").replace('M/s.', '').replace('M/S',
                                                                                    '').strip() if dictionary.get(
                        "res") else None,
                    'Complaint_Number': dictionary.get("reg_no"),
                    'Project_Registration_Number': None,
                    'Application_date': None,
                    'order_date': order_date,
                    'project_name': None,
                    'Order_Under_Section': None,
                    'district': None,
                    'status': None,
                    'Remarks': None,
                    'other_detail': None,
                    'pdf_link': dictionary.get("pdf_link")
                }

                if final_payload['Applicant'] or final_payload['Respondent']:
                    return final_payload
    return None


def parse_subject_two_vars(subject):
    if not subject or subject.strip() == "":
        return {"reg_no": "", "app": "", "res": ""}

    if "Suo Moto" in subject:
        subject = subject.split("Suo Moto")
        part1 = subject[0].strip()
        app = "Suo Moto"
        res = subject[-1].replace("Vs.", "").replace("Versus", "").replace("Vs", "").replace("VS", "").strip()

        return {
            'reg_no': part1,
            'app': app,
            'res': res
        }

    else:
        # Find reg/complaint numbers
        matches = list(re.finditer(r'(RAJ|RJ|F\.15)?[\-\s()]*\d{4}[\-\s]*\d+', subject, flags=re.IGNORECASE))

        if not matches:
            return {"reg_no": "", "app": "", "res": subject.strip()}

        last_match = matches[-1]
        split_index = last_match.end()

        part1 = subject[:split_index].strip().rstrip(',')  # till reg number
        part2 = subject[split_index:].strip().lstrip(',')  # after reg number

        # Try splitting applicant vs respondent
        app_res = re.split(r'\s+(vs\.?|versus)\s+', part2, flags=re.IGNORECASE)

        return {
            'reg_no': part1,
            'app': app_res[0].strip() if len(app_res) > 0 else None,
            'res': app_res[-1].strip() if len(app_res) > 1 else None
        }


def rera_rajasthan():
    page = 1

    while True:
        url = f"https://rera.rajasthan.gov.in/order-list/?show_records=100&per_page={page}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Referer": "https://rera.rajasthan.gov.in/order-list/?show_records=100",
            "Accept-Language": "en-IN,en;q=0.9",
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            table = soup.find("table", class_="table")

            if table:

                rows = table.find("tbody").find_all("tr")

                if not rows or "No results found." in rows[0].get_text(strip=True):
                    print(rows[0].get_text(strip=True))
                    break  # No more data

                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 4:
                        id_ = cols[0].get_text(strip=True)
                        subject = cols[1].get_text(strip=True)
                        order_date = cols[2].get_text(strip=True)

                        # Get PDF link
                        pdf_link = ""
                        links = cols[3].find_all("a")
                        for link in links:
                            href = link.get("href")
                            if href and href.endswith(".pdf"):
                                pdf_link = href

                        data = {
                            "id": id_,
                            "subject": subject,
                            "order_date": order_date,
                            "pdf_link": pdf_link,
                        }

                        # Parse Applicant/Respondent etc.
                        parsed = parse_subject_two_vars(subject)
                        data.update(parsed)

                        # Filter companies
                        targets = ["Ltd", "Llp", "Limited"]
                        result = find_strings_in_dict(data, targets)
                        if result:
                            split_data = split_payload(result)
                            for item in split_data:
                                print(item)
                                write_to_MargeFile(item,"Rajasthan")
                    else:
                        break
                page += 1
                print(
                    "================================================================================================")
                print(
                    "================================================================================================")
            else:
                break
        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
            break


