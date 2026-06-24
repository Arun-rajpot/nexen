
import pdfplumber
import re
from pathlib import Path

def flatten_tables(tables):
    """
    FIX: pdfplumber sometimes returns nested tables like:
    [[table1], [table2], [table3]]
    This function converts it to: [table1, table2, table3]
    """
    flat = []
    for t in tables:
        # nested → explode
        if t and isinstance(t[0], list) and isinstance(t[0][0], list):
            for inner in t:
                if isinstance(inner, list):
                    flat.append(inner)
        else:
            flat.append(t)
    return flat

def clean_header_row(table):
    """
    FIX: sometimes first row is ['', '', '', '', '']
    Remove it and return cleaned table.
    """
    if table and all((c is None or str(c).strip() == "") for c in table[0]):
        return table[1:]
    return table


def extract_bii(pdf_path):
    pdf = pdfplumber.open(pdf_path)
    """Extract B(ii) Particles of Change"""

    bii_rows = []
    header = None
    inside_bii = False

    for page_num, page in enumerate(pdf.pages, 1):
        lines = (page.extract_text() or "").split("\n")

        # detect B(ii) start
        if not inside_bii:
            if any("B (ii)" in line for line in lines):
                inside_bii = True
                print(f"B(ii) Started on page {page_num}")

        if not inside_bii:
            continue

        tables = page.extract_tables({
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "intersection_tolerance": 5
        })

        tables = flatten_tables(tables)

        for table in tables:
            table = clean_header_row(table)
            if not table or len(table) < 2:
                continue

            first_row_text = " ".join([str(x or "") for x in table[0]]).upper()

            # ❌ SKIP NON B(ii) TABLES
            if any(x in first_row_text for x in [
                "TYPE OF MEETING",
                "DATE OF MEETING",
                "% OF TOTAL SHAREHOLDING",
                "ATTENDANCE"
            ]):
                continue

            # detect correct B(ii) header
            if ("DESIGNATION AT THE" in first_row_text
                and "CHANGE" in first_row_text):
                header = [str(c).strip().replace("\n", " ") for c in table[0]]
                rows = table[1:]
            else:
                if header is None:
                    continue
                rows = table

            for row in rows:
                # Skip garbage rows
                if all((c is None or str(c).strip() == "") for c in row):
                    continue

                row_dict = {}
                for i, cell in enumerate(row):
                    if i < len(header):
                        row_dict[header[i]] = str(cell).strip().replace("\n", " ") if cell else ""

                # Skip wrong tables capturing "AGM" rows
                if len(row_dict.get("Name", "")) < 3:
                    continue

                # HARD FILTER → stop "Meeting" table rows
                if row_dict.get("Name", "").upper() in ["TYPE OF MEETING", "ANNUAL GENERAL MEETING"]:
                    continue

                bii_rows.append(row_dict)

        # stop when Meetings section starts
        if any("MEETINGS OF MEMBERS" in line.upper() for line in lines):
            print("B(ii) ended.")
            break

    return bii_rows
