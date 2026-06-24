import fitz
import re


def clean_header_line(text):
    """Remove common table headers"""
    text = re.sub(
        r'Classes\s+of\s+partly\s+convertible\s+debentures\s+Number\s+of\s+units\s+Nominal\s+value\s+per\s+unit\s+Total\s+value\s*\(Outstanding\s+at\s+the\s+end\s+of\s+the\s+year\)\s*',
        ' ', text, flags=re.IGNORECASE)
    text = re.sub(
        r'Classes\s+of\s+partly\s+convertible\s+debentures\s+Outstanding\s+as\s+at\s+the\s+beginning\s+of\s+the\s+year\s+Increase\s+during\s+the\s+year\s+Decrease\s+during\s+the\s+year\s+Outstanding\s+as\s+at\s+the\s+end\s+of\s+the\s+year\s*',
        ' ', text, flags=re.IGNORECASE)
    return text


def extract_partly_convertible_debentures(pdf_path):
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return {"Partly Convertible Debentures": {"Number of Classes": "0", "Nominal Value Table": [],
                                                  "Movement Table": []}}

    pages_text = []
    for page in doc:
        t = page.get_text("text")
        t = re.sub(r'Page\s*\d+\s*(of|/)\s*\d+', ' ', t, flags=re.IGNORECASE)
        pages_text.append(t)
    full_text = "\n".join(pages_text)

    # Start marker
    start_pat = re.compile(r'\(b\)\s+Partly\s+convertible\s+debentures', re.IGNORECASE)
    start_m = start_pat.search(full_text)
    if not start_m:
        return {"Partly Convertible Debentures": {"Number of Classes": "0", "Nominal Value Table": [],
                                                  "Movement Table": []}}

    # End marker — next section (c) Fully convertible
    end_pat = re.compile(r'\(c\)\s+Fully\s+convertible\s+debentures', re.IGNORECASE)
    end_m = end_pat.search(full_text, start_m.end())
    end_pos = end_m.start() if end_m else len(full_text)

    table_text = full_text[start_m.end():end_pos]
    table_text = clean_header_line(table_text)
    table_text = re.sub(r'\s+', ' ', table_text).strip()

    # === Extract Number of Classes ===
    classes_match = re.search(r'\*\s*Number\s+of\s+classes\s+(\d+)', table_text, re.IGNORECASE)
    num_classes = classes_match.group(1) if classes_match else "0"

    # Regex for numeric blocks
    num_block_re = re.compile(r'\b([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\b')

    # Split into two tables
    nominal_header = re.search(r'Nominal\s+value\s+per\s+unit', table_text, re.IGNORECASE)
    movement_header = re.search(r'Outstanding\s+as\s+at\s+the\s+beginning', table_text, re.IGNORECASE)

    nominal_text = ""
    movement_text = ""

    if nominal_header and movement_header:
        if nominal_header.start() < movement_header.start():
            nominal_text = table_text[:movement_header.start()]
            movement_text = table_text[movement_header.start():]
        else:
            nominal_text = table_text[:nominal_header.start()]
            movement_text = table_text[nominal_header.start():]
    elif nominal_header:
        nominal_text = table_text
    elif movement_header:
        movement_text = table_text
    else:
        nominal_text = table_text

    # === NOMINAL VALUE TABLE ===
    nominal_rows = []
    nominal_matches = list(num_block_re.finditer(nominal_text))
    prev_end = 0
    class_name = "Partly Convertible Debentures"

    if nominal_matches:
        for m in nominal_matches:
            raw_class = nominal_text[prev_end:m.start()].strip()
            raw_class = re.sub(r'^[\d.\)\-\:]+\s*', '', raw_class)
            raw_class = raw_class.strip(' :,-.')
            raw_class = re.sub(r'\s+', ' ', raw_class)
            if not raw_class or "total" in raw_class.lower():
                raw_class = class_name

            units = m.group(1).replace(',', '').strip() or ""
            nom_per_unit = m.group(2).replace(',', '').strip() or ""
            total_value = m.group(3).replace(',', '').strip() or ""

            nominal_rows.append({
                "Class": raw_class,
                "Number of Units": units,
                "Nominal Value per Unit": nom_per_unit,
                "Total Value (End of Year)": total_value
            })
            prev_end = m.end()
    else:
        # Default if blank
        nominal_rows.append({
            "Class": class_name,
            "Number of Units": "",
            "Nominal Value per Unit": "",
            "Total Value (End of Year)": ""
        })

    return {
        "Partly Convertible Debentures": {
            "Number of Classes": num_classes,
            "Nominal Value Table": nominal_rows,
        }
    }

