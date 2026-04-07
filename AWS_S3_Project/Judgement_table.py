import os
import time
import requests
from datetime import datetime, timedelta
from utils import (
    get_database_connection,
    log_console_and_file,
    upload_to_s3_if_not_exists,
    generate_safe_filename_from_url,
    is_file_exists_locally,
    save_to_local_if_not_exists
)
from urllib3.exceptions import InsecureRequestWarning
import csv

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

error_url_judgement = r'E:\\AWS_S3\\Daily_Pdf_download_S3\\Error_urls\\Judgement_error_urls.csv'


def process_recent_judgement_documents(Local_base_directory,S3_Base_Directory):
    conn = get_database_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        two_days_ago = datetime.now() - timedelta(days=3)

        # ✅ Fetch all new/updated judgement rows (unique by ID)
        cursor.execute("""
            SELECT
                j.id,
                j.case_link,
                c1.cin AS petitioner_cin,
                c2.cin AS respondent_cin
            FROM
                company_core.t_company_judgement j
                LEFT JOIN company_core.t_company_detail c1 ON c1.id = j.petitioner_id
                LEFT JOIN company_core.t_company_detail c2 ON c2.id = j.respondent_id
            WHERE
                j.case_link IS NOT NULL
                AND j.case_link <> ''
                AND (
                    j.created >= %s OR
                    j.modified >= %s
                )
            ORDER BY j.id DESC;
        """, (two_days_ago, two_days_ago))

        results = cursor.fetchall()
        log_console_and_file(f"🧾 Found {len(results)} judgement records (last 2 days).")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/140.0.0.0 Safari/537.36",
            "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Connection": "keep-alive",
        }

        for judgement_id, url, petitioner_cin, respondent_cin in results:


            print(petitioner_cin,respondent_cin)
            filename = generate_safe_filename_from_url(url)
            download_success = False

            try:
                response = requests.get(url, headers=headers, timeout=90, verify=False)
                if response.status_code == 200:
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "pdf" in content_type:
                        pdf_content = response.content
                        download_success = True
                    else:
                        log_console_and_file(f"⚠️ Skipped non-PDF URL: {url}")
                else:
                    log_console_and_file(f"❌ Failed to download: {url} (HTTP {response.status_code})")
                    with open(error_url_judgement, mode="a", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(["-", url, f"HTTP {response.status_code}"])

            except Exception as e:
                log_console_and_file(f"⚠️ Error processing {url}: {str(e)}")
                with open(error_url_judgement, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["-", url, str(e)])
                continue

            # ✅ Save under both CINs if available
            if download_success:
                for cin in [petitioner_cin, respondent_cin]:
                    if cin:
                        local_path_base = os.path.join(Local_base_directory, cin, "judgements", filename + ".pdf")
                        s3_key = f"{S3_Base_Directory}/{cin}/judgements/{filename}.pdf"

                        if is_file_exists_locally(local_path_base):
                            continue

                        save_to_local_if_not_exists(pdf_content, local_path_base)
                        upload_to_s3_if_not_exists(pdf_content, s3_key)
                        log_console_and_file(f"✅ Saved Judgement PDF for CIN: {cin} | ID: {judgement_id}")

    finally:
        cursor.close()
        conn.close()


