import json
import os
import time
import requests
import shutil

data_push_url = "http://103.233.79.196:8070/companies/updates_/judgement"
header = {
    "Content-Type": "application/json"
}


def JudgementResponseByServer(file):
    for datas in file:
        data = datas.replace('},', '}')
        print("pro==", data)

        try:
            response = requests.post(url=data_push_url, data=data, headers=header)
            print(response.content)
            print(response.status_code)
            if response.status_code == 200:
                pass  # Success
            else:
                with open("Unprocessed_set_data.txt", "a+", encoding="utf-8") as textfile:
                    textfile.write(data + "\n")
        except Exception as e:
            print("Exception occur in push:", e)
            with open("Unprocessed_sat_data.txt", "a+", encoding="utf-8") as textfile:
                textfile.write(data + "\n")




def push_job():
    path = r"D:\SAT_DATA\SAT_project\Cin_resolve\Resolve"
    dir_list = os.listdir(path)
    for dcourt_file in dir_list:
        print(f"Processing file: {dcourt_file}")
        dcourt_data = os.path.join(path, dcourt_file)

        # Open and process file
        with open(dcourt_data, 'r', encoding='cp1252') as file:
            JudgementResponseByServer(file)

        # ✅ Move the processed file to Pushed_data folder
        dest_path = os.path.join(r"D:\SAT_DATA\SAT_project\Cin_resolve\Pushed_data", dcourt_file)
        shutil.move(dcourt_data, dest_path)
        print(f"✅ Moved to Pushed_data: {dcourt_file}")

        time.sleep(1)
