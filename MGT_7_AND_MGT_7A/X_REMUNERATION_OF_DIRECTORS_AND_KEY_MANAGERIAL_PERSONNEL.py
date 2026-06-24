import fitz
import pdfplumber
import pandas as pd




# ----------------------------------------
# STEP 1 — Find Start & End pages
# ----------------------------------------
def find_page_for_heading(pdf_path, heading):
    heading_low = heading.lower()

    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text").lower().replace("\n", " ")
            if heading_low[:30] in text:
                return i
    return None


# ----------------------------------------
# STEP 2 — Extract all pdfplumber tables
# ----------------------------------------
def extract_plumber_tables(pdf_path, start_page, end_page):
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for pg in range(start_page - 1, end_page):
            page = pdf.pages[pg]
            page_tables = page.extract_tables()

            for tbl in page_tables:
                if tbl:
                    df = pd.DataFrame(tbl)
                    tables.append(df)
    return tables


# ----------------------------------------
# STEP 3 — Detect remuneration table header
# ----------------------------------------
def is_main_header(df):
    try:
        header = df.iloc[0].astype(str).str.lower().tolist()
        c0 = header[0].replace(".", "").replace("\n", "").strip()
        c1 = header[1].replace("\n", "").strip()
        c2 = header[2].replace("\n", "").strip()

        return (
                c0.startswith("s") and
                "name" in c1 and
                "design" in c2
        )
    except:
        return False


# ----------------------------------------
# STEP 4 — Break when penalty/other section starts
# ----------------------------------------
def is_break_table(df):
    try:
        first_cell = str(df.iloc[0, 0]).lower()
        return first_cell.startswith("name of the")
    except:
        return False


# ----------------------------------------
# STEP 5 — Clean table (remove \n, spaces, junk)
# ----------------------------------------
# def clean_table(df):
#     df = df.copy()
#     df = df.applymap(lambda x: str(x).replace("\n", " ").strip() if pd.notnull(x) else "")
#     return df
def clean_table(df):
    df = df.copy()
    df = df.map(lambda x: str(x).replace("\n", " ").strip() if pd.notnull(x) else "")
    return df

# ----------------------------------------
# STEP 6 — Set proper headers
# ----------------------------------------
def format_table(df):
    df = clean_table(df)
    header = df.iloc[0].tolist()
    df = df[1:].reset_index(drop=True)
    df.columns = header
    return df


# ----------------------------------------
# STEP 7 — Merge continuation tables
# ----------------------------------------
def merge_remuneration_tables(all_tables):
    final = []
    current = None
    started = False

    for df in all_tables:

        # STOP when penalty table appears
        if is_break_table(df):
            break

        # Case 1: Found main header → new table
        if is_main_header(df):
            if current is not None:
                final.append(format_table(current))

            current = df.copy()
            started = True
            continue

        # Case 2: Continuation (no header)
        if started and not is_main_header(df):
            current = pd.concat([current, df], ignore_index=True)
            continue

    if current is not None:
        final.append(format_table(current))

    return final[:3]  # return exactly 3 tables


# ----------------------------------------
# MASTER FUNCTION
def df_to_dict(df):
    df = df.replace("", None)  # optional clean
    return df.to_dict(orient="records")


def tables_to_dict(final_tables):
    output = {}
    for i, df in enumerate(final_tables, start=1):
        key = f"table_{i}"
        output[key] = df_to_dict(df)
    return output


# ----------------------------------------

def auto_extract_clean_three(pdf_path):

    if "MGT7A" in pdf_path.upper() or "MGT-7A" in pdf_path.upper():
        START_HEADING = "IX REMUNERATION OF DIRECTORS"
        END_HEADING = "X MATTERS RELATED TO CERTIFICATION OF COMPLIANCES AND DISCLOSURES"

    else:
        START_HEADING = "X REMUNERATION OF DIRECTORS AND KEY MANAGERIAL PERSONNEL"
        END_HEADING = "XI MATTERS RELATED TO CERTIFICATION OF COMPLIANCES AND DISCLOSURES"

    start = find_page_for_heading(pdf_path, START_HEADING)
    end = find_page_for_heading(pdf_path, END_HEADING)

    print("START PAGE =", start)
    print("END PAGE   =", end)
    if start is None or end is None:
        return {}
    all_tables = extract_plumber_tables(pdf_path, start, end)

    final_three = merge_remuneration_tables(all_tables)
    final_dict = tables_to_dict(final_three)
    return final_dict

#
# if __name__ == "__main__":
#     pdf = r"C:\Users\PC\Downloads\mgt\MGT7_2025.pdf"
#     data = auto_extract_clean_three(pdf)
#     print(data)