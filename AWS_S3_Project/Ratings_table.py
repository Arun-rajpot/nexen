
import os
import time
import requests
from datetime import datetime, timedelta
from utils import (
    get_database_connection,
    log_console_and_file,
    upload_to_s3_if_not_exists,
    save_to_local_if_not_exists,
    generate_safe_filename_from_url,
    is_file_exists_locally
)
from urllib3.exceptions import InsecureRequestWarning
import pdfkit
from playwright.sync_api import sync_playwright
import csv

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

error_url_rating = r'E:\\AWS_S3\\Daily_Pdf_download_S3\\Error_urls\\Rating_error_urls.csv'

def save_webpage_as_pdf_local(url, local_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)
        content = page.pdf(
            format="A4",
            print_background=True,
            margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"}
        )
        browser.close()
    save_to_local_if_not_exists(content, local_path)

def save_webpage_as_pdf_s3(url, s3_key):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)
        content = page.pdf(
            format="A4",
            print_background=True,
            margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"}
        )
        browser.close()

    upload_to_s3_if_not_exists(content, s3_key)


def process_recent_rating_downloads(Local_base_directory,S3_BASE_FOLDER):
    conn = get_database_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        # Calculate last 2 days
        two_days_ago = datetime.now() - timedelta(days=3)

        # Fetch new/modified records in last 2 days
        cursor.execute("""
            SELECT DISTINCT ON (r.link)
                c.id AS company_id,
                c.company_name,
                c.cin,
                r.rating_date,
                m.value AS agency,
                r.link
            FROM company_core.t_company_detail c
            JOIN company_core.t_company_ratings r ON c.id = r.company_id
            JOIN company_core.t_master_data m ON r.agency_id = m.id
            WHERE r.link IS NOT NULL
              AND r.link <> ''
              AND (
                    r.created >= %s OR
                    r.modified >= %s
                  )
            ORDER BY r.link, r.rating_date DESC;
        """, (two_days_ago, two_days_ago))

        results = cursor.fetchall()
        log_console_and_file(f"Found {len(results)} recent records to process.")

        for company_id, company_name, cin, rating_date, agency, link in results:
            try:
                print(link)
                filename = generate_safe_filename_from_url(link) + ".pdf"
                local_path_base = os.path.join(Local_base_directory, cin, "ratings", filename)
                s3_key_base = f"{S3_BASE_FOLDER}/{cin}/ratings/{filename}"
                if is_file_exists_locally(local_path_base):
                    continue

                # Handle different agency links
                if "crisil" in link or "connect.acuite.in" in link or 'bcrisp.in' in link:
                    path_wkhtmltopdf = r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
                    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
                    content = pdfkit.from_url(link, False, configuration=config)
                    save_to_local_if_not_exists(content, local_path_base)
                    upload_to_s3_if_not_exists(content,s3_key_base)
                    
                    
                                              
                elif "indiaratings" in link:
                    save_webpage_as_pdf_local(link, local_path_base)
                    save_webpage_as_pdf_s3(link,s3_key_base)
                elif "www.icra.in" in link:
                    pdf_id = link.split("Id=")[-1].strip()
                    actual_link = "https://www.icra.in/Rating/ShowRationalReportFilePdf/" + pdf_id
                    response = requests.get(actual_link, timeout=60000)
                    if response.status_code == 200:
                        save_to_local_if_not_exists(response.content, local_path_base)
                        upload_to_s3_if_not_exists(response.content, s3_key_base)
                    else:
                        log_console_and_file(f"ICRA download failed: {actual_link}")

                else:
                    if "careratings" in link:
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                            "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "Referer": "https://www.careratings.com/",
                            "Connection": "keep-alive"
                        }
                        response = requests.get(link, headers=headers, timeout=60000, verify=False)
                    else:
                        response = requests.get(link, timeout=60000, verify=False)

                    if response.status_code == 200:
                        content_type = response.headers.get("Content-Type", "").lower()
                        if "pdf" in content_type:

                            save_to_local_if_not_exists(response.content, local_path_base)
                            upload_to_s3_if_not_exists(response.content, s3_key_base)
                        else:

                            save_webpage_as_pdf_local(link, local_path_base)
                            save_webpage_as_pdf_s3(link, s3_key_base)
                    else:
                        log_console_and_file(f"Download failed for {link}")
                        with open(error_url_rating, mode="a", newline="", encoding="utf-8") as f:
                            writer = csv.writer(f)
                            writer.writerow([cin, link, f"HTTP {response.status_code}"])

            except Exception as e:
                log_console_and_file(f"Error processing {link}: {str(e)}")
                with open(error_url_rating, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([cin, link, str(e)])

    finally:
        cursor.close()
        conn.close()
