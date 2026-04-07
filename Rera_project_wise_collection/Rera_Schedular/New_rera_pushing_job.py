import json
import os
import time
import requests
from datetime import datetime
import shutil

def push_job():

    data_push_url = "http://103.233.79.196:8070/saveUpdate/ReraProjectDetail"
    header = {"Content-Type": "application/json"}

    resolve_dir = r"D:\\New_Rera\\New_rera_project\\Cin_Resolve\\Resolve"
    pushed_dir = r"D:\New_Rera\New_rera_project\Cin_Resolve\Pushed_File"
    os.makedirs(pushed_dir, exist_ok=True)

    dir_list = os.listdir(resolve_dir)

    def ReraResponseByServer(file_lines):
        for line in file_lines:
            data = line.replace('},', '}').strip()
            try:
                data_json = json.loads(data)
                updated_data = json.dumps([data_json])
                print("Data:", updated_data)

                response = requests.post(url=data_push_url, data=updated_data, headers=header)
                print("Status:", response.status_code)

                if response.status_code != 200:
                    with open("Unprocessed_Rera_data.txt", "a+", encoding="utf-8") as textfile:
                        textfile.write(data + "\n")
            except Exception as e:
                print("Exception occurred while pushing data:", e)
                with open("Unprocessed_Rera_data.txt", "a+", encoding="utf-8") as textfile:
                    textfile.write(data + "\n")

    for filename in dir_list:
        file_path = os.path.join(resolve_dir, filename)
        print(f"Processing file: {filename}")

        with open(file_path, 'r', encoding='cp1252') as file:
            lines = file.readlines()
            ReraResponseByServer(lines)

        # After processing, move the file to 'pushed' folder
        shutil.move(file_path, os.path.join(pushed_dir, filename))
        print(f"Moved {filename} to pushed directory.\n")
        time.sleep(0.1)

    print("✅ All files processed and moved to pushed folder.")
