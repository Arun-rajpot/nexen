
import os
import requests
import csv
from datetime import datetime, timedelta
from urllib3.exceptions import InsecureRequestWarning
from utils import (
    get_database_connection,
    log_console_and_file,
    generate_safe_filename_from_url,
    upload_to_s3_if_not_exists,
    save_to_local_if_not_exists,
    is_file_exists_locally
)

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

error_url_BL_IEC = r'E:\\AWS_S3\\Daily_Pdf_download_S3\\Error_urls\\Black_list_iec_error_urls.csv'


def process_Black_list_iec(Local_base_directory,S3_Base_Directory):
    """Download last 2 days new/updated Blacklist IEC PDFs and upload to S3."""

    conn = get_database_connection()
    if not conn:
        log_console_and_file("❌ Database connection failed.")
        return

    cursor = conn.cursor()
    try:
        # Get last 2 days records
        two_days_ago = datetime.now() - timedelta(days=3)

        cursor.execute(
            """
            SELECT 
                c.id AS company_id,
                c.company_name,
                c.cin,
                BL.link
            FROM
                company_core.t_company_black_list_iec BL
            JOIN
                company_core.t_company_detail c
                ON c.id = BL.company_id
            WHERE
                BL.link IS NOT NULL
                AND BL.link <> ''
                AND (
                    BL.created >= %s OR
                    BL.modified >= %s
                )
            ORDER BY BL.link DESC;
            """,
            (two_days_ago, two_days_ago)
        )

        results = cursor.fetchall()
        log_console_and_file(f"🧾 Found {len(results)} Blacklist IEC records (last 2 days).")

        for company_id, company_name, cin, url in results:
            cin_folder = os.path.join(Local_base_directory, cin, "black_list_iec")
            os.makedirs(cin_folder, exist_ok=True)

            filename = generate_safe_filename_from_url(url) + ".pdf"
            local_path = os.path.join(cin_folder, filename)
            s3_key = f"{S3_Base_Directory}/{cin}/black_list_iec/{filename}.pdf"

            if is_file_exists_locally(local_path):
                log_console_and_file(f"⏭️ Already exists locally: {local_path}")
                continue

            try:
                # HEAD check first
                head = requests.head(url, timeout=20, verify=False, allow_redirects=True)
                content_type = head.headers.get("Content-Type", "").lower()

                # If HEAD fails → fallback to GET
                if not content_type:
                    response = requests.get(url, timeout=60, verify=False, stream=True)
                    content_type = response.headers.get("Content-Type", "").lower()
                else:
                    response = requests.get(url, timeout=60, verify=False, stream=True)

                if response.status_code == 200:
                    file_bytes = response.content
                    if (
                        "pdf" in content_type
                        or url.lower().endswith(".pdf")
                        or file_bytes.startswith(b"%PDF")
                    ):
                        # ✅ It's a PDF
                        save_to_local_if_not_exists(file_bytes, local_path)
                        upload_to_s3_if_not_exists(file_bytes, s3_key)
                        log_console_and_file(f"✅ PDF saved: {url}")
                    else:
                        log_console_and_file(f"⚠️ Not a PDF (skipped): {url} [{content_type}]")
                else:
                    log_console_and_file(f"❌ Download failed for {url} (HTTP {response.status_code})")
                    with open(error_url_BL_IEC, mode="a", newline="", encoding="utf-8") as f:
                        csv.writer(f).writerow([cin, url, f"HTTP {response.status_code}"])

            except Exception as e:
                log_console_and_file(f"⚠️ Error processing {url}: {str(e)}")
                with open(error_url_BL_IEC, mode="a", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerow([cin, url, f"{str(e)}"])

    finally:
        cursor.close()
        conn.close()