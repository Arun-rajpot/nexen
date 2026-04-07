import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import date


today = date.today()




def write_data_to_textfile(payload):
    """Write data to a text file."""
    try:
        post_data = json.dumps(payload)
        print(post_data)
        with open('D:\\SAT_DATA\\SAT_project\\New_Data\\Sat_{}.txt'.format(today), 'a') as f:
            f.write(post_data)
            f.write(',\n')
    except Exception as e:
        print(f"Exception occurred while writing data: {e}")


def final_payload(data_payload):
    """Prepare the final payload."""
    filing_date = data_payload.get("Filing Date")

    if filing_date and filing_date != "NA":
        try:
            # Parse and format the date
            filing_date = pd.to_datetime(filing_date, format='%d %b %Y').strftime("%Y-%m-%d")
        except ValueError:
            filing_date = None
    else:
        filing_date = None

    my_payload = {
        "petitionerCin": None,
        "respondentCin": None,
        "petitionerName": data_payload["petitioner"],
        "respondentName": data_payload["respondent"],
        "petitionerAdv": None,
        "respondentAdv": None,
        "caseDate": filing_date,
        "nextHearing": None,
        "caseDetails": data_payload["Appeal No"],
        "courtName": "SEBI - Mumbai Bench",
        "caseStatus": data_payload["Status"],
        "caseCategory": data_payload['Appeal Type'],
        "caseSubCategory": None,
        "cnrNumber": None,
        'casePaperType': None,
        "courtEstablishment": "Securities Appellate Tribunal",
        "caseLink": "https://satweb.sat.gov.in/case-status"
    }
    return my_payload


def refresh_csrf_token(session, url, headers, retries=3):
    """Refresh the CSRF token."""
    for attempt in range(retries):
        try:
            response = session.get(url, headers=headers, verify=False, timeout=120)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                csrf_token = soup.find('input', {'id': 'security_token'})['value']
                return csrf_token
            print(f"CSRF token refresh failed, status code: {response.status_code}")
        except Exception as e:
            print(f"Error refreshing CSRF token: {e}")
        print(f"Retrying CSRF token refresh ({attempt + 1}/{retries})...")
    return None


def Sat():
    filing_year = str(date.today().year)
    session = requests.Session()
    initial_url = "https://satweb.sat.gov.in/case-status"
    initial_headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9',
        'connection': 'keep-alive',
        'referer': 'https://satweb.sat.gov.in/causelist',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
    }

    csrf_token = refresh_csrf_token(session, initial_url, initial_headers)
    if not csrf_token:
        print("Unable to retrieve initial CSRF token. Exiting.")
        return

    post_headers = {
        **initial_headers,
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-requested-with': 'XMLHttpRequest'
    }

    post_url = "https://satweb.sat.gov.in/get-partywise-status"
    order_url = "https://satweb.sat.gov.in/get-case-history"
    parties = ["Ltd", "Limited", "Llp", "Bank"]

    for party in parties:
        print(f"Processing party: {party}")
        csrf_token = refresh_csrf_token(session, initial_url, initial_headers)
        if not csrf_token:
            print(f"Failed to refresh CSRF token for party {party}. Skipping.")
            continue

        payload = {
            'bench': 1,
            'prty_name': party,
            'filing_year': filing_year,
            'token': csrf_token
        }

        try:
            response = session.post(post_url, headers=post_headers, data=payload, verify=False, timeout=120)
            if response.status_code != 200:
                print(f"Failed to fetch data for party {party}, status code: {response.status_code}")
                continue

            data_dict = json.loads(response.text)
            content = data_dict['content']
            soup = BeautifulSoup(content, 'html.parser')
            table = soup.find('table', {'class': 'table table-bordered'})
            if not table:
                print(f"No data table found for party {party}.")
                continue

            headers = [header.text.strip() for header in table.find_all('th')]
            rows = []
            for row in table.find('tbody').find_all('tr'):
                cells = row.find_all('td')
                row_data = {headers[i]: cell.text.strip() for i, cell in enumerate(cells)}
                row_data['caseLink'] = cells[-1].find('a')['data-id']
                rows.append(row_data)

            for row in rows:
                csrf_token = refresh_csrf_token(session, initial_url, initial_headers)
                order_payload = {
                    'filing_no': row["caseLink"],
                    'token': csrf_token
                }

                try:
                    order_response = session.post(order_url, headers=post_headers, data=order_payload, verify=False, timeout=120)
                    # print(order_response.text)
                    if order_response.status_code != 200:
                        print(f"Failed to fetch case history for case {row['caseLink']}, status code: {order_response.status_code}")
                        continue

                    order_data_dict = json.loads(order_response.text)
                    order_content = order_data_dict['content']
                    order_soup = BeautifulSoup(order_content, 'html.parser')
                    # print(order_soup)
                    # Find the table with counsel details
                    counsel_table = order_soup.find('h3', text='Counsel Details').find_next('table')

                    # Extract the headings
                    headings = counsel_table.find('thead').find_all('th')
                    heading_dict = {heading.text.strip(): None for heading in headings}

                    # Extract the counsel details from tbody
                    counsel_rows = counsel_table.find('tbody').find_all('tr')
                    for co_row in counsel_rows:
                        cols = co_row.find_all('td')
                        if len(cols) >= len(heading_dict):
                            # Assuming the order of <td> matches the headings
                            for i, heading in enumerate(heading_dict.keys()):
                                heading_dict[heading] = cols[i].text.strip()

                    # Print the extracted details
                    applicant_counsel = heading_dict.get('Applicant Counsel', 'Not found')
                    respondent_counsel = heading_dict.get('Respondent Counsel', 'Not found')

                    if 'Petitioner Vs. Respondent' in row:
                        rep_pet = row['Petitioner Vs. Respondent']
                        if rep_pet:
                            rep_pet = rep_pet.split("vs")
                            row["petitioner"] = rep_pet[0].strip()
                            row["respondent"] = rep_pet[1].strip()

                    final_data = final_payload(row)
                    final_data["petitionerAdv"] = applicant_counsel if applicant_counsel else None
                    final_data["respondentAdv"] = respondent_counsel if respondent_counsel else None
                    write_data_to_textfile(final_data)

                except Exception as e:
                    print(f"Error fetching case history for case {row['caseLink']}: {e}")

        except Exception as e:
            print(f"Error processing party {party}: {e}")
        print(f"====================={party}===========================================")

    session.close()



