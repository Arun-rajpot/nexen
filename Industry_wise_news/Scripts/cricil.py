import requests
import csv, json
import pandas as pd
from Utils import get_sentiment,get_industry_name,write_txt,create_unique
import re
from datetime import datetime, timedelta
current_date = datetime.now()


# Function to convert date format
def format_date(date_str):
    try:
        return datetime.strptime(date_str, "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return date_str  # Return original if conversion fails


def crisil_news():
    # URL to scrape
    url = "https://www.crisilratings.com/content/crisilratings/en/home/newsroom/press-releases/_jcr_content/wrapper_100_par/columncontrol/col-100-1/pressreleases.loadmore.json"

    # Headers
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cookie": "<Your_Cookie_Here>",
        "referer": "https://www.crisilratings.com/en/home/newsroom/press-releases.html",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    params = {
        "loadmore": "true",
        "month": "",
        "year": "2025",
        "searchValue": "",
        "onLoadPagescount": 0,
        "onLoadPDFcount": 0,
    }

    # Collect all data
    all_data = []

    for month in range(1, 13):  # Iterate over all months (1 to 12)
        params["month"] = f"{month:02d}"  # Zero-padded month
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            try:
                data = response.json()
                if data:  # Check if data is not empty
                    for item in data:  # Adjust key to match CRISIL's API response
                        headline = item.get("releaseTitle", "")
                        description = item.get("releaseDescription", None)
                        pdf_url = item.get("releasePath", "")
                        date = item.get("releaseCreatedDate", "")
                        industry = get_industry_name.find_industry(headline, description, get_industry_name.industry_keywords)

                        # Format date and append the processed item to the list
                        all_data.append({
                            "date": format_date(date),
                            "industry": industry,
                            "headline": headline,
                            "description": description,
                            "url": "https://www.crisilratings.com" + pdf_url
                        })
            except Exception as e:
                print(f"Error processing month {month}: {e}")

        else:
            print(f"Failed to fetch data for month {month}: {response.status_code}")

    # Save all data to text file
    for data in all_data:
        # Convert 'date' from string to datetime object
        data_date = datetime.strptime(data['date'], "%Y-%m-%d")
        print(data_date)

        # Check if the date is within the last 7 days
        if current_date - data_date <= timedelta(days=2):
            # If within 7 days, continue processing
            print(f"Date {data['date']} is within the last 7 days.")

            if data["description"]:
                data["description"] = re.sub(r'[^\x20-\x7E]', '', data["description"])

                # Remove multiple spaces and trim leading/trailing spaces
                data["description"] = re.sub(r'\s+', ' ', data["description"]).strip()

            if data["description"] and data["headline"]:
                sentiment = get_sentiment.get_sentence_sentiment(data["headline"] + " " + data["description"])
            else:
                sentiment = get_sentiment.get_sentence_sentiment(data["headline"])

            data["sentiment"] = sentiment

            print(data)
            write_txt.write_data_to_textfile(data,agancy="all")

        else:
            break

def crisil_main():
        crisil_news()
        # # Step 2: Compare with previous day's data
        # previous_file = write_txt.get_previous_date_file(agancy="cricil")
        # current_file = write_txt.get_current_date_file(agancy="cricil")
        # output_directory = "D:\\industry_wise_news\\Industry_News_Project\\unique_data"
        #
        # create_unique.compare_datewise_files(previous_file, current_file, output_directory)


# crisil_main()

