import json
import os
from datetime import datetime, timedelta

def get_previous_date_file(agancy):
    today = datetime.now()
    previous_date = today - timedelta(days=1)
    return f"D:\\industry_wise_news\\Industry_News_Project\\data\\{agancy}_{previous_date.strftime('%Y-%m-%d')}_news.txt"

def get_current_date_file(agancy):
    today = datetime.now()
    return f"D:\\industry_wise_news\\Industry_News_Project\\data\\{agancy}_{today.strftime('%Y-%m-%d')}_news.txt"


def write_data_to_textfile(payload, agancy):
    try:
        # Convert the payload to a JSON string
        post_data = json.dumps(payload, ensure_ascii=False)

        # Get the current date
        current_date = datetime.now().strftime('%Y-%m-%d')

        # Directory path for saving data
        directory = "D:\\industry_wise_news\\Industry_News_Project\\data"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # File path for the current date
        file_path = os.path.join(directory, f"{agancy}_{current_date}_news.txt")

        # Open the file in append mode and write the JSON string
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(post_data)
            f.write(',\n')
    except Exception as e:
        print(f"Exception occurred while saving data: {e}")
