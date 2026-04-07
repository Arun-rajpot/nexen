import requests
from bs4 import BeautifulSoup
import json
from Utils import get_sentiment,write_txt,create_unique,get_industry_name
import re

from datetime import datetime, timedelta
current_date = datetime.now()


def final_payload(data, id):
    overview = data['overview']
    overview = BeautifulSoup(overview, 'html.parser').text.replace('\r\n', ' ').replace('\n', ' ').replace(
        '·\xa0\xa0\xa0\xa0\xa0\xa0', ' ').strip()
    # Remove any extra whitespace from overview text
    date = data['effectiveDate']
    date_obj = datetime.strptime(date, "%b %d, %Y")
    formatted_date = date_obj.strftime("%Y-%m-%d")

    # get industry_name
    found = False  # Flag to check if a match is found
    for industry_name_key, industry_keywords in get_industry_name.industry_keywords.items():
        if data['industry'] in industry_keywords:
            new_industry = industry_name_key
            print(new_industry)
            found = True
            break

    # If no matching industry is found
    if not found:
        new_industry = "Others"

    final_data = {
        'date': formatted_date,
        'industry': new_industry,
        'headline': data['pressReleaseTitle'],
        'description': overview,
        'url': "https://www.indiaratings.co.in/pressrelease/" + str(id)
    }
    return final_data


def industry_news_indiarating():
    url = "https://www.indiaratings.co.in/pressReleases/GetListingIndustryWise"
    payload = {
        'type': 'NRAC',
        'industryIds': ''
    }
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers, params=payload)
    get_datas = json.loads(response.text)
    for data in get_datas:
        pressReleaseId = data["pressReleaseID"]
        new_url = "https://www.indiaratings.co.in/pressReleases/GetPressreleaseData"
        new_payload = {
            'pressReleaseId': pressReleaseId
        }
        new_response = requests.get(new_url, headers=headers, params=new_payload)
        new_get_datas = json.loads(new_response.text)
        if new_get_datas:
            # Process the detailed data
            data = final_payload(new_get_datas[0], pressReleaseId)

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
def indiarating():
        industry_news_indiarating()
        # # Step 2: Compare with previous day's data
        # previous_file = write_txt.get_previous_date_file(agancy="india_rating")
        # current_file = write_txt.get_current_date_file(agancy="india_rating")
        # output_directory = "D:\\industry_wise_news\\Industry_News_Project\\unique_data"
        #
        # create_unique.compare_datewise_files(previous_file, current_file, output_directory)


# indiarating()
