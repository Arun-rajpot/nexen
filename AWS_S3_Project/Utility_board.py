
import os
import time
import requests
import csv
from datetime import datetime, timedelta
from urllib3.exceptions import InsecureRequestWarning
from utils import (
    get_database_connection,
    log_console_and_file,
    save_to_local_if_not_exists,
    upload_to_s3_if_not_exists,
    generate_safe_filename_from_url,
    is_file_exists_locally
)

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

error_url_UB = r'E:\\AWS_S3\\Daily_Pdf_download_S3\\Error_urls\\utility_board_error_urls.csv'


def process_recent_utility_board(Local_Base_Directory,S3_BASE_FOLDER):
    conn = get_database_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        two_days_ago = datetime.now() - timedelta(days=3)

        # ✅ Fetch all Utility Board records created/modified in last 2 days
        cursor.execute("""
            SELECT
                UB.id,
                UB.order_file,
                c1.cin AS appellant_cin,
                c2.cin AS respondent_cin
            FROM
                company_core.t_company_utility_board UB
                LEFT JOIN company_core.t_company_detail c1 ON c1.id = UB.appellant_id
                LEFT JOIN company_core.t_company_detail c2 ON c2.id = UB.respondent_id
            WHERE
                UB.order_file IS NOT NULL
                AND UB.order_file <> ''
                AND (
                    UB.created >= %s OR
                    UB.modified >= %s
                )
            ORDER BY UB.id DESC;
        """, (two_days_ago, two_days_ago))

        results = cursor.fetchall()
        log_console_and_file(f"🧾 Found {len(results)} new/updated Utility Board records in last 2 days.")

        req_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/140.0.0.0 Safari/537.36",
            "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        for ub_id, url, appellant_cin, respondent_cin in results:
            print(appellant_cin, respondent_cin)
            filename = generate_safe_filename_from_url(url)
            download_success = False

            try:
                response = requests.get(url, headers=req_headers, timeout=300, verify=False)
                if response.status_code == 200:
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "pdf" in content_type:
                        pdf_content = response.content
                        download_success = True
                    else:
                        log_console_and_file(f"⚠️ Skipped non-PDF content for: {url}")
                else:
                    log_console_and_file(f"❌ Failed to download: {url} (HTTP {response.status_code})")
                    with open(error_url_UB, mode="a", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(["-", url, f"HTTP {response.status_code}"])

            except Exception as e:
                log_console_and_file(f"⚠️ Error processing {url}: {str(e)}")
                with open(error_url_UB, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["-", url, str(e)])
                continue

            # ✅ Save PDF under both CINs (appellant & respondent)
            if download_success:
                for cin in [appellant_cin, respondent_cin]:
                    if cin:
                        local_path_base = os.path.join(Local_Base_Directory, cin, "utility_board", filename + ".pdf")
                        s3_key_base = f"{S3_BASE_FOLDER}/{cin}/utility_board/{filename}"
                        if is_file_exists_locally(local_path_base):
                            continue

                        save_to_local_if_not_exists(pdf_content, local_path_base)
                        upload_to_s3_if_not_exists(pdf_content, s3_key_base)
                        log_console_and_file(f"✅ Saved Utility Board PDF for CIN: {cin} | ID: {ub_id}")

    finally:
        cursor.close()
        conn.close()

