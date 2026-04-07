import requests
import json
from Utils import get_sentiment,write_txt,create_unique,get_industry_name
import re
import fitz
from io import BytesIO
from datetime import datetime, timedelta
current_date = datetime.now()



# Industry dictionary
def get_industry(code):
    industry_dict = {
        '9': "Auto and Auto Components",
        '10': "Agri and Agri-Allied",
        '11': "BFSI",
        '12': "Building Construction Material",
        '13': "Capital Goods",
        '14': "Infrastructure",
        '15': "Manufacturing",
        '16': "Metals and Mining",
        '17': "Services",
        '18': "Special Studies",
    }
    return industry_dict.get(code)

def clean_text(text):
    """
    Clean up unwanted characters, extra spaces, and other irrelevant text.
    """
    # Remove unwanted characters such as newline and carriage return
    text = text.replace("\n", " ").replace("\r", "")

    # Remove extra spaces (more than one consecutive space)
    text = re.sub(r'\s+', ' ', text)

    # Remove unwanted non-alphanumeric characters (if needed)
    text = re.sub(r'[^\w\s,;.!?-]', '', text)  # Keep common punctuation

    # Strip leading and trailing spaces
    return text.strip()
# Clean description text

def extract_text_by_heading_from_url(pdf_url, headings):
    """
    Extract paragraphs following specific headings from the first two pages of a PDF fetched from a live URL.
    If a heading is not found on both pages, extract all text from the first page.
    Returns the extracted content in a dictionary with key 'data'.
    """
    extracted_data = {"data": ""}  # Initialize the result with an empty string for the 'data' key

    # Fetch the PDF from the URL
    response = requests.get(pdf_url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch PDF from URL: {pdf_url}, status code: {response.status_code}")

    # Open the PDF from the response content
    pdf_stream = BytesIO(response.content)
    with fitz.open(stream=pdf_stream, filetype="pdf") as pdf:
        # Iterate through the first two pages (or fewer if the PDF has less than two pages)
        for page_number in range(min(2, pdf.page_count)):
            page = pdf[page_number]

            # Extract all text blocks on the current page
            blocks = page.get_text("blocks")
            sorted_blocks = sorted(blocks, key=lambda b: b[1])  # Sort by vertical position (y-coordinate)

            # Extract content based on headings
            for heading in headings:
                # Ensure that extracted_data["data"] is not None before checking for headings
                if extracted_data["data"] and heading in extracted_data["data"]:  # Skip if heading is already found
                    continue

                found = False
                paragraph = []
                for i, block in enumerate(sorted_blocks):
                    if heading.lower() in block[4].lower():  # Check if heading exists in the block
                        found = True
                        # Collect all text following the heading until a blank block or unrelated block
                        for following_block in sorted_blocks[i + 1:]:
                            text = clean_text(following_block[4].strip())
                            if not text or any(
                                    h.lower() in text.lower() for h in headings):  # Stop at blank or next heading
                                break
                            paragraph.append(text)
                        extracted_data["data"] = " ".join(paragraph).strip()  # Combine lines into a single paragraph
                        break
                if not found and not extracted_data["data"]:
                    # Mark as None only if heading not found in both pages
                    extracted_data["data"] = None

        # If heading is not found on both pages, extract all text from the first page
        if not extracted_data["data"] or extracted_data["data"] is None:
            first_page = pdf[0]
            blocks = first_page.get_text("blocks")
            sorted_blocks = sorted(blocks, key=lambda b: b[1])
            all_text = " ".join([clean_text(block[4].strip()) for block in sorted_blocks if block[4].strip()])
            extracted_data["data"] = all_text

    return extracted_data
# def clean_description(description):
#     if description:
#         # Remove all HTML tags and unwanted spaces
#         description = re.sub(r'<[^>]+>', '', description)  # Remove HTML tags
#         description = description.replace('\n', ' ').replace('\r', ' ').strip()  # Remove newlines and extra spaces
#         description = ' '.join(description.split())  # Normalize spaces between words
#     return description


# Prepare the final payload
def final_payload(data):
    date = data['Date']
    date_obj = datetime.strptime(date, "%d-%m-%Y")

    # Format into YYYY-MM-DD
    formatted_date = date_obj.strftime("%Y-%m-%d")
    # Iterate through industry keywords to find the matching industry
    found = False  # Flag to check if a match is found
    for industry_name_key, industry_keywords in get_industry_name.industry_keywords.items():
        if get_industry(data.get('Category')) in industry_keywords:
            new_industry = industry_name_key
            print(new_industry)
            found = True
            break

    # If no matching industry is found
    if not found:
        new_industry = "Others"

    headings = ["Overview", "Synopsis"]  # Specify the headings dynamically
    pdf_url = "https://www.careratings.com/uploads/newsfiles/" + data['PDf']
    pdf_data = extract_text_by_heading_from_url(pdf_url, headings)
    final_data = {
        'date': formatted_date,
        'industry': new_industry,
        'headline': data['Title'],
        'description': pdf_data['data'],
        'url': "https://www.careratings.com/uploads/newsfiles/" + data['PDf']
    }
    return final_data



# Main function to fetch data and save to text file
def care_news():
    url = "https://www.careratings.com/insightspagedata"
    params = {
        "PageId": "",
        "SectionId": 5034,
        "YearID": 2025,
        "MonthID": 0
    }

    # Headers for the request
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.careratings.com/industry-research"
    }

    # Cookies (if needed)
    cookies = {
        "__uzma": "494d07da-0c22-4f10-880f-bdb87f495853",
        "__uzmb": "1731407078",
        "__uzme": "9871",
        "user_cookie_consent": "1",
        "XSRF-TOKEN": "your-xsrf-token",
        "laravel_session": "your-laravel-session"
    }

    # Sending the GET request
    response = requests.get(url, params=params, headers=headers, cookies=cookies)
    # print(response.text)
    json_data = json.loads(response.text)
    datas = json_data['data']

    # Collect all final data
    final_data_list = []
    for data in datas:
        final_data = final_payload(data)
        final_data_list.append(final_data)

    # Save all data to text file
    for data in final_data_list:
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
def care_main():
        care_news()

        # # Step 2: Compare with previous day's data
        # previous_file = write_txt.get_previous_date_file(agancy="care")
        # current_file = write_txt.get_current_date_file(agancy="care")
        # output_directory = "D:\\industry_wise_news\\Industry_News_Project\\unique_data"
        #
        # create_unique.compare_datewise_files(previous_file, current_file, output_directory)


# care_main()

