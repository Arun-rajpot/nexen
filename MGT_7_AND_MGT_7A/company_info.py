import json
import re
import pdfplumber
import os

def clean_cell(val):
    if isinstance(val, str):
        return val.strip()
    return val

def extract_company_info(file_path):
    """
    Extracts company information from an MGT-7 PDF form.

    This function processes the given PDF file path, extracts text lines and tables,
    parses key company details like CIN, financial year, PAN, email, etc.

    Args:
        file_path (str): The full path to the MGT-7 PDF file.

    Returns:
        dict: A dictionary containing 'company_info' with parsed company details.

    Raises:
        FileNotFoundError: If the file_path does not exist.
        ValueError: If the file is not a valid PDF or extraction fails.
    """
    try:
        with pdfplumber.open(file_path) as doc:
            all_lines = []
            pages = doc.pages

            # Extract all lines of text from all pages
            for page in pages:
                lines = page.extract_text_lines()
                for line in lines:
                    all_lines.append(line['text'].strip())

            # Company info extraction
            company_info = {}
            for i, line in enumerate(all_lines):
                line = line.strip()

                # # CIN (value before label)
                # if '*Corporate Identity Number (CIN)' in line:
                #     k = i - 1
                #     while k >= 0 and k >= i - 5:
                #         if re.match(r'[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}', all_lines[k]):
                #             company_info['cin'] = all_lines[k]
                #             break
                #         k -= 1
                if 'Corporate Identity Number (CIN)' in line:

                    # 1️⃣ Try same line (right side box case)
                    m_same = re.search(r'\b[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b', line)
                    if m_same:
                        company_info['cin'] = m_same.group()
                        continue

                    # 2️⃣ Otherwise check previous lines (old layout case)
                    k = i - 1
                    while k >= 0 and k >= i - 5:
                        prev = all_lines[k].strip()
                        prev_clean = re.sub(r'^[^A-Z0-9]*', '', prev)

                        m = re.search(r'\b[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b', prev_clean)
                        if m:
                            company_info['cin'] = m.group()
                            break
                        k -= 1
                # Financial Year Start (value on same line or after)
                elif '*Financial year for which the annual return is being filed (From date) (DD/MM/YYYY)' in line:
                    match = re.search(r'(\d{2}/\d{2}/\d{4})$', line)
                    if match:
                        company_info['Financial Year Start Date'] = match.group(1)
                    else:
                        j = i + 1
                        while j < len(all_lines) and j <= i + 5:
                            match = re.search(r'(\d{2}/\d{2}/\d{4})', all_lines[j])
                            if match:
                                company_info['Financial Year Start Date'] = match.group(1)
                                break
                            j += 1

                # Financial Year End (value on same line or after)
                elif '*Financial year for which the annual return is being filed (To date) (DD/MM/YYYY)' in line:
                    match = re.search(r'(\d{2}/\d{2}/\d{4})$', line)
                    if match:
                        company_info['Financial Year End Date'] = match.group(1)
                    else:
                        j = i + 1
                        while j < len(all_lines) and j <= i + 5:
                            match = re.search(r'(\d{2}/\d{2}/\d{4})', all_lines[j])
                            if match:
                                company_info['Financial Year End Date'] = match.group(1)
                                break
                            j += 1

                # PAN (value before or after label, handling masked format)
                elif '*Permanent Account Number (PAN) of the company' in line:
                    k = i - 1
                    while k >= 0 and k >= i - 5:
                        if re.match(r'[A-Z]{2}\*{4,}\d[A-Z]', all_lines[k]):  # Matches AA*****7N
                            company_info['pan'] = all_lines[k]
                            break
                        k -= 1
                    if 'pan' not in company_info:
                        j = i + 1
                        while j < len(all_lines) and j <= i + 5:
                            if re.match(r'[A-Z]{2}\*{4,}\d[A-Z]', all_lines[j]):
                                company_info['pan'] = all_lines[j]
                                break
                            j += 1


                elif '*e-mail ID of the company' in line:
                    print(line)

                    # ✅ Universal email regex (supports .IN / .CO.IN / capital domains / mixed case)
                    email_pattern = re.compile(
                        r"[\w\*\.\-]+@[\w\.\-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?",
                        re.IGNORECASE
                    )

                    # 🔹 Check previous 5 lines for possible email
                    for k in range(i - 1, max(i - 6, -1), -1):
                        candidate = all_lines[k].strip()
                        match = email_pattern.search(candidate)
                        if match:
                            company_info['email'] = match.group(0)
                            break

                    # 🔹 If not found, check next 5 lines (forward scan)
                    if 'email' not in company_info:
                        combined = ""
                        for j in range(i + 1, min(i + 6, len(all_lines))):
                            part = all_lines[j].strip()
                            if not part:
                                continue
                            combined += part.replace(" ", "")
                            match = email_pattern.search(combined)
                            if match:
                                company_info['email'] = match.group(0)
                                break

                    # 🔹 Handle multi-line broken emails (like "mphasis.c" + "om")
                    if 'email' not in company_info:
                        merged_block = ''.join(all_lines[i + 1:i + 6]).replace(" ", "").replace("\n", "")
                        match = email_pattern.search(merged_block)
                        if match:
                            company_info['email'] = match.group(0)

                    if 'email' not in company_info:
                        email_pattern = re.compile(
                            r"(?:[\w\*\.\-]+@[\w\*\.\-]+|\*+)[\.\-]*[a-zA-Z0-9\-]*\.(?:[a-zA-Z]{2,}|IN|CO\.IN|ORG\.IN|MLAB\.IN)",
                            re.IGNORECASE
                        )
                        merged_block = ''.join(all_lines[i + 1:i + 6]).replace(" ", "").replace("\n", "")
                        match = email_pattern.search(merged_block)
                        if match:
                            company_info['email'] = match.group(0)

                # Phone (value before or after label, handling masked format)
                # elif '*Telephone number with STD code' in line:
                #     k = i - 1
                #     while k >= 0 and k >= i - 5:
                #         candidate = all_lines[k]
                #         if re.match(r'\d{2}\*{4,}\d{2}', candidate):  # Matches 04*****41
                #             company_info['phone'] = candidate
                #             break
                #         k -= 1
                #     if 'phone' not in company_info:
                #         j = i + 1
                #         while j < len(all_lines) and j <= i + 5:
                #             candidate = all_lines[j]
                #             if re.match(r'\d{2}\*{4,}\d{2}', candidate):
                #                 company_info['phone'] = candidate
                #                 break
                #             j += 1

                elif '*Telephone number with STD code' in line:

                    k = i - 1

                    while k >= 0 and k >= i - 5:

                        candidate = all_lines[k].strip()

                        # ✅ Match +91********49 or 04*****41 etc.

                        if re.match(r'(\+\d{1,3}\*+\d{1,3}|\+\d{1,3}\*+\d{2,5}|\d{2}\*{4,}\d{2})$', candidate):
                            company_info['phone'] = candidate

                            break

                        k -= 1

                    if 'phone' not in company_info:

                        j = i + 1

                        while j < len(all_lines) and j <= i + 5:

                            candidate = all_lines[j].strip()

                            if re.match(r'(\+\d{1,3}\*+\d{1,3}|\+\d{1,3}\*+\d{2,5}|\d{2}\*{4,}\d{2})$', candidate):
                                company_info['phone'] = candidate

                                break

                            j += 1
                # Website (value after 'Website' label, excluding dates or page numbers)
                elif 'Website' in line:
                    j = i + 1
                    while j < len(all_lines) and j <= i + 5:
                        candidate = all_lines[j]
                        if candidate and not re.match(r'\d{2}/\d{2}/\d{4}', candidate) and not candidate.startswith('Page ') and ('http' in candidate or '.' in candidate and not candidate.isdigit()):
                            company_info['website'] = candidate
                            break
                        j += 1
                    if 'website' not in company_info:
                        company_info['website'] = ''

                # Date of Incorporation (value after label)
                elif '*Date of Incorporation (DD/MM/YYYY)' in line:
                    j = i + 1
                    while j < len(all_lines) and j <= i + 5:
                        match = re.search(r'(\d{2}/\d{2}/\d{4})', all_lines[j])
                        if match:
                            company_info['incorporation_date'] = match.group(0)
                            break
                        j += 1

                # Class of Company (value after label and options)
                elif '*Class of Company (as on the financial year end date)' in line:
                    j = i + 1
                    skipped_options = False
                    while j < len(all_lines) and j <= i + 10:
                        if not skipped_options and '/' in all_lines[j]:
                            skipped_options = True
                            j += 1
                            continue
                        candidate = all_lines[j]
                        if candidate in ['Private company', 'Public company', 'One Person Company']:
                            company_info['class'] = candidate
                            break
                        j += 1

                # Category of Company (value after label and options)
                elif '*Category of the Company (as on the financial year end date)' in line:
                    j = i + 1
                    skipped_options = False
                    while j < len(all_lines) and j <= i + 10:
                        if not skipped_options and '/' in all_lines[j]:
                            skipped_options = True
                            j += 1
                            continue
                        candidate = all_lines[j]
                        if candidate in ['Company limited by shares', 'Company limited by guarantee', 'Unlimited company']:
                            company_info['category'] = candidate
                            break
                        j += 1

                # Sub-category (value on same line or after label and options)
                elif '*Sub-category of the Company (as on the financial year end date)' in line:
                    match = re.search(r'\*Sub-category of the Company \(as on the financial year end date\) (.*)', line)
                    if match and match.group(1):
                        company_info['sub_category'] = match.group(1).strip()
                    else:
                        j = i + 1
                        skipped_options = False
                        while j < len(all_lines) and j <= i + 10:
                            if not skipped_options and ('/' in all_lines[j] or 'Guarantee and association company' in all_lines[j]):
                                skipped_options = True
                                j += 1
                                continue
                            candidate = all_lines[j]
                            if 'company' in candidate.lower() and '/' not in candidate:
                                company_info['sub_category'] = candidate
                                break
                            j += 1

                # Listed on Stock Exchange
                elif 'Whether shares listed on recognized Stock Exchange(s)' in line:
                    company_info['listed'] = 'No'
                    j = i + 1
                    while j < len(all_lines) and j <= i + 20:
                        if re.match(r'^\d+$', all_lines[j]):
                            company_info['listed'] = 'Yes'
                            break
                        if 'viii Number of Registrar and Transfer Agent' in all_lines[j]:
                            break
                        j += 1

                # AGM Date (value after label)
                elif 'date of AGM (DD/MM/YYYY)' in line:
                    j = i + 1
                    while j < len(all_lines) and j <= i + 5:
                        match = re.search(r'(\d{2}/\d{2}/\d{4})', all_lines[j])
                        if match:
                            company_info['agm_date'] = match.group(0)
                            break
                        j += 1

            # Name and Address from first page table
            if pages:
                page = pages[0]
                tables = page.extract_tables()
                for table in tables:
                    normalized = [[clean_cell(cell) for cell in row] for row in table]
                    for row in normalized:
                        if len(row) >= 3:
                            if 'Name of the company' in row[0]:
                                company_info['name'] = (row[1] or row[2]).replace('\n', ' ')
                            if 'Registered office address' in row[0]:
                                company_info['address'] = (row[1] or row[2]).replace('\n', ' ')

            return {"company_info": company_info}

    except FileNotFoundError:
        raise FileNotFoundError(f"PDF file not found at: {file_path}")
    except Exception as e:
        raise ValueError(f"Error processing PDF: {str(e)}")

# import os
# folder_path = r"D:\MGT-7\MGT-2025"
# for filename in os.listdir(folder_path):
#     if filename.lower().endswith('.pdf'):
#         input_pdf_path = os.path.join(folder_path, filename)
#         data = extract_company_info(input_pdf_path)
#         print(data)
#     print("===========================================================")