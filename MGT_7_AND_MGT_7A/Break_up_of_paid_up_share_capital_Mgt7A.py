# --------------------------------------------------------------
#  MGT-7 → (d) Break-up of paid-up share capital → Key-Value Print
# --------------------------------------------------------------
import fitz  # PyMuPDF
import re
from pathlib import Path
import os

# ============================= CONFIG =============================
# PDF_FOLDER = r"D:\MGT-7\MGT-2025"  # CHANGE THIS PATH
# =================================================================

# Fixed header from all MGT-7 forms
HEADERS = [
    "Total",
    "Total Nominal Amount",
    "Total Paid-up amount",
    "Total premium"
]


def find_section_pages(pdf_path: str):
    """Return (start_page, end_page) 0-based"""
    doc = fitz.open(pdf_path)
    start = end = None
    for pno in range(len(doc)):
        text = doc[pno].get_text()
        if "Break-up of paid-up share capital" in text and start is None:
            start = pno
        if "ii Details of shares" in text and start is not None:
            end = pno
            break
    doc.close()
    return start, end


def extract_tables_from_pages(pdf_path: str, start_page: int, end_page: int):
    """Extract all tables using PyMuPDF's built-in table detection"""
    doc = fitz.open(pdf_path)
    all_tables = []

    for pno in range(start_page, end_page + 1):
        page = doc.load_page(pno)
        tables = page.find_tables()

        for tab in tables:
            # print(tab.extract())
            df = tab.extract()
            if df and len(df) > 0 and len(df[0]) >= 5:
                all_tables.append(df)
    doc.close()
    return all_tables


def clean_and_merge_tables(tables):
    """Merge all tables, remove duplicate headers, clean numbers"""
    rows = []
    seen_header = False

    for tab in tables:
        if not tab or len(tab) == 0:
            continue
        first_row = [str(x).strip() for x in tab[0][:5]]

        if (first_row and "Classes of non-convertible debentures" in first_row[0]):
            # ❌ Skip entire table
            break

        for row in tab:
            if len(row) < 5:
                continue
            # Clean cells
            cleaned = [str(cell).strip() for cell in row[:5]]

            first = cleaned[0]

            # Skip header row
            if (first == "Particulars" or first == "Number of") and "Total Nominal" in cleaned[1]:
                seen_header = True
                continue

            # Skip empty or junk rows
            if not first or first.lower() in ["nan", "none", ""]:
                continue

            # Clean numbers: remove commas, handle empty
            values = []
            for v in cleaned[1:]:
                v = v.replace("\n", "").replace(",", "").strip()
                if not v or v.lower() in ["nan", "none", ""]:
                    v = v
                values.append(v)

            rows.append((first, values))

    return rows


def build_key_value(rows):
    """Build nested dict with proper indentation for sub-items"""
    result = []
    current_main = None
    sub_items = []

    indent_pattern = re.compile(r'^\s*[ivx]+\s+')

    for title, values in rows:
        # print(title,"===",values)
        # Detect main sections
        if re.match(r'^\(?[ivx]+\)?\s+Equity|Preference', title, re.I):
            if current_main:
                result.append({current_main: sub_items})
            current_main = title
            sub_items = []
        # Detect sub-items under Increase/Decrease
        elif any(x in title for x in
                 ["Public Issues", "Rights issue", "Bonus", "ESOPs", "Others, specify", "Buy-back", "forfeited"]):
            sub_items.append({title: dict(zip(HEADERS, values))})
        else:
            # Normal row
            if current_main:
                sub_items.append({title: dict(zip(HEADERS, values))})

    if current_main:
        result.append({current_main: sub_items})

    return result


# ============================= MAIN =============================
def process_mgt7A(pdf_path: str):
    # print("\n" + "=" * 80)
    # print(f"PROCESSING: {Path(pdf_path).name}")
    # print("=" * 80)

    start_page, end_page = find_section_pages(pdf_path)
    if start_page is None:
        print("Section not found!")
        return
    if end_page is None:
        end_page = start_page

    # Extract ISIN
    doc = fitz.open(pdf_path)
    isin = "Not mentioned"
    for pno in range(start_page, end_page + 1):
        text = doc[pno].get_text()
        m = re.search(r'\bIN[A-Z0-9]{10}\b', text)
        if m:
            isin = m.group(0)
            break
    doc.close()

    # print(f"ISIN: {isin}")

    # Extract tables
    print(start_page, end_page)
    tables = extract_tables_from_pages(pdf_path, start_page, end_page)
    if not tables:
        print("No tables detected in section.")
        return

    # print(f"Found {len(tables)} table(s) in section.")

    # Clean & merge
    rows = clean_and_merge_tables(tables)
    if not rows:
        print("No valid data rows found.")
        return

    # Build key-value
    data = build_key_value(rows)
    return data
#
# # # ------------------ RUN ------------------
# if __name__ == "__main__":
#     pdf = r"D:\MGT7A\MGT7A Form\MGT7A Form\MGT-7A_Form MGT7A_27_10_2025.pdf"
#     data = process_mgt7A(pdf)
#     print(data)
