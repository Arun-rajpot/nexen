# import pdfplumber
# import re
#
# def extract_business_activities_table(file_path):
#     """
#     Extracts the table following 'II PRINCIPAL BUSINESS ACTIVITIES OF THE COMPANY' from the page where it appears in an MGT-7 PDF form.
#
#     Args:
#         file_path (str): The full path to the MGT-7 PDF file.
#
#     Returns:
#         list: A list of lists representing the table rows.
#     """
#     table = []
#     try:
#         with pdfplumber.open(file_path) as doc:
#             for page in doc.pages:
#                 text = page.extract_text()
#                 if "II PRINCIPAL BUSINESS ACTIVITIES OF THE COMPANY" in text:
#                     # table.append(["--- Start of Section ---", "II PRINCIPAL BUSINESS ACTIVITIES OF THE COMPANY"])
#                     # Extract tables from the page
#                     tables = page.extract_tables()
#                     for t in tables:
#                         cleaned = [[cell.strip() if cell else "" for cell in row if cell] for row in t if
#                                    any(cell for cell in row)]
#                         if cleaned and any(
#                                 "S. No." in str(row) or any(str(cell).isdigit() for cell in row) for row in cleaned):
#                             table.extend(cleaned)
#                             # table.append(["--- End of Section ---", "End of Table"])
#                             return table
#                     # Fallback: If no table is found, use text lines after the heading
#                     lines = [line.strip() for line in text.split('\n') if line.strip()]
#                     start_idx = next((i for i, line in enumerate(lines) if
#                                       "II PRINCIPAL BUSINESS ACTIVITIES OF THE COMPANY" in line), -1)
#                     if start_idx != -1:
#                         section_lines = lines[start_idx + 1:]
#                         current_row = []
#                         for line in section_lines:
#                             if re.match(r'^\s*\d+\s+[A-Z]\s+', line) or any(num.isdigit() for num in line.split()):
#                                 if current_row:
#                                     table.append(current_row)
#                                 current_row = [item for item in line.split() if item]
#                             elif current_row and line.strip():
#                                 current_row.append(line.strip())
#                         if current_row:
#                             table.append(current_row)
#                             # table.append(["--- End of Section ---", "End of Table"])
#                             return table
#                     return table  # Return empty or partial table if nothing found
#         return table
#     except Exception as e:
#         raise ValueError(f"Error processing PDF: {str(e)}")
#
#
# def table_to_dict(table):
#     if not table or len(table) < 2:
#         return []
#
#     headers = [h.replace("\n", " ").strip() for h in table[0]]  # clean headers
#     rows = table[1:]
#
#     result = []
#     for row in rows:
#         clean_row = [c.replace("\n", " ").strip() for c in row]
#         result.append(dict(zip(headers, clean_row)))
#
#     return result
#
#
# def extrect_PRINCIPAL_BUSINESS_ACTIVITIES(input_pdf_path):
#     try:
#         table = extract_business_activities_table(input_pdf_path)
#         if table and len(table) > 2:  # Ensure there’s data beyond headers and indicators
#             result = table_to_dict(table)
#             return result
#         else:
#             print(f"No table found in {input_pdf_path} for the specified range.")
#             return {}
#     except ValueError as e:
#         print(f"Error processing {input_pdf_path}: {str(e)}")
#         return {}
import pdfplumber
import re

START_HEADING = "II PRINCIPAL BUSINESS ACTIVITIES OF THE COMPANY"
END_HEADING = "III PARTICULARS OF ASSOCIATE COMPANIES"

EXPECTED_HEADERS = [
    "s. no", "main activity", "business activity", "% of turnover"
]


def extract_business_activities_table(file_path):
    table = []
    try:
        with pdfplumber.open(file_path) as doc:
            pages = doc.pages

            start_page = None
            end_page = None

            # Step 1: find start and end pages
            for i, page in enumerate(pages):
                text = (page.extract_text() or "").lower()

                if START_HEADING.lower() in text and start_page is None:
                    start_page = i

                if END_HEADING.lower() in text and start_page is not None:
                    end_page = i
                    break

            if start_page is None:
                print("Start heading not found")
                return []

            if end_page is None:
                end_page = start_page + 3  # fallback safety

            # Step 2: extract tables between start and end
            for i in range(start_page, min(end_page + 1, len(pages))):
                page = pages[i]
                tables = page.extract_tables()

                for t in tables:
                    cleaned = [
                        [cell.strip() if cell else "" for cell in row]
                        for row in t if any(cell for cell in row)
                    ]

                    header_line = " ".join(cleaned[0]).lower() if cleaned else ""

                    if any(h in header_line for h in EXPECTED_HEADERS):
                        table.extend(cleaned)

        return table

    except Exception as e:
        raise ValueError(f"Error processing PDF: {str(e)}")


def table_to_dict(table):
    if not table or len(table) < 2:
        return []

    headers = [h.replace("\n", " ").strip() for h in table[0]]
    rows = table[1:]

    result = []
    for row in rows:
        clean_row = [c.replace("\n", " ").strip() for c in row]
        result.append(dict(zip(headers, clean_row)))

    return result


def extrect_PRINCIPAL_BUSINESS_ACTIVITIES(input_pdf_path):
    table = extract_business_activities_table(input_pdf_path)

    if not table:
        print(f"No table found in {input_pdf_path} for the specified range.")
        return {}

    return table_to_dict(table)


if __name__ == "__main__":
    pdf = r"C:\Users\PC\Downloads\mgt\MGT7_2025.pdf"
    data = extrect_PRINCIPAL_BUSINESS_ACTIVITIES(pdf)
    print(data)