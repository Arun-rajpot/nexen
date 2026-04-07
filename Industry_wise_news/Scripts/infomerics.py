import requests
from bs4 import BeautifulSoup
from Utils import get_sentiment,get_industry_name,write_txt,create_unique
import re

from datetime import datetime, timedelta
current_date = datetime.now()

def infomerics():

    url = 'https://www.infomerics.com/publication/industry-report'
    # Fetch the HTML content from the URL
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all report containers
        report_containers = soup.select('.col-md-4 .service-item')

        # Initialize a list to store the report data
        reports = []

        for container in report_containers:
            # Extract headline
            headline_tag = container.select_one('h3')
            headline = headline_tag.text.strip() if headline_tag else None

            # Extract date
            date_tag = container.select_one('.date')
            date = None
            if date_tag:
                try:
                    date = datetime.strptime(date_tag.text.strip(), '%A, %B %d %Y').strftime('%Y-%m-%d')
                except ValueError:
                    date = None

            # Extract URL
            url_tag = container.select_one('a.overlay_link')
            report_url = url_tag['href'] if url_tag else None

            # Initialize detailed data and PDF URL
            detailed_data = None
            pdf_url = None

            # Fetch detailed data from the report URL
            if report_url:
                detailed_response = requests.get(report_url)
                if detailed_response.status_code == 200:
                    detailed_soup = BeautifulSoup(detailed_response.text, 'html.parser')

                    # Example: Extract a detailed description (adjust selector as needed)
                    detailed_description_tag = detailed_soup.select_one('.section .container p')
                    detailed_data = detailed_description_tag.text.strip() if detailed_description_tag else None

                    # Extract the PDF URL (assuming it's in an <a> tag with a class or href pattern)
                    pdf_tag = detailed_soup.select_one('a[href$=".pdf"]')  # Looks for a link ending with .pdf
                    if pdf_tag:
                        pdf_url = pdf_tag['href']
                        # If the URL is relative, make it absolute
                        if not pdf_url.startswith('http'):
                            pdf_url = f"https://www.infomerics.com{pdf_url}"

            # Find the industry for the current report
            industry = get_industry_name.find_industry(headline, detailed_data, get_industry_name.industry_keywords)

            # Append the report data to the list
            reports.append({
                'date': date,
                'industry': industry,  # Store the industry name
                'headline': headline,
                'description': detailed_data,
                'url': pdf_url,  # Store the PDF URL
            })

        for data in reports:
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
    else:
        print(f"Failed to fetch the URL. Status code: {response.status_code}")

def infomerics_main():
        infomerics()
        # # Step 2: Compare with previous day's data
        # previous_file = write_txt.get_previous_date_file(agancy="infomerics")
        # current_file = write_txt.get_current_date_file(agancy="infomerics")
        # output_directory = "D:\\industry_wise_news\\Industry_News_Project\\unique_data"
        #
        # create_unique.compare_datewise_files(previous_file, current_file, output_directory)

# infomerics_main()