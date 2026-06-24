import pdfplumber
import pandas as pd


def extract_specific_table(pdf_path):

    if "MGT7A" in pdf_path.upper() or "MGT-7A" in pdf_path.upper():

        start_heading = "III PARTICULARS OF ASSOCIATE COMPANIES (INCLUDING JOINT VENTURES)"
    else:
      start_heading = "III PARTICULARS OF HOLDING, SUBSIDIARY AND ASSOCIATE COMPANIES (INCLUDING JOINT VENTURES)"

    if "MGT7A" in pdf_path.upper() or "MGT-7A" in pdf_path.upper():

        end_heading = "IV SHARE CAPITAL, DEBENTURES AND OTHER SECURITIES OF THE COMPANY"
    else:
        end_heading = "IV SHARE CAPITAL, DEBENTURES AND OTHER SECURITIES OF THE COMPANY"

    table_data = []
    headers = None
    in_section = False
    target_table_identified = False

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""

            if not in_section and start_heading in text:
                in_section = True

            if in_section:
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue

                    if headers is None and any('CIN' in str(cell) for row in table for cell in row):
                        headers = table[0]
                        table_data.append(headers)
                        table_data.extend(table[1:])
                        target_table_identified = True

                    elif target_table_identified and headers is not None:
                        if table and (table[0][0].strip().isdigit() or not table[0][0].strip()):
                            table_data.extend(table)

            if end_heading in text:
                break

    if not table_data:
        return None

    df = pd.DataFrame(table_data[1:], columns=table_data[0])

    # Clean headers
    df.columns = [col.replace("\n", " ").replace("\r", " ").strip() for col in df.columns]

    # Clean cell values — UPDATED
    df = df.map(lambda x: x.replace("\n", " ").replace("\r", " ").strip() if isinstance(x, str) else x)

    # FIX COLUMN MAPPING
    fixed_map = {
        "S. No.": "s_no",
        "CIN /FCRN": "cin",
        "Other registration number": "other_registration_no",
        "Name of the company": "company_name",
        "Holding/ Subsidiary/Associate/ Joint Venture": "relation_type",
        "% of shares held": "shareholding_percent"
    }

    final_rows = []
    for _, row in df.iterrows():
        clean_row = {}
        for orig_col, value in row.items():
            col_cleaned = orig_col.replace(" ", "").replace("\n", "").lower()

            match_found = None
            for k, v in fixed_map.items():
                if k.replace(" ", "").lower() in col_cleaned:
                    match_found = v
                    break

            if match_found:
                clean_row[match_found] = value
        final_rows.append(clean_row)

    return final_rows


# ------------------ RUN ------------------
# if __name__ == "__main__":
#     pdf = r"D:\MGT-7\MGT-7\MGT-7A\MGT-7A_Form MGT7A_05_09_2025.pdf"
#     data = extract_specific_table(pdf)
#     print(data)
