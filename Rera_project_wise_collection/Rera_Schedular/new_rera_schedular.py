import importlib
import schedule
import time
import os
from datetime import datetime
import traceback
import asyncio
import  New_rera_pushing_job
import Create_unique ,Cin_resolver

def log_error(state_name, error):
    with open("rera_error_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {state_name}: {error}\n")
        f.write(traceback.format_exc() + "\n")

def run_state(state_name, module_name, function_name):
    try:
        module = importlib.import_module(f"Scripts.{module_name}")
        func = getattr(module, function_name)

        if state_name.lower() == "odisha":
            asyncio.run(func())  # Odisha ke liye async function run
        else:
            func()

        print(f"✅ Completed: {state_name}")
    except Exception as e:
        log_error(state_name, str(e))
        print(f"❌ Error in {state_name}")

def main():
    print(f"\n🚀 RERA run started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    states = [
        ("Aasam", "Aasam_rera", "rera_Aasam"),
        ("Andhra Pradesh", "Andhra_pradesh_rera", "rera_andhra"),
        ("Bihar", "Bihar_rera", "rera_bihar"),
        ("Chhattisgarh", "CG_rera", "rera_cg"),
        ("Delhi", "Delhi_rera", "rera_delhi"),
        ("Goa", "Goa_rera", "rera_goa"),
        ("Gujarat", "Gujrat_rera", "rera_gujarat"),
        ("Haryana", "Haryana_rera", "rera_haryana"),
        ("Himachal Pradesh", "Himachal_pradesh_rera", "rera_himachal_pradesh"),
        ("Jharkhand", "Jharkhand_rera", "rera_jharkhand"),
        ("Karnataka", "Karnataka_rera", "rera_karnataka"),
        ("Kerala", "Kerala_rera", "rera_kerala"),
        ("Madhya Pradesh", "Madhya_pradesh_rera", "rera_mp"),
        ("Maharashtra", "Maharashtra_rera", "rera_maharashtra"),
        ("Odisha", "Odisha_rera", "rera_Odisha"),
        ("Punjab", "Panjab_rera", "rera_punjab"),
        ("Rajasthan", "Rajasthan_rera", "rera_rajasthan"),
        ("Tamil Nadu", "Tamil_nadu_rera", "rera_tamil_nadu"),
        ("Telangana", "Telangana_rera", "rera_telangana"),
        ("Uttar Pradesh", "Up_rera", "rera_up"),
        ("West Bengal", "West_bengal_rera", "rera_West_bengal"),
    ]

    for state in states:
        run_state(*state)

    #========================== create unique file ==============================
    Create_unique.create_unique()


    #============================================================================
    #============================Cin Resolve ====================================

    Cin_resolver.process_all_unique_files()

    # ============================================================================
    # ============================Push data  ====================================

    # New_rera_pushing_job.push_job()



    print(f"✅ RERA run completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

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
            main()
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
