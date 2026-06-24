#============================ final code ====================================

import fitz
import re

# --------------------------------------------------
# Find B section pages
# --------------------------------------------------
def find_b_promoter_pages(pdf_path):
    doc = fitz.open(pdf_path)
    start = end = None

    for i in range(len(doc)):
        text = doc[i].get_text().lower()

        if start is None and (
            "b other than promoters" in text
            or "public/other than promoters" in text
        ):
            start = i

        if start is not None and "total number of shareholders (other than promoters)" in text:
            end = i
            break

    if start is not None and end is None:
        end = len(doc) - 1

    doc.close()
    return start, end


# --------------------------------------------------
# Find vertical position of heading
# --------------------------------------------------
def find_text_y(page):
    texts = ["B Other than promoters", "Public/Other than promoters"]
    for text in texts:
        areas = page.search_for(text)
        if areas:
            return areas[0].y0
    return None


# --------------------------------------------------
# Identify B promoter table
# --------------------------------------------------
def is_b_promoter_table(df):
    if not df or len(df) < 2:
        return False

    header = " ".join(str(x) for x in df[0]).lower()
    if "category" in header and "equity" in header and "preference" in header:
        return True

    known = ["individual", "government", "insurance", "banks", "mutual", "venture", "others"]
    content = " ".join(str(x).lower() for row in df[:4] for x in row if x)
    return any(k in content for k in known)


# --------------------------------------------------
# Extract rows from all pages
# --------------------------------------------------
def extract_b_rows(pdf_path, start, end):
    doc = fitz.open(pdf_path)
    rows = []

    for p in range(start, end + 1):
        page = doc[p]
        heading_y = None

        if p == start:
            heading_y = find_text_y(page)

        for t in page.find_tables():
            bbox = t.bbox

            if p == start and heading_y and bbox[1] < heading_y:
                continue

            df = t.extract()
            if not is_b_promoter_table(df):
                continue

            for r in df:
                if not r:
                    continue

                r = list(r) + [""] * (6 - len(r))

                s_no = str(r[0]).strip()
                cat = str(r[1]).replace("\n", " ").strip()
                eq_num = str(r[2]).strip()
                eq_pct = str(r[3]).strip()
                pref_num = str(r[4]).strip()
                pref_pct = str(r[5]).strip()

                if cat.lower() in ["category", "nan", "none", ""]:
                    continue
                if "number of shares" in cat.lower():
                    continue

                rows.append([s_no, cat, eq_num, eq_pct, pref_num, pref_pct])

    doc.close()
    return rows


# --------------------------------------------------
# Build final structured output
# --------------------------------------------------
def build_b_promoters(rows):
    result = []
    parent = None

    for s_no, cat, eq_num, eq_pct, pref_num, pref_pct in rows:
        cat_clean = cat.strip()

        if cat_clean.lower() == "total":
            result.append({
                "Category": "Total",
                "Equity": {"Number of shares": eq_num, "Percentage": eq_pct},
                "Preference": {"Number of shares": pref_num, "Percentage": pref_pct}
            })
            break

        if s_no.isdigit() and not eq_num and cat_clean.lower() not in ["others", "total"]:
            parent = cat_clean
            continue

        if cat_clean.startswith("("):
            full = f"{parent} {cat_clean}" if parent else cat_clean
        else:
            full = cat_clean

        result.append({
            "Category": full,
            "Equity": {"Number of shares": eq_num, "Percentage": eq_pct},
            "Preference": {"Number of shares": pref_num, "Percentage": pref_pct}
        })

    return {"B Other than promoters": result}


# --------------------------------------------------
# Wrapper
# --------------------------------------------------
def extract_b_promoters(pdf_path):
    start, end = find_b_promoter_pages(pdf_path)

    if start is None:
        raise SystemExit("❌ B Other than promoters section not found")

    rows = extract_b_rows(pdf_path, start, end)
    return build_b_promoters(rows)

# # ------------------ RUN ------------------
if __name__ == "__main__":
    pdf = r"C:\Users\PC\Downloads\mgt\MGT7_2025.pdf"
    data = extract_b_promoters(pdf)
    print(data)