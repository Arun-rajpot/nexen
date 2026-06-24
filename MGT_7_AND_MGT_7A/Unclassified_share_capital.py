import fitz
import re
import json


def extract_unclassified_share_capital(pdf_path):
    # -------------------------------------------------
    # 1. Load full PDF text
    # -------------------------------------------------
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        text = page.get_text("text")
        text = re.sub(r'Page\s*\d+\s*(of|/)\s*\d+', '', text, flags=re.IGNORECASE)
        full_text += text + "\n"
    doc.close()

    # -------------------------------------------------
    # 2. Find block: (c) Unclassified → (d) Break-up
    # -------------------------------------------------
    start_pat = re.compile(r'\(c\)\s+Unclassified\s+share\s+capital', re.IGNORECASE)
    end_pat   = re.compile(r'\(d\)\s+Break-up\s+of\s+paid-up\s+share\s+capital', re.IGNORECASE)

    start = start_pat.search(full_text)
    end   = end_pat.search(full_text)

    if not start or not end:
        raise ValueError("Could not find Unclassified Share Capital block")

    block = full_text[start.end():end.start()]
    block = re.sub(r'\s+', ' ', block).strip()

    # Remove table header
    block = re.sub(
        r'Particulars\s+Authorised\s+Capital',
        '', block, flags=re.IGNORECASE
    )

    # -------------------------------------------------
    # 3. Extract the only row: Total amount
    # -------------------------------------------------
    # Pattern: "Total amount of unclassified shares" followed by number
    amount_match = re.search(
        r'Total\s+amount\s+of\s+unclassified\s+shares.*?([\d\.]+)',
        block, re.IGNORECASE
    )

    amount = amount_match.group(1) if amount_match else ""

    # -------------------------------------------------
    # 4. Return final structure
    # -------------------------------------------------
    return {
        "Unclassified Share Capital": {
            "Total amount of unclassified shares (in rupees)": amount
        }
    }