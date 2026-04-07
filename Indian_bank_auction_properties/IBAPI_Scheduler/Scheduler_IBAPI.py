import importlib
import schedule
import time
import os
from datetime import datetime
import traceback
import IBAPI_scraping
import create_unique
import IBAPI_cin_resolve
import ibapi_pushing_code



def scheduler_main():
    print("--------")
    # ===== data collection ======================

    IBAPI_scraping.IBAPI_Scraping()
    create_unique.compare_and_update_all()

    #=========== Cin resolve ============================

    # IBAPI_cin_resolve.IBAPI_cin_resolve()



    # ========== data  push into DB ====================================
    # ibapi_pushing_code.push_job()





# ================= Scheduler =================


def has_already_run_today():
    filepath = "last_run.txt"
    today_str = datetime.now().strftime("%Y-%m-%d")

    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            last_run_date = f.read().strip()
            return last_run_date == today_str
    return False

def mark_as_run_today():
    with open("last_run.txt", "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d"))

def monthly_runner():
    now = datetime.now()
    if now.day == 14 and now.strftime("%H:%M") >= "12:04":
        if not has_already_run_today():
            scheduler_main()
            mark_as_run_today()

schedule.every(1).minutes.do(monthly_runner)

print("🕒 Scheduler started......")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("\n❌ Scheduler stopped manually.")
