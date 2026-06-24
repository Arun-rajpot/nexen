import pdfplumber
import re
from pathlib import Path
import pandas as pd


def extract_bi_directors_clean_final(pdf_path):
    pdf_path = Path(pdf_path)
    # print(f"\n{'=' * 110}")
    # print(f"EXTRACTING B(i) → {pdf_path.name}")
    # print('=' * 110)

    directors = []
    header = None
    in_bi_section = False

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            lines = text.split('\n')

            # START B(i)
            if not in_bi_section:
                if any("B (i)" in line for line in lines):
                    in_bi_section = True
                    print(f"B(i) Section STARTED → Page {page_num}")

            if not in_bi_section:
                continue

            # FIX-1: Safe table extraction (no merging)
            tables = page.extract_tables({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "intersection_tolerance": 5
            })

            for table in tables:
                if not table or len(table) < 2:
                    continue

                # ⭐ FIX-1: Remove any blank first row BEFORE header detection
                if table and all((c is None or str(c).strip() == "") for c in table[0]):
                    table = table[1:]

                # Now recalc first_row
                first_row = " ".join([str(c) if c else "" for c in table[0]]).upper()

                # Skip NON B(i) tables
                if any(skip in first_row for skip in [
                    "CATEGORY",
                    "BEGINNING OF THE YEAR",
                    "TYPE OF MEETING",
                    "DATE OF MEETING",
                    "S.NO",
                    "ATTENDANCE"
                ]):
                    continue

                # ⭐ HEADER DETECT
                if ("NAME" in first_row and "NUMBER OF EQUITY" in first_row and (
                        "DIN" in first_row or "PAN" in first_row)):
                    header = [str(c).strip().replace("\n", " ") for c in table[0]]
                    rows_to_use = table[1:]
                else:
                    if header is None:
                        continue
                    rows_to_use = table

                for row in rows_to_use:
                    if len(row) < 3:
                        continue

                    # ---------- FIX-1: Detect B(ii) table header ----------
                    header_upper = " ".join([str(h).upper() for h in header])

                    # This header ONLY exists in B(ii)
                    if ("DESIGNATION AT THE" in header_upper and
                            "CHANGE IN DESIGNATION" in header_upper):
                        print("⚠️ Detected B(ii) header → Skipping entire table")
                        skip_entire_table = True
                        break  # skip whole table → do NOT proceed rows

                    # If this flag was set for previous table → skip rows
                    if "skip_entire_table" in locals() and skip_entire_table:
                        continue

                    # ---------- FIX-2: Skip any B(ii) type rows ----------
                    full_text = " ".join([str(c).upper() for c in row if c])

                    if any(x in full_text for x in [
                        "PARTICULARS OF CHAN",
                        "CHANGE IN DIRECTOR",
                        "CHANGE IN DESIGNATION",
                        "APPOINTMENT",
                        "CESSATION",
                        "RE-APPOINT"
                    ]):
                        continue

                    # ---------- MAP ROWS ----------
                    row_dict = {}
                    for i, cell in enumerate(row):
                        if i < len(header):
                            row_dict[header[i]] = str(cell).strip().replace("\n", " ") if cell else ""

                    name = row_dict.get("Name", "").strip()
                    if not name or len(name) < 3:
                        continue

                    din = row_dict.get("DIN/PAN", "").strip()
                    designation = row_dict.get("Designation", "").strip() or "Director"

                    # Extract Shares
                    shares_raw = row_dict.get("Number of equity shares held", "")
                    shares = re.search(r"\d+", shares_raw).group(0) if shares_raw and re.search(r"\d+",
                                                                                                shares_raw) else "0"

                    # Extract Cessation Date
                    cessation_match = re.search(r"\d{2}/\d{2}/\d{4}", full_text)
                    cessation = cessation_match.group(0) if cessation_match else ""

                    directors.append({
                        "Name": name,
                        "DIN/PAN": din,
                        "Designation": designation,
                        "Shares": shares,
                        "Cessation": cessation
                    })

            # STOP on B(ii)
            if any("B (ii)" in line for line in lines):
                print(f"B(ii) SECTION STARTED → STOPPING at Page {page_num}")
                break

    # print(f"FINAL CLEAN DIRECTORS/KMP → {len(directors)} rows")
    return directors