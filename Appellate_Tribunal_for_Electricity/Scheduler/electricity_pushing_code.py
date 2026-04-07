import json
import os
import time
import requests
from datetime import datetime
import shutil

data_push_url = "http://103.233.79.196:8070/saveUpdate/UtilityBoard"
header = {
    "Content-Type": "application/json"
}



def utilityboardResponseByServer(file):
    global cin, company_name
    for datas in file:
        data = datas.replace('},', '}')
        # print("d ", data)
        try:
            data = json.loads(data)
            updated_data = json.dumps([data])
            print("d", updated_data)

            response = requests.post(url=data_push_url, data=updated_data, headers=header)
            print(response.content)

        except Exception as e:
            print("Exception occur in electricity :", e)
            textfile = open("Unprocessed_electricity_data.txt", "a+")
            textfile.write(data)



def data_push():

    path = r"D:\\SATElectricity\\Cin resolve\\resolve_file"
    pushed_path = r"D:\\SATElectricity\\Cin resolve\\pushed"

    # Ensure the pushed directory exists
    os.makedirs(pushed_path, exist_ok=True)

    dir_list = os.listdir(path)
    for electrycity_file in dir_list:
        electrycity_data = os.path.join(path, electrycity_file)

        try:
            with open(electrycity_data, 'r', encoding='cp1252') as file:
                utilityboardResponseByServer(file)
            time.sleep(1)

            # Move file after successful processing
            shutil.move(electrycity_data, os.path.join(pushed_path, electrycity_file))
            print(f"Moved pushed file: {electrycity_file}")
        except Exception as e:
            print(f"Error processing or moving file {electrycity_file}: {e}")
