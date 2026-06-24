import fitz, re, pandas as pd


def extract_securities_text(pdf):
    doc = fitz.open(pdf)
    text = "\n".join([p.get_text("text") for p in doc])

    text = re.sub(r"Page\s*\d+\s*(of|/)\s*\d+", " ", text, flags=re.I)

    start = re.search(r"v\s*Securities\s*\(other\s*than\s*shares\s*and\s*debentures\)", text, re.I)
    end = re.search(r"V\s*Turnover\s*and\s*net\s*worth", text, re.I)

    if not start or not end:
        print("❌ Securities section not found")
        return {}

    block = text[start.end():end.start()].strip()
    block = re.sub(r"\s+", " ", block)

    # Pattern → Name + 5 numbers
    pattern = re.compile(
        r"([A-Za-z][A-Za-z\s\-\(\)/]+?)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)",
        re.I
    )

    results = {}

    for m in pattern.finditer(block):
        name = m.group(1).strip()
        nums = [float(x.replace(",", "")) for x in m.groups()[1:]]

        # ✅ Clean header junk from name
        clean_name = (
            name.replace("Type of Securities", "")
            .replace("Number of Securities", "")
            .replace("Nominal Value of each Unit", "")
            .replace("Total Nominal Value", "")
            .replace("Paid up Value of each Unit", "")
            .replace("Total Paid up Value", "")
            .strip()
        )
        clean_name = re.sub(r"\s+", " ", clean_name).strip()

        results[clean_name] = {
            "Number": nums[0],
            "Nominal_Per_Unit": nums[1],
            "Total_Nominal": nums[2],
            "Paidup_Per_Unit": nums[3],
            "Total_Paidup": nums[4],
        }

    return results



