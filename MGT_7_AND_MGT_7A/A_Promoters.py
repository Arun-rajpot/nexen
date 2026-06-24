# final code for A promoters


import fitz
import re


# --------------------------------------------------
# Find A Promoters section
# --------------------------------------------------
def find_a_promoter_pages(pdf_path):
    doc = fitz.open(pdf_path)
    start = end = None

    for i in range(len(doc)):
        text = doc[i].get_text()
        if start is None and "A Promoters" in text:
            start = i
        if start is not None and "Total number of shareholders (promoters)" in text:
            end = i
            break

    doc.close()
    return start, end


# --------------------------------------------------
# Identify promoter table only
# --------------------------------------------------
def is_a_promoter_table(df):
    if not df or len(df) < 2:
        return False

    header = " ".join(str(x) for x in df[0]).lower()

    if "category" in header and "equity" in header and "preference" in header:
        return True

    known = ["individual", "government", "insurance", "banks", "mutual", "venture", "others"]
    content = " ".join(str(x).lower() for row in df[:4] for x in row if x)

    return any(k in content for k in known)


# --------------------------------------------------
# Extract rows from only promoter tables
# --------------------------------------------------
def extract_a_promoter_rows(pdf_path, start, end):
    doc = fitz.open(pdf_path)
    rows = []

    for p in range(start, end + 1):
        page = doc[p]
        for t in page.find_tables():
            df = t.extract()

            if not is_a_promoter_table(df):
                continue

            for r in df:
                # print(r)
                if not r or len(r) < 6:
                    continue

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
# Build output
# --------------------------------------------------
def build_a_promoters(rows):
    result = []
    parent = None

    for s_no, cat, eq_num, eq_pct, pref_num, pref_pct in rows:

        cat_clean = cat.strip()

        # Stop after Total
        if cat_clean.lower() == "total":
            result.append({
                "Category": "Total",
                "Equity": {"Number of shares": eq_num.replace(",", ""), "Percentage": eq_pct.replace(",", "")},
                "Preference": {"Number of shares": pref_num.replace(",", ""), "Percentage": pref_pct.replace(",", "")}
            })
            break

        # Detect parent rows EXCEPT Others
        if s_no.isdigit() and not eq_num and cat_clean.lower() not in ["others", "total"]:
            parent = cat_clean
            continue

        # Merge sub category
        if cat_clean.startswith("(") and parent:
            full = f"{parent} {cat_clean}"
        else:
            full = cat_clean

        result.append({
            "Category": full,
            "Equity": {"Number of shares": eq_num.replace(",", ""), "Percentage": eq_pct.replace(",", "")},
            "Preference": {"Number of shares": pref_num.replace(",", ""), "Percentage": pref_pct.replace(",", "")}
        })

    return {"A Promoters": result}


# def build_a_promoters(rows):
#     result = []
#     parent = None

#     for s_no, cat, eq_num, eq_pct, pref_num, pref_pct in rows:
#         if s_no.isdigit() and not eq_num:
#             parent = cat
#             continue

#         if cat.startswith("(") and parent:
#             full = f"{parent} {cat}"
#         else:
#             full = cat

#         result.append({
#             "Category": full.strip(),
#             "Equity": {"Number of shares": eq_num.replace(",", ""), "Percentage": eq_pct.replace(",", "")},
#             "Preference": {"Number of shares": pref_num.replace(",", ""), "Percentage": pref_pct.replace(",", "")}
#         })

#     # Deduplicate
#     clean = []
#     seen = set()
#     for r in result:
#         key = r["Category"].lower()
#         if key not in seen:
#             clean.append(r)
#             seen.add(key)

#     return {"A Promoters": clean}

# --------------------------------------------------
# Main
# --------------------------------------------------
def extract_a_promoters(pdf_path):
    start, end = find_a_promoter_pages(pdf_path)
    if start is None:
        raise SystemExit("❌ A Promoters section not found")

    rows = extract_a_promoter_rows(pdf_path, start, end)
    return build_a_promoters(rows)


# --------------------------------------------------
# RUN
# --------------------------------------------------
# if __name__ == "__main__":
#     pdf_path = r"D:\MGT-7\MGT-7\MGT-7\MGT-7_Form MGT7_01_09_2025.pdf"
#     data = extract_a_promoters(pdf_path)
#     print(data)
