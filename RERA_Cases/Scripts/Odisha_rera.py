import os
import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from Scripts.Write_to_txt import write_to_MargeFile




# -------------------- Helper Functions --------------------

def format_date_to_yyyy_mm_dd(date_str):
    """
    Converts date like '04 Jun 2025' to '2025-06-04'.
    Returns None if the date is invalid or '--'.
    """
    if not date_str or date_str.strip() == "--":
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d %b %Y").strftime("%Y-%m-%d")
    except ValueError:
        return date_str


def init_driver(download_dir):
    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(service=Service(), options=options)


def wait_for_download(download_dir, timeout=30):
    for _ in range(timeout):
        for file in os.listdir(download_dir):
            if file.endswith(".csv") and not file.endswith(".crdownload"):
                return os.path.join(download_dir, file)
        time.sleep(1)
    return None


# -------------------- CSV Processors --------------------

def process_complaint_status_csv(csv_file_path):
    df = pd.read_csv(csv_file_path)
    for _, row in df.iterrows():
        final_payload = {
            'Estate': "Real Estate Regulatory Authority Odisha",
            'Applicant_Cin': None,
            'Respondent_Cin': None,
            'Applicant': row.get("Complainant", "").strip() if isinstance(row.get("Complainant"), str) else None,
            'Respondent': row.get("Respondent", "").strip() if isinstance(row.get("Respondent"), str) else None,
            'Complaint_Number': row.get("Case No."),
            'Project_Registration_Number': None,
            'Application_date': None,
            'order_date': None,
            'project_name': None,
            'Order_Under_Section': None,
            'district': None,
            'status': row.get("Status"),
            'Remarks': row.get("Complaint Before"),
            'other_detail': None if pd.isna(row.get('Property & Address')) else row.get('Property & Address'),
            'pdf_link': "https://rera.odisha.gov.in/complaint-status"
        }
        write_to_MargeFile(final_payload,"Odisha")


def process_cause_list_csv(csv_file_path):
    df = pd.read_csv(csv_file_path)
    for _, row in df.iterrows():
        next_date_val = row.get("Next Date")
        order_date_val = None if pd.isna(next_date_val) or next_date_val == "--" else next_date_val
        if order_date_val:
            order_date_val = format_date_to_yyyy_mm_dd(order_date_val)

        final_payload = {
            'Estate': "Real Estate Regulatory Authority Odisha",
            'Applicant_Cin': None,
            'Respondent_Cin': None,
            'Applicant': row.get("Complainant", "").strip() if isinstance(row.get("Complainant"), str) else None,
            'Respondent': row.get("Respondent", "").strip() if isinstance(row.get("Respondent"), str) else None,
            'Complaint_Number': row.get("Case No"),
            'Project_Registration_Number': None,
            'Application_date': None,
            'order_date': order_date_val,
            'project_name': None,
            'Order_Under_Section': row.get("Purpose"),
            'district': None,
            'status': "Ongoing" if order_date_val else "Closed",
            'Remarks': row.get("Nature Of Case"),
            'other_detail': None,
            'pdf_link': "https://rera.odisha.gov.in/cause-list"
        }
        write_to_MargeFile(final_payload,"Odisha")


# -------------------- Download and Process --------------------

def download_and_process(url, download_dir, is_cause_list=False):
    driver = init_driver(download_dir)
    wait = WebDriverWait(driver, 30)
    try:
        print(f"🌐 Opening {url}")
        driver.get(url)

        # Wait for Angular spinner to go (optional)
        try:
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "ngx-overlay")))
        except:
            pass
        time.sleep(1)

        # Wait for Download Button
        download_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-success"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", download_button)

        print("⏳ Waiting for download...")
        file_path = wait_for_download(download_dir)
        if file_path:
            print(f"✅ Downloaded: {file_path}")
            if is_cause_list:
                process_cause_list_csv(file_path)
            else:
                process_complaint_status_csv(file_path)
        else:
            print("❌ File not downloaded.")
    except Exception as e:
        print("❌ Error:", e)
    finally:
        driver.quit()


# -------------------- Main Entry --------------------
def clear_existing_csvs(download_dir):
    for file in os.listdir(download_dir):
        if file.endswith(".csv"):
            os.remove(os.path.join(download_dir, file))

def rera_Odisha():
    download_dir = r"D:\RERA_Scheduler\Download_odisha_csv"
    clear_existing_csvs(download_dir)
    os.makedirs(download_dir, exist_ok=True)

    download_and_process("https://rera.odisha.gov.in/complaint-status", download_dir, is_cause_list=False)
    download_and_process("https://rera.odisha.gov.in/cause-list", download_dir, is_cause_list=True)




