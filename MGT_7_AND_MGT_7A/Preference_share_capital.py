
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


def extract_preference_share_capital(pdf_path):
    try:
        doc = fitz.open(pdf_path)
    except:
        return {"Preference Share Capital": {"Overall": [], "Number of Classes": "0", "Classes": []}}

    # Read all pages
    pages_text = []
    for page in doc:
        txt = page.get_text("text")
        txt = re.sub(r'Page\s*\d+\s*(of|/)\s*\d+', ' ', txt)
        pages_text.append(txt)

    full_text = "\n".join(pages_text)

    # ------------------ 1) Locate section (b) ------------------
    start_pat = re.compile(r'\(b\)\s+Preference\s+share\s+capital', re.IGNORECASE)
    start_m = start_pat.search(full_text)

    if not start_m:
        return {"Preference Share Capital": {"Overall": [], "Number of Classes": "0", "Classes": []}}

    end_pat = re.compile(r'\(c\)\s+Unclassified\s+share\s+capital', re.IGNORECASE)
    end_m = end_pat.search(full_text, start_m.end())
    end_pos = end_m.start() if end_m else len(full_text)

    sec_text = full_text[start_m.end():end_pos]
    sec_text = clean_header_line(sec_text)

    # Remove "(b) Preference share capital" header line
    sec_text = re.sub(r'\(b\)\s+Preference\s+share\s+capital', '', sec_text, flags=re.IGNORECASE)
    # print(sec_text)
    # Split at "Number of classes"
    stop_m = re.search(r'Number\s+of\s+classes', sec_text, re.IGNORECASE)
    if stop_m:
        overall_text = sec_text[:stop_m.start()]
        classes_text = sec_text[stop_m.end():]
    else:
        overall_text = sec_text
        classes_text = ""
    # print(overall_text)
    overall_text = re.sub(r'\s+', ' ', overall_text).strip()
    classes_text = re.sub(r'\s+', ' ', classes_text).strip()

    # ------------------ 2) Regex for numeric 4-column table ------------------
    num_block_re = re.compile(
        r'\b([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\b'
    )

    # ------------------ 3) OVERALL section extraction ------------------
    overall_matches = list(num_block_re.finditer(overall_text))
    overall_rows = []

    if overall_matches:
        prev_end = 0
        for m in overall_matches:
            raw = overall_text[prev_end:m.start()].strip()
            raw = re.sub(r'^[\d.\)\-\:]+\s*', '', raw)
            raw = raw.strip(' :,-.')
            raw = re.sub(r'\s+', ' ', raw)

            # If blank, default label
            if not raw:
                raw = "Total"

            overall_rows.append({
                "Particular": raw,
                "Authorised": m.group(1).replace(',', ''),
                "Issued": m.group(2).replace(',', ''),
                "Subscribed": m.group(3).replace(',', ''),
                "Paid Up": m.group(4).replace(',', '')
            })

            prev_end = m.end()

    # ------------------ 4) NUMBER OF CLASSES ------------------
    # Handle multi-line number
    num_classes_m = re.search(r'Number\s+of\s+classes\s*([0-9]+)?', sec_text, re.I)
    if num_classes_m and num_classes_m.group(1):
        num_classes = num_classes_m.group(1)
    else:
        # Next line may contain only the number
        next_line_m = re.search(r'Number\s+of\s+classes\s*\n\s*([0-9]+)', full_text, re.I)
        num_classes = next_line_m.group(1) if next_line_m else "0"

    # ------------------ 5) CLASSES TABLE EXTRACTION ------------------
    classes_rows = []

    if num_classes != 0 or num_classes != "" :
        # Find Class of shares block
        cls_start = re.search(r'Class\s+of\s+shares', sec_text, re.IGNORECASE)
        if cls_start:
            cls_text = sec_text[cls_start.end():]

            matches = list(num_block_re.finditer(cls_text))
            prev_end = 0

            for m in matches:
                raw = cls_text[prev_end:m.start()].strip()
                raw = re.sub(r'^[\d.\)\-\:]+\s*', '', raw)
                raw = raw.strip(' :,-.')
                raw = re.sub(r'\s+', ' ', raw)

                if not raw:
                    raw = "Details"

                classes_rows.append({
                    "Class": raw,
                    "Authorised": m.group(1).replace(",", ""),
                    "Issued": m.group(2).replace(",", ""),
                    "Subscribed": m.group(3).replace(",", ""),
                    "Paid Up": m.group(4).replace(",", "")
                })

                prev_end = m.end()

    return {
        "Preference Share Capital": {
            "Overall": overall_rows,
            "Number of Classes": num_classes,
            "Classes": classes_rows
        }
    }
