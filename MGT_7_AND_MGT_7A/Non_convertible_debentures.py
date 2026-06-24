
import fitz
import re


def extract_non_convertible_debentures(pdf_path):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"error": str(e)}

    full_text = ""
    for page in doc:
        text = page.get_text("text")
        text = re.sub(r'Page\s*\d+\s*of\s*\d+', '', text, flags=re.IGNORECASE)
        full_text += text + "\n"

    full_text = re.sub(r'\s+', ' ', full_text).strip()

    # === Find Section (a) ===
    start = re.search(r'\(a\)\s*Non-convertible\s+debentures', full_text, re.IGNORECASE)
    if not start:
        return {
            "Non-Convertible Debentures": {"Number of Classes": "0", "Nominal Value Table": [], "Movement Table": []}}

    end = re.search(r'\(b\)\s*Partly\s+convertible\s+debentures', full_text, re.IGNORECASE)
    end_pos = end.start() if end else len(full_text)

    section = full_text[start.end():end_pos]
    section = re.sub(r'\s+', ' ', section).strip()

    # === Extract Number of Classes ===
    classes_match = re.search(r'Number\s+of\s+classes\s+(\d+)', section, re.IGNORECASE)
    num_classes = classes_match.group(1) if classes_match else "0"

    # === Remove ALL headers & *Number of classes ===
    section = re.sub(r'\*?\s*Number\s+of\s+classes\s+\d+', ' ', section, flags=re.IGNORECASE)
    section = re.sub(r'Classes\s+of\s+non-convertible\s+debentures.*?Total\s+value.*?year\)', ' ', section,
                     flags=re.IGNORECASE)
    section = re.sub(r'Classes\s+of\s+non-convertible\s+debentures.*?Outstanding\s+as\s+at\s+the\s+end', ' ', section,
                     flags=re.IGNORECASE)
    section = re.sub(r'\s+', ' ', section).strip()

    # === Split Nominal & Movement ===
    move_start = re.search(r'Outstanding\s+as\s+at\s+the\s+beginning\s+of\s+the\s+year', section, re.IGNORECASE)
    nominal_text = section[:move_start.start()] if move_start else section
    movement_text = section[move_start.start():] if move_start else ""

    # === Parse Nominal Table (SKIP FIRST ROW = HEADER) ===
    nominal_rows = []
    matches = list(re.finditer(r'\d[\d,]*\.?\d*\s+\d[\d,]*\.?\d*\s+\d[\d,]*\.?\d*', nominal_text))

    # Skip first match if it's the header (e.g., "Number of units", "Nominal value", etc.)
    for i, m in enumerate(matches):
        if i == 0:
            continue  # Skip first row (header)

        # Extract 3 numbers
        nums = re.findall(r'\d[\d,]*\.?\d*', m.group())
        if len(nums) < 3:
            continue

        nominal_rows.append({
            "Number of Units": nums[0].replace(',', ''),
            "Nominal Value per Unit": nums[1].replace(',', ''),
            "Total Value (End of Year)": nums[2].replace(',', '')
        })

    if not nominal_rows:
        nominal_rows.append({
            "Number of Units": "",
            "Nominal Value per Unit": "",
            "Total Value (End of Year)": ""
        })

    # === Parse Movement Table (SKIP FIRST ROW = HEADER) ===
    movement_rows = []
    matches = list(re.finditer(r'\d[\d,]*\.?\d*\s+\d[\d,]*\.?\d*\s+\d[\d,]*\.?\d*\s+\d[\d,]*\.?\d*', movement_text))

    for i, m in enumerate(matches):
        if i == 0:
            continue  # Skip first row (header)

        nums = re.findall(r'\d[\d,]*\.?\d*', m.group())
        if len(nums) < 4:
            continue

        movement_rows.append({
            "Outstanding at Beginning": nums[0].replace(',', ''),
            "Increase During Year": nums[1].replace(',', ''),
            "Decrease During Year": nums[2].replace(',', ''),
            "Outstanding at End": nums[3].replace(',', '')
        })

    if not movement_rows:
        movement_rows.append({
            "Outstanding at Beginning": "",
            "Increase During Year": "",
            "Decrease During Year": "",
            "Outstanding at End": ""
        })

    return {
        "Non-Convertible Debentures": {
            "Number of Classes": num_classes,
            "Nominal Value Table": nominal_rows,
            "Movement Table": movement_rows
        }
    }


# # ------------------ RUN ------------------
# if __name__ == "__main__":
#     pdf = r"D:\MGT7A\MGT-7A\MGT-7A_Form MGT7A_05_09_2025.pdf"
#     data = extract_non_convertible_debentures(pdf)
#     print(data)