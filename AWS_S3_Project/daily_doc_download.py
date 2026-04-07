
# ============= doc_download.py ==============================================

import os
import threading
import schedule
import time
from datetime import datetime
from utils import get_database_connection, log_console_and_file
from Ratings_table import process_recent_rating_downloads
from Nclt_table import process_recent_nclt_cases
from Judgement_table import process_recent_judgement_documents
from Black_list_iec import process_Black_list_iec
from Auction_property import process_recent_auction_property_cases
from Utility_board import process_recent_utility_board


def run_in_thread(target_func, Local_base_directory,S3_BASE_FOLDER):
    """Run one process in a separate thread."""
    try:
        log_console_and_file(f"🚀 Starting {target_func.__name__} ...")
        target_func(Local_base_directory,S3_BASE_FOLDER)
        log_console_and_file(f"✅ Completed {target_func.__name__}")
    except Exception as e:
        log_console_and_file(f"❌ Error in {target_func.__name__}: {e}")


def create_cin_folders_and_process(Local_base_directory,S3_BASE_FOLDER, conn):
    """Run all processes in parallel threads."""
    try:
        functions = [
            process_recent_rating_downloads,
            process_recent_nclt_cases,
            process_recent_judgement_documents,
            process_Black_list_iec,
            process_recent_auction_property_cases,
            process_recent_utility_board
        ]

        threads = []
        for func in functions:
            thread = threading.Thread(target=run_in_thread, args=(func, Local_base_directory,S3_BASE_FOLDER))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        log_console_and_file("✅ All processes finished successfully.")

    finally:
        conn.close()
        log_console_and_file("🔒 Database connection closed.")


def job():
    """The scheduled job that runs daily."""
    log_console_and_file(f"🕒 Scheduler triggered at {datetime.now()}")
    Local_base_directory = r"F:\nexensus\nexsftp\documents"
    S3_BASE_FOLDER = "documents"
    conn = get_database_connection()
    
    if conn:
        print("==")
        create_cin_folders_and_process(Local_base_directory, S3_BASE_FOLDER,conn)
    else:
        log_console_and_file("Database connection failed.")


def main():
    # Run every day at a fixed time
    schedule.every().day.at("01:05").do(job)   # ⏰ change time if needed

    log_console_and_file("📅 Daily scheduler started (runs every day .......)")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
