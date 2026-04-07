import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime
from Scripts.Write_to_txt import write_to_MargeFile
from Scripts.Split_payload import split_payload

current_date = datetime.now().strftime('%d/%m/%Y')

# Function to find specific strings in a dictionary and construct a final payload
def find_strings_in_dict(dictionary, target_strings):
    for target_string in target_strings:
        for value in dictionary.values():
            if isinstance(value, str) and value is not None and target_string in value.title():

                Application_date = dictionary.get("complaint_date")  if dictionary.get("complaint_date") else None
                if Application_date:
                    Application_date = pd.to_datetime(Application_date, errors='coerce', format='%d/%m/%Y')
                    Application_date = Application_date.strftime('%Y-%m-%d') if not pd.isna(Application_date) else None
                    
                order_date = dictionary.get("Hearing_Date") or dictionary.get("Fixed for the Date") or dictionary.get("Judgement Date")
                if order_date:
                    order_date = pd.to_datetime(order_date, errors='coerce', format='%d/%m/%Y')
                    order_date = order_date.strftime('%Y-%m-%d') if not pd.isna(order_date) else None


                final_payload = {
                    'Estate': "Himachal Pradesh Real Estate Regulatory Authority",
                    'Applicant_Cin': None,
                    'Respondent_Cin': None,
                    'Applicant': dictionary.get("Applicant") or dictionary.get("Complainant_Name"),
                    'Respondent': dictionary.get("Respondent") or dictionary.get("Respondent_Name"),
                    'Complaint_Number': dictionary.get("Appeal No") or dictionary.get("complaint_no"),
                    'Project_Registration_Number': dictionary.get("project_no"),
                    'Application_date': Application_date,
                    'order_date': order_date,
                    'project_name': None, 
                    'Order_Under_Section': None,
                    'district':None,
                    'status':None,
                    'Remarks': dictionary.get('Advocate/Authorized person') or dictionary.get('Complaint_Subject'),
                    'other_detail':dictionary.get('Appeal Subject'),
                    'pdf_link': dictionary.get("pdf_link")
                }
                return final_payload
    return None

def process_and_save_data(item):
        check_cname = ["Ltd", "Llp", "Limited", "Bank"]

        # for item in data:
        for key in item:
            if item[key] == '_' or item[key] == '':
                item[key] = None

        result = find_strings_in_dict(item, check_cname)
        if result is not None:
            split_data = split_payload(result)
            for sdata in split_data:
                print("At least one target string found in the dictionary.")
                print("Resulting dictionary:", sdata)
                write_to_MargeFile(sdata,"Himachal")

# Function to scrape the complaints table from the first URL
def scrape_complaints_table():
    url = "https://hprera.nic.in/Home/GetComplaintCauseListsPV"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }
    
    payload = {
        'SDate': '01/01/2020',
        'Tdate': current_date,
        '_': '1729597885684'
    }
    response = requests.get(url, headers=headers, params=payload, timeout=30)
    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table', {'class': 'table table-bordered table-responsive-lg table-md font-sm datatables'})
    
    data = []
    for table in tables:
        for row in table.find('tbody').find_all('tr', class_='lh-2'):
            complaint_data = {}
            ref_no_td = row.find_all('td')[1]
            project_no = ref_no_td.find('span', class_='fw-600').text.strip()
            complaint_no = ref_no_td.find_all('span', 'fw-600')[1].text.strip()
            order_date_text = ref_no_td.find('div', class_='font-xxs text-muted').find('span', 'fw-600').text.strip()
            complaint_subject = row.find_all('td')[2].text.strip()
            complainant_name = row.find_all('td')[3].text.strip()
            respondent_name = row.find_all('td')[4].text.strip()
            status_td = row.find_all('td')[5]
            hearing_date = status_td.find('span', class_='fw-600').text.strip() if status_td.find('span', 'fw-600') else None

            complaint_data['project_no'] = project_no
            complaint_data['complaint_no'] = complaint_no
            complaint_data['complaint_date'] = order_date_text
            complaint_data['Complaint_Subject'] = complaint_subject
            complaint_data['Complainant_Name'] = complainant_name
            complaint_data['Respondent_Name'] = respondent_name
            complaint_data['Hearing_Date'] = hearing_date.split(" ")[0].strip() if hearing_date else None

            data.append(complaint_data)
    for item in data:
        process_and_save_data(item)

# Function to scrape data from the two other URLs
# Function to scrape data from the two other URLs
def scrape_rera_data():
    urls = [
        # 'https://hprera.nic.in/Home/GetJudgementListsPV?SDate=01%2F01%2F2020&Tdate=24%2F10%2F2024&_=1729757692154',
        # 'https://hprera.nic.in/Home/GetCauseListsPV?SDate=01%2F01%2F2020&Tdate=24%2F10%2F2024&_=1729757692154'
        'https://hprera.nic.in/Home/GetJudgementListsPV',
        'https://hprera.nic.in/Home/GetCauseListsPV'
        
    ]
    perams = {
        'SDate': '01/01/2020',
        'Tdate': current_date,
        '_': '1731051667800'
    }

    for url in urls:
        print("url==",url)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, params=perams, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='datatables')

        if table:
            thead = table.find('thead')
            table_headers = [th.text.strip() for th in thead.find_all('th')]
            data = []
            rows = table.find('tbody').find_all('tr')

            for row in rows:
                row_data = {}
                cells = row.find_all('td')
                for i in range(len(table_headers)):
                    cell = cells[i]
                    a_tag = cell.find('a')
                    cell_value = "https://hprera.nic.in" + a_tag['href'] if a_tag and 'href' in a_tag.attrs else cell.text.strip()
                    row_data[table_headers[i]] = cell_value
                data.append(row_data)

            # Process the data for Applicant and Respondent
            check_cname = ["Ltd", "Llp", "Limited", "Bank"]
            # print(data)
            for item in data:
                item['pdf_link'] = item.pop('')  # Handle any specific key you're replacing here
                subject = item['Appeal Subject']
                if any(cname in subject for cname in check_cname):
                    subject = subject.split("Vs") if "Vs" in subject else subject.split("V/s") if "V/s" in subject else subject.split("vs") if "vs" in subject else "continue"
                    Applicant = subject[0].lstrip("'M/s''Ms'").strip()
                    Respondent = subject[1].lstrip("'M/s''Ms'").strip()

                    item['Applicant'] = Applicant
                    item['Respondent'] = Respondent

                    # Clean up the Appeal No
                    AppealNo = item['Appeal No'].replace("of", "/").replace("-", "/")
                    AppealNo = AppealNo.replace("_", '')
                    if "No" in AppealNo:
                        AppealNo = AppealNo.split("No")[1].strip()
                        if "In" in AppealNo:
                            AppealNo = AppealNo.split("In")[0].strip()
                        elif "in" in AppealNo:
                            AppealNo = AppealNo.split("in")[0].strip()
                    if "NO" in AppealNo:
                        AppealNo = AppealNo.split("NO")[1].strip()
                        if "In" in AppealNo:
                            AppealNo = AppealNo.split("In")[0].strip()
                        elif "in" in AppealNo:
                            AppealNo = AppealNo.split("in")[0].strip()
                    if "and" in AppealNo:
                        AppealNo = AppealNo.split("and")[1].strip()

                    item['Appeal No'] = AppealNo.replace(" ", "")
                    item.pop('Appeal Subject', None)  # Remove the Appeal Subject key

            # print("data==", data)
            
                    process_and_save_data(item)




# Main function to scrape all three URLs
def rera_Himachal():
    scrape_complaints_table()
    scrape_rera_data()
    
