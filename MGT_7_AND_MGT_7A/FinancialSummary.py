import pdfplumber
import re
from pathlib import Path


def extract_mgt7_with_pdfplumber(pdf_path: str) -> dict:
    """
    Extracts key fields line-by-line using pdfplumber to preserve layout accuracy.
    Fields:
      - i *Number of business activities
      - i *Turnover
      - ii * Net worth of the Company
      - Total shareholders (promoters)
      - Total shareholders (other than promoters)
      - Total shareholders (Promoters + Public/Other than promoters)
    """

    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                # Clean headers and page numbers
                text = re.sub(r'Page\s*\d+\s*(of|/)\s*\d+', '', text, flags=re.IGNORECASE)
                for ln in text.splitlines():
                    ln = ln.strip()
                    if ln:
                        lines.append(ln)

    result = {
        "II Principal Business Activities": {"Number of business activities": ""},
        "V Turnover and Net Worth": {"Turnover": "", "Net worth of the Company": ""},
        "VI Share Holding Pattern": {
            "Total number of shareholders (promoters)": "",
            "Total number of shareholders (other than promoters)": "",
            "Total number of shareholders (Promoters + Public/Other than promoters)": "",
        },
    }

    def find_value_near_line(keyword):
        """Find numeric value (including negative) on same line or within next 2 lines."""
        for i, line in enumerate(lines):
            if re.search(keyword, line, re.IGNORECASE):
                # Same line first
                same_line_match = re.search(r'(-?[0-9][0-9,]*\.?[0-9]*)', line)
                if same_line_match:
                    return same_line_match.group(1).replace(',', '')

                # Next 2 lines
                for j in range(i + 1, min(i + 3, len(lines))):
                    next_line = lines[j]
                    match = re.search(r'(-?[0-9][0-9,]*\.?[0-9]*)', next_line)
                    if match:
                        return match.group(1).replace(',', '')
        return ""

    # --- Extract Values ---
    result["II Principal Business Activities"]["Number of business activities"] = find_value_near_line(
        r'i\s*\*?\s*Number\s+of\s+business\s+activities'
    )
    result["V Turnover and Net Worth"]["Turnover"] = find_value_near_line(r'i\s*\*?\s*Turnover')
    result["V Turnover and Net Worth"]["Net worth of the Company"] = find_value_near_line(
        r'ii\s*\*?\s*Net\s*worth\s*of\s*the\s*Company'
    )
    result["VI Share Holding Pattern"]["Total number of shareholders (promoters)"] = find_value_near_line(
        r'Total\s+number\s+of\s+shareholders\s*\(promoters\)'
    )
    result["VI Share Holding Pattern"]["Total number of shareholders (other than promoters)"] = find_value_near_line(
        r'Total\s+number\s+of\s+shareholders\s*\(other\s+than\s+promoters\)'
    )
    result["VI Share Holding Pattern"][
        "Total number of shareholders (Promoters + Public/Other than promoters)"] = find_value_near_line(
        r'Total\s+number\s+of\s+shareholders\s*\(Promoters\s*\+\s*(?:Public/)?Other\s+than\s+promoters\)'

    )

    return result

# ------------------ RUN ------------------
if __name__ == "__main__":
    pdf = r"D:\MGT-7\MGT-7\MGT-7A\MGT-7A_Form MGT7A_05_09_2025.pdf"
    data = extract_mgt7_with_pdfplumber(pdf)
    print(data)
