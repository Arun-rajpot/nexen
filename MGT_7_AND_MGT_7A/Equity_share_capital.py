
import fitz
import re


def clean_header_line(text):
    text = re.sub(
        r'Particulars\s+Authorised\s+Capital\s+Issued\s+capital\s+Subscribed\s+capital\s+Paid\s+Up\s+capital\s*',
        ' ', text, flags=re.IGNORECASE)
    text = re.sub(
        r'Class\s+of\s+shares\s+Authorised\s+Capital\s+Issued\s+capital\s+Subscribed\s+Capital\s+Paid\s+Up\s+capital\s*',
        ' ', text, flags=re.IGNORECASE)
    return text


def extract_equity_share_capital(pdf_path):
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return {"Equity Share Capital": {"Overall": [], "Number of Classes": "0", "Classes": []}}

    pages_text = []
    for page in doc:
        t = page.get_text("text")
        t = re.sub(r'Page\s*\d+\s*(of|/)\s*\d+', ' ', t, flags=re.IGNORECASE)
        pages_text.append(t)
    full_text = "\n".join(pages_text)

    # Start marker
    start_pat = re.compile(r'\bIV\s+SHARE\s+CAPITAL,\s+DEBENTURES\s+AND\s+OTHER\s+SECURITIES\s+OF\s+THE\s+COMPANY\b', re.IGNORECASE)
    start_m = start_pat.search(full_text)

    if not start_m:
        return {"Equity Share Capital": {"Overall": [], "Number of Classes": "0", "Classes": []}}

    # End marker (Preference section)
    end_pat = re.compile(r'\(b\)\s+Preference\s+share\s+capital', re.IGNORECASE)
    end_m = end_pat.search(full_text, start_m.end())
    end_pos = end_m.start() if end_m else len(full_text)

    table_text = full_text[start_m.end():end_pos]
    table_text = clean_header_line(table_text)

    # Split overall and classes section
    stop_match = re.search(r'\b(Number\s+of\s+classes)\b', table_text, re.IGNORECASE)
    if stop_match:
        overall_text = table_text[:stop_match.start()]
        classes_text = table_text[stop_match.start():]
    else:
        overall_text = table_text
        classes_text = ""

    overall_text = re.sub(r'i\s+SHARE\s+CAPITAL\s*\(a\)\s+Equity\s+share\s+capital\s*', ' ', overall_text, flags=re.IGNORECASE)
    overall_text = re.sub(r'\s+', ' ', overall_text).strip()
    classes_text = re.sub(r'\s+', ' ', classes_text).strip()

    # Regex with comma support (1,00,000)
    num_block_re = re.compile(r'\b([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\b')

    # === OVERALL SECTION ===
    overall_matches = list(num_block_re.finditer(overall_text))
    overall_rows = []

    if overall_matches:
        prev_end = 0
        for m in overall_matches:
            raw_cat = overall_text[prev_end:m.start()].strip()
            raw_cat = re.sub(r'^[\d.\)\-\:]+\s*', '', raw_cat)
            raw_cat = raw_cat.strip(' :,-.')
            raw_cat = re.sub(r'\s+', ' ', raw_cat)
            if not raw_cat:
                raw_cat = "At the beginning of the year"

            auth = m.group(1).replace(',', '').strip() or ""
            issued = m.group(2).replace(',', '').strip() or ""
            sub = m.group(3).replace(',', '').strip() or ""
            paid = m.group(4).replace(',', '').strip() or ""

            overall_rows.append({
                "Particular": raw_cat,
                "Authorised": auth,
                "Issued": issued,
                "Subscribed": sub,
                "Paid Up": paid
            })
            prev_end = m.end()
    else:
        # Default rows if table is blank or no match
        default_particulars = [
            "At the beginning of the year",
            "Issued during the year",
            "Bought back during the year",
            "At the end of the year"
        ]
        for part in default_particulars:
            overall_rows.append({
                "Particular": part,
                "Authorised": "",
                "Issued": "",
                "Subscribed": "",
                "Paid Up": ""
            })

    # === NUMBER OF CLASSES ===
    num_classes_m = re.search(r'Number\s+of\s+classes\s+(\d+)', table_text, re.IGNORECASE)
    num_classes = num_classes_m.group(1) if num_classes_m else ""

    # === CLASSES SECTION ===
    classes_rows = []
    if int(num_classes or "") > 0 and classes_text:
        class_name_pat = re.compile(r'(\d+)\s*([^\d]+?)\s*Number\s+of\s+equity\s+shares', re.IGNORECASE)
        class_name_m = class_name_pat.search(classes_text)
        class_prefix = class_name_m.group(2).strip() if class_name_m else "Equity Shares"

        class_matches = list(num_block_re.finditer(classes_text))
        prev_end = 0

        if class_matches:
            for m in class_matches:
                raw_cat = classes_text[prev_end:m.start()].strip()
                raw_cat = re.sub(r'^[\d.\)\-\:]+\s*', '', raw_cat)
                raw_cat = raw_cat.strip(' :,-.')
                raw_cat = re.sub(r'\s+', ' ', raw_cat)
                if not raw_cat:
                    raw_cat = "Details"

                auth = m.group(1).replace(',', '').strip() or ""
                issued = m.group(2).replace(',', '').strip() or ""
                sub = m.group(3).replace(',', '').strip() or ""
                paid = m.group(4).replace(',', '').strip() or ""

                classes_rows.append({
                    "Class": raw_cat, #f"{class_prefix} - {raw_cat}" if raw_cat != "Details" else class_prefix,
                    "Authorised": auth,
                    "Issued": issued,
                    "Subscribed": sub,
                    "Paid Up": paid
                })
                prev_end = m.end()
        else:
            # Placeholder even if no numeric data
            classes_rows.append({
                "Class": class_prefix,
                "Authorised": "",
                "Issued": "",
                "Subscribed": "",
                "Paid Up": ""
            })

    return {
        "Equity Share Capital": {
            "Overall": overall_rows,
            "Number of Classes": num_classes,
            "Classes": classes_rows
        }
    }
