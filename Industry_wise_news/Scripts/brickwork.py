# ======================================================brickworkratings====================================

import requests
from bs4 import BeautifulSoup
from Utils import get_sentiment,get_industry_name,write_txt,create_unique
import re
from datetime import datetime, timedelta
current_date = datetime.now()

def brikcwork():
    # URL to scrape
    url = "https://www.brickworkratings.com/Media.aspx"
    res = requests.get(url)

    # Parse the HTML content
    soup = BeautifulSoup(res.text, "html.parser")

    # Find all mediaSec divs
    media_sections = soup.find_all("div", class_="mediaSec")

    # List to store extracted data
    all_results = []

    # Define a regex pattern to match dates
    date_pattern = re.compile(r"\b(?:\d{1,2} \w+ \d{4})\b")  # e.g., 17 August 2022


    # Iterate through each mediaSec div and extract details
    for media_section in media_sections:
        # print(media_section)
        try:
            # Extract headline (if present)
            headline_tag = media_section.find("h4")
            headline = headline_tag.text.strip() if headline_tag else None

            # Extract description (if present)
            description_tag = media_section.find("p")
            description = description_tag.text.strip() if description_tag else None

            # Extract URL (if present)
            url_tag = headline_tag.find("a") if headline_tag else None
            media_url = url_tag["href"] if url_tag else None

            # Extract date using regex
            text_content = media_section.get_text(separator=" ").strip()  # Combine all text in the section
            date_match = date_pattern.search(text_content)
            original_date = date_match.group(0) if date_match else None
            # Convert to datetime object
            formats = ["%d %b %Y", "%d %B %Y"]
            for fmt in formats:
                try:
                    date_object = datetime.strptime(original_date, fmt)
                    formatted_date = date_object.strftime("%Y-%m-%d")
                    break
                except ValueError:
                    continue
            # Determine the industry
            matched_industry = get_industry_name.find_industry(headline, description, get_industry_name.industry_keywords)

            # Append the extracted details to the results list
            all_results.append({
                "date": formatted_date,
                "industry": matched_industry if matched_industry else None,
                "headline": headline,
                "description": description,
                "url": f"https://www.brickworkratings.com/{media_url}" if media_url else None,
            })

        except Exception as e:
            print(f"Error processing a media section: {e}")

    # Output the results
    for data in all_results:
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

def brikcwork_main():
        brikcwork()
        # # Step 2: Compare with previous day's data
        # previous_file = write_txt.get_previous_date_file(agancy="brikcwork")
        # current_file = write_txt.get_current_date_file(agancy="brikcwork")
        # output_directory = "D:\\industry_wise_news\\Industry_News_Project\\unique_data"
        #
        # create_unique.compare_datewise_files(previous_file, current_file, output_directory)


# brikcwork_main()
