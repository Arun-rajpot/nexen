import requests
from bs4 import BeautifulSoup
from Utils import get_sentiment,write_txt,create_unique,get_industry_name
import re

from datetime import datetime, timedelta
current_date = datetime.now()
import fitz  # PyMuPDF
import requests
from io import BytesIO


def extract_and_clean_first_page_text(pdf_url):
    """
    Extract and clean text from the first page of a PDF fetched from a URL.

    Args:
        pdf_url (str): URL of the PDF file.

    Returns:
        str: Cleaned text content of the first page.
    """
    # Headers to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Accept": "application/pdf",
    }

    # Fetch the PDF from the URL
    response = requests.get(pdf_url, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch PDF from URL: {pdf_url}, status code: {response.status_code}")

    # Open the PDF from the response content
    pdf_stream = BytesIO(response.content)
    with fitz.open(stream=pdf_stream, filetype="pdf") as pdf:
        if pdf.page_count < 1:
            raise ValueError("The PDF has no pages.")

        # Extract text from the first page
        first_page = pdf[0]
        raw_text = first_page.get_text("text")

        # Clean the text
        cleaned_text = (
            raw_text.replace("\n", " ")  # Replace newlines with spaces
            .replace("\r", "")  # Remove carriage returns
            .replace("•", "")  # Remove bullet points
            .strip()  # Remove leading and trailing spaces
        )
        # Collapse multiple spaces into one
        cleaned_text = " ".join(cleaned_text.split())

        return cleaned_text

def convert_date(date_str):
    # Parse the input date string
    parsed_date = datetime.strptime(date_str, '%d %b %Y')
    # Format the date in the desired format
    return parsed_date.strftime('%Y-%m-%d')


industry_dict = {
    "104": "Affordable Housing Finance",
    "39": "Airlines",
    "96": "Airport Infrastructure",
    "124": "Alcoholic Beverages",
    "93": "Apparel & Fabric",
    "79": "Asset-Backed Security",
    "1": "Auto Components",
    "37": "Automobile",
    "90": "Banking",
    "87": "Banking Statistics",
    "95": "Basmati Rice",
    "88": "Bearing",
    "76": "Brokerages",
    "101": "Buffalo Meat",
    "103": "Bulk Tea",
    "122": "Capital Goods",
    "113": "Cashew",
    "40": "Cement",
    "116": "Chemicals - Basic Chemicals",
    "118": "Chemicals - Petrochemicals",
    "117": "Chemicals - Specialty Chemicals",
    "120": "Climate Series",
    "41": "Commercial Vehicles",
    "135": "Company Update",
    "42": "Construction",
    "43": "Construction Equipment",
    "127": "Consumer Durables",
    "97": "Corporate sector",
    "45": "Cotton & Manmade Yarns",
    "81": "Credit Quality Trends",
    "138": "Critical Minerals",
    "121": "Cross-sectoral trends and outlook",
    "119": "Dairy",
    "130": "Data Centres",
    "133": "Defence",
    "83": "Economic Outlook & Macro Trends",
    "131": "Edible Oil",
    "123": "Electric Vehicles",
    "47": "Ferrous Metals",
    "48": "Fertilizers",
    "89": "Financial Markets & Banking Update",
    "69": "Footwear",
    "70": "Gas Utilities",
    "78": "General Insurance",
    "125": "Healthcare",
    "108": "Hospital",
    "49": "Hotels",
    "75": "Housing Finance Companies",
    "98": "Housing Finance Statistics",
    "132": "ICRA Market Outreach",
    "115": "Indian Retail Industry",
    "110": "IT Services",
    "50": "Jewellery",
    "77": "Life Insurance",
    "102": "Logistics - Road",
    "92": "Market Update",
    "74": "Micro Finance Institutions",
    "80": "Mortgage-Backed Security",
    "106": "Multiplex Industry",
    "73": "NBFC – Infrastructure",
    "72": "NBFC – Retail & Commercial Finance",
    "112": "Non-Basmati Rice",
    "51": "Non-ferrous Metals",
    "52": "Oil & Gas",
    "105": "Others",
    "137": "Outlook FY2025",
    "129": "Paper Manufacturing",
    "54": "Passenger Vehicles",
    "55": "Pharmaceuticals",
    "107": "Port Logistics",
    "56": "Ports",
    "57": "Poultry",
    "58": "Power",
    "134": "Print Media",
    "59": "Real Estate",
    "60": "Refining & Marketing",
    "62": "Renewable Energy",
    "136": "Rice Millers",
    "61": "Roads & Highways",
    "94": "Seeds",
    "114": "Ship Breaking",
    "91": "Small Finance Banks",
    "139": "Small NBFCs",
    "84": "State Government Finance",
    "63": "Sugar",
    "64": "Telecom Services",
    "109": "Telecom Tower",
    "111": "Tiles",
    "65": "Tractors",
    "126": "Transformers",
    "66": "Two Wheelers",
    "67": "Tyres",
}



def fetch_icra_news():
    session = requests.Session()

    # Step 1: GET request to fetch the main page and get the verification token
    base_url = "https://www.icra.in/Media/MediaRelease"
    response = session.get(base_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    })
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the __RequestVerificationToken
    token_input = soup.find('input', {'name': '__RequestVerificationToken'})
    if not token_input:
        print("Failed to find verification token.")
        return
    token = token_input['value']

    # Initialize the output list
    all_media_data = []

    # Iterate over all SectorIds in the industry dictionary
    for sector_id, industry_name in industry_dict.items():
        print(f"Fetching data for SectorId {sector_id} ({industry_name})...")

        # Step 2: POST request to fetch data for the given sector
        url = "https://www.icra.in/Media/MediaReleasePost"
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'www.icra.in',
            'Origin': 'https://www.icra.in',
            'Referer': 'https://www.icra.in/Media/MediaRelease',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }
        payload = {
            '__RequestVerificationToken': token,
            'SectorId': sector_id,
            'DateFrom': '',
            'DateTo': ''
        }

        response = session.post(url, headers=headers, data=payload)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all media_print_list divs
            media_releases = soup.find_all('div', class_='media_print_list')

            # Check if any data was returned
            if not media_releases:
                print(f"No data found for SectorId {sector_id}.")
                continue

            # Extract data from the response
            for media_list in media_releases:
                # Extract date
                date = media_list.find('span', class_='date').text.strip()
                formated_date = convert_date(date)
                # Extract source
                source = media_list.find('span', class_='source').text.strip()
                source = source if source != '--' else None

                # Extract title and URL
                title_tag = media_list.find('p', class_='media_newsLink')
                title = title_tag.text.strip()
                title_url = title_tag.find_parent('a')['href']

                try:
                    description = extract_and_clean_first_page_text("https://www.icra.in"+title_url)
                    print("--- Cleaned First Page Text ---\n")
                except ValueError as e:
                    print(e)
                # Extract download link
                download_tag = media_list.find('a', class_='link_download')
                download_url = download_tag['href'] if download_tag else None
                # print(industry_name)

                # Iterate through industry keywords to find the matching industry
                found = False  # Flag to check if a match is found
                for industry_name_key, industry_keywords in get_industry_name.industry_keywords.items():
                    if industry_name in industry_keywords:
                        new_industry = industry_name_key
                        # print(new_industry)
                        found = True
                        break

                # If no matching industry is found
                if not found:
                    new_industry = "Others"
                    # New_industry =
                # Append data to the list
                all_media_data.append({
                    'date': formated_date,
                    'industry': new_industry,
                    'headline': title,
                    'description': description[26:],
                    'url': f"https://www.icra.in{title_url}"
                })
        else:
            print(f"Failed to fetch data for SectorId {sector_id}: {response.status_code}")

    for data in all_media_data:
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
            continue

def icra_main():
        fetch_icra_news()
        # # Step 2: Compare with previous day's data
        # previous_file = write_txt.get_previous_date_file(agancy="icra")
        # current_file = write_txt.get_current_date_file(agancy="icra")
        # output_directory = "D:\\industry_wise_news\\Industry_News_Project\\unique_data"
        #
        # create_unique.compare_datewise_files(previous_file, current_file, output_directory)


# icra_main()
