import fitz
from io import BytesIO
import requests
import re
from bs4 import BeautifulSoup
from Utils import get_sentiment,get_industry_name,write_txt,create_unique
from datetime import datetime, timedelta
current_date = datetime.now()
def extract_text_by_heading_from_url(pdf_url, headings):
    """
    Extract all text from the first two pages of a PDF following specific headings.
    If heading is not found on both pages, extract all text from the first page.
    Clean the text by removing unwanted characters like \n and \r.
    """
    extracted_data = {}

    # Fetch the PDF from the URL
    response = requests.get(pdf_url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch PDF from URL: {pdf_url}, status code: {response.status_code}")

    # Open the PDF from the response content
    pdf_stream = BytesIO(response.content)
    with fitz.open(stream=pdf_stream, filetype="pdf") as pdf:
        # Iterate through the first two pages (or all pages if fewer than 2 exist)
        for page_number in range(min(2, pdf.page_count)):
            page = pdf[page_number]

            # Extract all text blocks on the current page
            blocks = page.get_text("blocks")
            sorted_blocks = sorted(blocks, key=lambda b: b[1])  # Sort by vertical position (y-coordinate)

            # Extract content based on headings
            for heading in headings:
                if heading in extracted_data and extracted_data[heading] is not None:
                    # Skip if the heading is already found on a previous page
                    continue

                found = False
                for i, block in enumerate(sorted_blocks):
                    if heading.lower() in block[4].lower():  # Check if heading exists in the block
                        found = True
                        # Collect all text following the heading (including subsequent blocks)
                        paragraphs = [block[4].strip()]  # Include the heading block
                        for following_block in sorted_blocks[i + 1:]:
                            text = following_block[4].strip()
                            if text:  # Only include non-blank blocks
                                paragraphs.append(text)
                        # Combine lines into a single paragraph and clean unwanted characters
                        extracted_data[heading] = " ".join(paragraphs).replace("\n", " ").lstrip("Press Release").replace("\r", "").strip()
                        break
                if not found and heading not in extracted_data:
                    # Mark as None only if it's not yet checked
                    extracted_data[heading] = None

        # If the heading is not found on both pages, extract all text from the first page
        for heading in headings:
            if heading not in extracted_data or extracted_data[heading] is None:
                first_page = pdf[0]
                blocks = first_page.get_text("blocks")
                sorted_blocks = sorted(blocks, key=lambda b: b[1])
                all_text = " ".join([block[4].strip() for block in sorted_blocks if block[4].strip()])
                extracted_data[heading] = all_text.replace("\n", " ").replace("\r", "").lstrip("Press Release").strip()

    return extracted_data

# Function to clean and convert date
def clean_and_convert_date(date_str):
    # Remove ordinal suffixes like 'st', 'nd', 'rd', 'th'
    cleaned_date = re.sub(r'(st|nd|rd|th)', '', date_str)
    return datetime.strptime(cleaned_date.strip(), '%d %b %y').strftime('%Y-%m-%d')


# Main function to scrape and process news
def Acuite_news():
    url = "https://www.acuite.in/releases.htm"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all rows in the table
    rows = soup.find_all('tr')

    # List to store extracted data
    data_list = []

    # Extract data
    for row in rows:
        date = row.find('td', width="20%").text.strip()
        link_tag = row.find('a')
        title = link_tag.text.strip()
        url = f"https://www.acuite.in//{link_tag['href']}"  # Adjust base URL if needed
        headings = ["Press Release"]
        pdf_data = extract_text_by_heading_from_url(url, headings)
        # Detect industry
        industry = get_industry_name.find_industry(title, pdf_data['Press Release'], get_industry_name.industry_keywords)

        # Append to list
        data_list.append({
            'date': clean_and_convert_date(date),
            'industry': industry,
            'headline': title,
            'description': pdf_data["Press Release"],
            'url': url
        })

    # Print the extracted data

    for data in data_list:
        # Convert 'date' from string to datetime object
        data_date = datetime.strptime(data['date'], "%Y-%m-%d")
        print(data_date)

        # Check if the date is within the last 7 days
        if current_date - data_date <= timedelta(days=2):
            # If within 7 days, continue processing
            print(f"Date {data['date']} is within the last 7 days.")

            if data["description"] and data["headline"]:
                sentiment = get_sentiment.get_sentence_sentiment(data["headline"] + " " + data["description"])
            else:
                sentiment = get_sentiment.get_sentence_sentiment(data["headline"])

            data["sentiment"] = sentiment
            print(data)
            write_txt.write_data_to_textfile(data, agancy="all")
        else:
            # Break the loop if the date is not within the last 7 days
            break






def Acuite_main():
        Acuite_news()
#
#         # # Step 2: Compare with previous day's data
#         # previous_file = write_txt.get_previous_date_file(agancy="Aciute")
#         # current_file = write_txt.get_current_date_file(agancy="Aciute")
#         # output_directory = "D:\\industry_wise_news\\Industry_News_Project\\unique_data"
#         #
#         # create_unique.compare_datewise_files(previous_file, current_file, output_directory)
#
#
#
# Acuite_main()
