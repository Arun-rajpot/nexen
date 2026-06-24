import fitz, re, pandas as pd

def extract_indebtedness_summary(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = "\n".join([page.get_text("text") for page in doc])

    full_text = re.sub(r"Page\s*\d+\s*(of|/)\s*\d+", " ", full_text, flags=re.I)

    start_pat = r"\(d\)\s*Summary\s*of\s*Indebtedness"
    end_pat = r"v\s*Securities\s*\(other\s*than\s*shares\s*and\s*debentures\)"

    start = re.search(start_pat, full_text, flags=re.I)
    end = re.search(end_pat, full_text, flags=re.I)

    if not start or not end:
        raise Exception("❌ Section not found")

    block = full_text[start.end(): end.start()]
    block = re.sub(r"\s+", " ", block)

    labels = [
        "Non-convertible debentures",
        "Partly convertible debentures",
        "Fully convertible debentures",
        "Total"
    ]

    data = []

    for lbl in labels:
        pattern = lbl + r"\s*([\d.,]*)\s*([\d.,]*)\s*([\d.,]*)\s*([\d.,]*)"
        m = re.search(pattern, block, flags=re.I)

        if m:
            raw_nums = [(x.replace(",", "").strip()) for x in m.groups()]

            # ✅ Keep blank as empty string, not zero
            nums = [ (float(x) if x != "" else "") for x in raw_nums ]
        else:
            nums = ["", "", "", ""]  # ✅ all blank

        data.append([lbl] + nums)

    df = pd.DataFrame(data, columns=["Particulars", "Opening", "Increase", "Decrease", "Closing"])
    data_dict = {
        row["Particulars"]: {
            "Opening": row["Opening"],
            "Increase": row["Increase"],
            "Decrease": row["Decrease"],
            "Closing": row["Closing"]
        }
        for _, row in df.iterrows()
    }
    return data_dict



# if __name__ == "__main__":
#     pdf = r"D:\MGT-7\MGT-7\MGT-7\MGT-7_Form MGT7_01_09_2025.pdf"
#     data = extract_indebtedness_summary(pdf)
#     print(data)


