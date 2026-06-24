import fitz
import re


def clean_header_line(text):
    text = re.sub(
        r'Classes\s+of\s+fully\s+convertible\s+debentures\s+Number\s+of\s+units\s+Nominal\s+value\s+per\s+unit\s+Total\s+value\s*\(Outstanding\s+at\s+the\s+end\s+of\s+the\s+year\)\s*',
        ' ', text, flags=re.IGNORECASE)
    text = re.sub(
        r'Classes\s+of\s+fully\s+convertible\s+debentures\s+Outstanding\s+as\s+at\s+the\s+beginning\s+of\s+the\s+year\s+Increase\s+during\s+the\s+year\s+Decrease\s+during\s+the\s+year\s+Outstanding\s+as\s+at\s+the\s+end\s+of\s+the\s+year\s*',
        ' ', text, flags=re.IGNORECASE)
    return text


def extract_fully_convertible_debentures(pdf_path):
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return {
            "Fully Convertible Debentures": {"Number of Classes": "0", "Nominal Value Table": [], "Movement Table": []}}

    pages_text = []
    for page in doc:
        t = page.get_text("text")
        t = re.sub(r'Page\s*\d+\s*(of|/)\s*\d+', ' ', t, flags=re.IGNORECASE)
        pages_text.append(t)
    full_text = "\n".join(pages_text)

    # Start marker
    start_pat = re.compile(r'\(c\)\s+Fully\s+convertible\s+debentures', re.IGNORECASE)
    start_m = start_pat.search(full_text)
    if not start_m:
        return {
            "Fully Convertible Debentures": {"Number of Classes": "0", "Nominal Value Table": [], "Movement Table": []}}

    # End marker
    end_pat = re.compile(r'\(d\)\s+Summary\s+of\s+Indebtedness', re.IGNORECASE)
    end_m = end_pat.search(full_text, start_m.end())
    end_pos = end_m.start() if end_m else len(full_text)

    table_text = full_text[start_m.end():end_pos]
    table_text = clean_header_line(table_text)
    table_text = re.sub(r'\s+', ' ', table_text).strip()

    # === Number of Classes (with *) ===
    classes_match = re.search(r'\*\s*Number\s+of\s+classes\s+(\d+)', table_text, re.IGNORECASE)
    num_classes = classes_match.group(1) if classes_match else "0"

    # Split into Nominal and Movement sections
    nominal_marker = re.search(r'Nominal\s+value\s+per\s+unit', table_text, re.IGNORECASE)
    movement_marker = re.search(r'Outstanding\s+as\s+at\s+the\s+beginning', table_text, re.IGNORECASE)

    nominal_text = ""
    movement_text = ""

    if nominal_marker and movement_marker:
        nominal_text = table_text[:movement_marker.start()]
        movement_text = table_text[movement_marker.start():]
    elif nominal_marker:
        nominal_text = table_text
    elif movement_marker:
        movement_text = table_text
    else:
        nominal_text = table_text

    # === NOMINAL VALUE TABLE (3 columns) ===
    nominal_re = re.compile(r'\b([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\b')  # 3 groups
    nominal_rows = []
    matches = list(nominal_re.finditer(nominal_text))
    prev_end = 0

    for m in matches:
        raw_class = nominal_text[prev_end:m.start()].strip()
        raw_class = re.sub(r'^[\d.\)\-\:]+\s*', '', raw_class)
        raw_class = raw_class.strip(' :,-.')
        raw_class = re.sub(r'\s+', ' ', raw_class)
        if not raw_class or "total" in raw_class.lower():
            continue  # Skip Total row

        units = m.group(1).replace(',', '').strip()
        nom = m.group(2).replace(',', '').strip()
        total = m.group(3).replace(',', '').strip()

        nominal_rows.append({
            "Class": raw_class,
            "Number of Units": units or "",
            "Nominal Value per Unit": nom or "",
            "Total Value (End of Year)": total or ""
        })
        prev_end = m.end()

    if not nominal_rows:
        nominal_rows.append({
            "Class": "Fully Convertible Debentures",
            "Number of Units": "",
            "Nominal Value per Unit": "",
            "Total Value (End of Year)": ""
        })

    return {
        "Fully Convertible Debentures": {
            "Number of Classes": num_classes,
            "Nominal Value Table": nominal_rows,

        }
    }

# # ------------------ RUN ------------------
# if __name__ == "__main__":
#     pdf = r"D:\MGT-7\MGT-7\MGT-7A\MGT-7A_Form MGT7A_05_09_2025.pdf"
#     data = extract_fully_convertible_debentures(pdf)
#     print(data)
