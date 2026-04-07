import json
import os
import requests
import time
import shutil
from datetime import datetime

data_push_url = "http://103.233.79.196:8070/saveUpdate/AuctionProperty"
header = {
    "Content-Type": "application/json"
}



def IBAPI_ResponseByServer(file):
    global cin, company_name
    for datas in file:
        data = datas.replace('},', '}')
        # print("d ", data)
        try:
            data = json.loads(data)
            data['TYPE_OF_TITLE_DEED'] = data['TYPE_OF_TITLE_DEED'].title()
            data['AUTHORISED_OFFICER'] = data['AUTHORISED_OFFICER'].title()
            # Convert the updated data back to JSON format
            updated_data = json.dumps([data])
            print("d", updated_data)

            response = requests.post(url=data_push_url, data=updated_data, headers=header)
            print(response.content)

        except Exception as e:
            print("Exception occur in epfo :", e)
            textfile = open("Unprocessed_epfo_data_ibapi.txt", "a+")
            textfile.write(data)


def push_job():
    resolve_path = r"D:\\IBAPI\\IBAPI_project\\Cin_Resolve\\Resolve"
    pushed_path = r"D:\\IBAPI\\IBAPI_project\\Cin_Resolve\\Pushed"

    # Ensure pushed folder exists
    os.makedirs(pushed_path, exist_ok=True)

    dir_list = os.listdir(resolve_path)

    for IBAPI_file in dir_list:
        try:
            IBAPI_data_path = os.path.join(resolve_path, IBAPI_file)
            with open(IBAPI_data_path, 'r', encoding='cp1252') as file:
                IBAPI_ResponseByServer(file)

            # Move the file after successful push
            shutil.move(IBAPI_data_path, os.path.join(pushed_path, IBAPI_file))
            print(f"✅ Moved pushed file: {IBAPI_file}")
            time.sleep(1)

        except Exception as e:
            print(f"❌ Error processing file {IBAPI_file}: {e}")