import importlib
import schedule
import time
from datetime import datetime
import traceback
import satelectricity
import Electricity_cin_resolve
import electricity_pushing_code
import os



def scheduler_main():

    # ===== data collection ======================
    satelectricity.satelectricity()

    #=========== Cin resolve ============================
    Electricity_cin_resolve.cin_resolve_main()


    # ========== data ====================================

    electricity_pushing_code.data_push()




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
