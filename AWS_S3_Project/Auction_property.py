
import os
import time
import requests
import csv
from datetime import datetime, timedelta
from urllib3.exceptions import InsecureRequestWarning
from utils import (
    get_database_connection,
    log_console_and_file,
    upload_to_s3_if_not_exists,
    save_to_local_if_not_exists,
    generate_safe_filename_from_url,
    is_file_exists_locally
)

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

error_url_AP = r'E:\\AWS_S3\\Daily_Pdf_download_S3\\Error_urls\\Auction_property_error_urls.csv'


def process_recent_auction_property_cases(Local_Base_Directory,S3_BASE_FOLDER):
    conn = get_database_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        two_days_ago = datetime.now() - timedelta(days=3)

        # ✅ Fetch all Auction Property records created/modified in last 2 days
        cursor.execute("""
            SELECT
                ap.id,
                ap.pdf_link,
                c1.cin AS bank_cin,
                c2.cin AS borrower_cin
            FROM
                company_core.t_company_auction_property ap
                LEFT JOIN company_core.t_company_detail c1 ON c1.id = ap.bank_id
                LEFT JOIN company_core.t_company_detail c2 ON c2.id = ap.borrower_id
            WHERE
                ap.pdf_link IS NOT NULL
                AND ap.pdf_link <> ''
                AND (
                    ap.created >= %s OR
                    ap.modified >= %s
                )
            ORDER BY ap.id DESC;
        """, (two_days_ago, two_days_ago))

        results = cursor.fetchall()
        log_console_and_file(f"🧾 Found {len(results)} Auction Property records (last 2 days).")

        req_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/140.0.0.0 Safari/537.36",
            "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        for ap_id, url, bank_cin, borrower_cin in results:
            # Clean URL formatting
            if not url:
                continue

            url = url.replace("\\", "/")
            if url.startswith("http:/") and not url.startswith("http://"):
                url = url.replace("http:/", "http://", 1)
            elif url.startswith("https:/") and not url.startswith("https://"):
                url = url.replace("https:/", "https://", 1)

            filename = generate_safe_filename_from_url(url)
            download_success = False

            try:
                response = requests.get(url, headers=req_headers, timeout=120, verify=False)
                if response.status_code == 200:
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "pdf" in content_type or response.content.startswith(b"%PDF"):
                        pdf_content = response.content
                        download_success = True
                    else:
                        log_console_and_file(f"⚠️ Skipped non-PDF content for: {url}")
                else:
                    log_console_and_file(f"❌ Failed to download: {url} (HTTP {response.status_code})")
                    with open(error_url_AP, mode="a", newline="", encoding="utf-8") as f:
                        csv.writer(f).writerow(["-", url, f"HTTP {response.status_code}"])
                    continue

            except Exception as e:
                log_console_and_file(f"⚠️ Error processing {url}: {str(e)}")
                with open(error_url_AP, mode="a", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerow(["-", url, str(e)])
                continue

            # ✅ Step 2: If downloaded, save under both CINs (bank & borrower)
            if download_success:
                for cin in [bank_cin, borrower_cin]:
                    if not cin:
                        continue

                    local_path = os.path.join(Local_Base_Directory, cin, "auction_property", filename + ".pdf")
                    s3_key_base = f"{S3_BASE_FOLDER}/{cin}/auction_property/{filename}"

                    if is_file_exists_locally(local_path):
                        continue

                    save_to_local_if_not_exists(pdf_content, local_path)
                    upload_to_s3_if_not_exists(pdf_content, s3_key_base)
                    log_console_and_file(f"✅ Saved Auction PDF for CIN: {cin} | ID: {ap_id}")

    finally:
        cursor.close()
        conn.close()
