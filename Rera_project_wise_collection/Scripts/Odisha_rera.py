import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
from datetime import datetime
from Scripts.write_to_txt_file import write_to_MargeFile

def change_date_format(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%d-%m-%Y')
        return date_obj.strftime('%Y-%m-%d')
    except Exception:
        return date_str

async def close_popup_if_any(page):
    try:
        popup = await page.query_selector("div.swal2-container.swal2-center.swal2-backdrop-show")
        if popup:
            print("⚠️ Popup detected! Closing it...")
            btn = await popup.query_selector("button.swal2-confirm")
            if btn:
                await btn.click()
                await page.wait_for_timeout(2000)
            else:
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(2000)
    except Exception as e:
        print("❌ Popup close error:", e)

def parse_project_data(html_part1, html_part2):
    soup1 = BeautifulSoup(html_part1, 'html.parser')
    soup2 = BeautifulSoup(html_part2, 'html.parser')

    project_details = {}
    for detail in soup1.select('.details-project'):
        label_tag = detail.find('label')
        if label_tag:
            label = label_tag.get_text(strip=True).replace(':', '')
            if label == "Registration Certificate":
                a_tag = detail.find('a', href=True)
                project_details[label] = a_tag['href'] if a_tag else ""
            else:
                value_tag = detail.find('strong')
                project_details[label] = value_tag.get_text(strip=True) if value_tag else ""

    registration_date = ""
    for span in soup1.select('span'):
        if span.get_text(strip=True).count('-') == 2:
            registration_date = span.get_text(strip=True)
            break

    def extract_from_part2(label_text):
        label = soup2.find('label', string=lambda x: x and label_text in x)
        if label:
            strong = label.find_next('strong')
            return strong.get_text(strip=True) if strong else ""
        return ""

    project_name = project_details.get("Project Name", "")
    project_location = project_details.get("Project Location", "")
    project_type = project_details.get("Project Type", "")
    rera_number = project_details.get("RERA Regd. No.", "")

    company_name = extract_from_part2("Company Name")
    entity_type = extract_from_part2("Entity")
    registered_office_address = extract_from_part2("Registered Office Address")
    acknowledgementNumber = extract_from_part2("Registration No.")

    data = {
        'projectCin': None,
        'promoterCin': None,
        'projectName': project_name.strip().replace('\n', ' ').title(),
        'promoterName': company_name.strip().replace('\n', ' ').title(),
        'acknowledgementNumber': acknowledgementNumber,
        'projectRegistrationNo': rera_number,
        'reraRegistrationDate': change_date_format(registration_date),
        'projectProposeCompletionDate': None,
        'projectStatus': None,
        'projectType': project_type,
        'promoterType': entity_type,
        'projectStateName': "Odisha",
        'projectPinCode': None,
        'projectDistrictName': None,
        'projectVillageName': None,
        'projectAddress': project_location.replace('\n', ' ').title().strip(),
        'totalLandArea': None,
        'promotersAddress': registered_office_address.replace('\n', ' ').replace(',,,,,', ',').title().strip(),
        'landownerTypes': None,
        'promoterPinCode': None,
        'longitude': None,
        'latitude': None,
        'viewLink': "https://rera.odisha.gov.in/projects/project-list"
    }
    return data

async def rera_Odisha():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        MAIN_URL = 'https://rera.odisha.gov.in/projects/project-list'

        # Retry logic for page.goto
        for attempt in range(3):
            try:
                await page.goto(MAIN_URL, timeout=60000, wait_until="networkidle")
                break
            except Exception as e:
                print(f"Attempt {attempt+1} to open main page failed: {e}")
                if attempt == 2:
                    await browser.close()
                    return
                await asyncio.sleep(5)

        await page.wait_for_selector('.card', timeout=30000)

        page_num = 1
        while True:
            print(f"🔄 Loading page {page_num}")
            await page.wait_for_timeout(5000)

            # Dynamic projects count
            projects = await page.query_selector_all("a:has-text('View Details')")
            projects_count = len(projects)
            print(f"📝 Found {projects_count} projects on page {page_num}")

            for i in range(projects_count):
                print(f"➡️ Processing project {i+1} on page {page_num}")
                try:
                    xpath = f"(//a[contains(text(),'View Details')])[{i+1}]"
                    await page.wait_for_selector(xpath, timeout=30000)

                    await close_popup_if_any(page)

                    await page.locator(xpath).click()
                    await page.wait_for_timeout(5000)

                    html_part1 = await page.content()

                    try:
                        part2_tab = await page.wait_for_selector("#ngb-nav-1", timeout=10000)
                        await part2_tab.click()
                        await page.wait_for_timeout(4000)
                        html_part2 = await page.content()
                    except Exception:
                        print("⚠️ Part 2 tab not found or timeout, using empty content")
                        html_part2 = ""

                    data = parse_project_data(html_part1, html_part2)
                    print(data)
                    # write_to_MargeFile(data,"odisha")

                    # Go back to main list page
                    # Retry for page.goto
                    for attempt in range(3):
                        try:
                            await page.goto(MAIN_URL, timeout=60000, wait_until="networkidle")
                            break
                        except Exception as e:
                            print(f"Attempt {attempt+1} to reload main page failed: {e}")
                            if attempt == 2:
                                raise
                            await asyncio.sleep(5)

                    await page.wait_for_selector('.card', timeout=30000)
                    await page.wait_for_timeout(3000)

                except Exception as e:
                    print(f"❌ Error on project {i+1} page {page_num}: {e}")

            try:
                next_btn = await page.wait_for_selector("//button[@aria-label='Next']", timeout=15000)
                disabled = await next_btn.get_attribute("disabled")
                if disabled:
                    print("🔚 No more pages, exiting.")
                    break

                await next_btn.scroll_into_view_if_needed()
                await close_popup_if_any(page)
                await next_btn.click()
                page_num += 1
                await page.wait_for_selector('.card', timeout=30000)
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"❌ Could not click Next button or no more pages: {e}")
                break

        await browser.close()
        print("✅ Browser closed.")

# if __name__ == "__main__":
#     asyncio.run(rera_Odisha())
# rera_Odisha()
