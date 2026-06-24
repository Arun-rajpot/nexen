# import fitz
# import re
# from typing import List, Dict, Any
#
#
# def clean_header_line(text: str) -> str:
#     """Remove all possible table headers and merged header fragments."""
#     text = re.sub(
#         r'Category\s*Number\s*of\s*directors.*?year\s*Executive\s*Non-?\s*executive\s*Executive\s*Non-?\s*executive\s*Executive\s*Non-?\s*executive',
#         '',
#         text,
#         flags=re.IGNORECASE | re.DOTALL
#     )
#     text = re.sub(
#         r'Executive\s*Non-?\s*executive\s*Executive\s*Non-?\s*executive\s*Executive\s*Non-?\s*executive',
#         '',
#         text,
#         flags=re.IGNORECASE
#     )
#     return text.strip()
#
#
# def _extract_director_rows(text_block: str) -> List[Dict[str, Any]]:
#     """
#     Extract rows flexibly from the 'A Composition of Board of Directors' table.
#     Handles 6 numeric columns. Splits 'Others' and 'Total' even if combined.
#     """
#     # Normalize whitespace
#     text_block = re.sub(r'\s+', ' ', text_block).strip()
#
#     # Attempt to separate obvious "Others Total" combinations by adding newline
#     text_block = re.sub(r'\b(Others)\s+(Total)\b', r'\1\n\2', text_block, flags=re.IGNORECASE)
#
#     # Find numeric tokens
#     num_pat = re.compile(r'\d{1,10}(?:\.\d+)?')
#     matches = list(num_pat.finditer(text_block))
#     if not matches:
#         return []
#
#     rows = []
#     prev_end = 0
#     i = 0
#
#     while i < len(matches):
#         m = matches[i]
#         raw_cat = text_block[prev_end:m.start()].strip()
#         raw_cat = re.sub(r'^[\d.\)\-]+\s*', '', raw_cat)
#         raw_cat = re.sub(r'\s+', ' ', raw_cat)
#         raw_cat = raw_cat.strip(' :,-.')
#
#         if not raw_cat or re.match(r'^\d+(\.\d+)?$', raw_cat):
#             i += 1
#             prev_end = m.end()
#             continue
#
#         # Collect up to 6 numeric values (fills missing)
#         numbers = [m.group()]
#         j = i + 1
#         while j < len(matches) and len(numbers) < 6:
#             gap = matches[j].start() - matches[j - 1].end()
#             if gap > 80:  # large gap => next row
#                 break
#             numbers.append(matches[j].group())
#             j += 1
#
#         while len(numbers) < 6:
#             numbers.append('')
#
#         beg_exec, beg_nonexec, end_exec, end_nonexec, share_exec, share_nonexec = numbers[:6]
#         rows.append({
#             "Category": raw_cat,
#             "Number of directors at the beginning of the year": {
#                 "Executive": beg_exec, "Non-executive": beg_nonexec
#             },
#             "Number of directors at the end of the year": {
#                 "Executive": end_exec, "Non-executive": end_nonexec
#             },
#             "Percentage of shares held by directors as at the end of year": {
#                 "Executive": share_exec, "Non-executive": share_nonexec
#             }
#         })
#
#         prev_end = matches[j - 1].end()
#         i = j
#
#     # cleanup: remove header remnants and duplicates
#     cleaned = []
#     seen = set()
#     for r in rows:
#         cat = r["Category"].strip()
#         if not cat or cat.lower().startswith("category"):
#             continue
#         if cat.lower() in seen:
#             continue
#         seen.add(cat.lower())
#         cleaned.append(r)
#
#     return cleaned
#
#
# def extract_board_of_directors(pdf_path: str) -> dict:
#     """Extract the full and clean 'A Composition of Board of Directors' table."""
#     doc = fitz.open(pdf_path)
#     pages_text = []
#     for page in doc:
#         text = page.get_text("text")
#         text = re.sub(r'Page\s*\d+\s*(of|/)\s*\d+', ' ', text, flags=re.IGNORECASE)
#         pages_text.append(text)
#     full_text = "\n".join(pages_text)
#
#     start_pat = re.compile(r'\bA\s+Composition\s+of\s+Board\s+of\s+Directors\b', re.IGNORECASE)
#     end_pat = re.compile(r'\bB\s*\(i\)\s*Details\s+of\s+directors\b', re.IGNORECASE)
#     start_m = start_pat.search(full_text)
#     end_m = end_pat.search(full_text)
#
#     if not start_m:
#         raise SystemExit("❌ Could not find 'A Composition of Board of Directors' section.")
#     if not end_m:
#         raise SystemExit("❌ Could not find the end section marker.")
#
#     table_text = full_text[start_m.end():end_m.start()]
#     table_text = clean_header_line(table_text)
#
#     # Cut before footnote or next section if present
#     table_text = re.split(r'\*Number\s+of\s+Directors', table_text, flags=re.IGNORECASE)[0]
#
#     rows = _extract_director_rows(table_text)
#
#     # --------------------------
#     # Post-process: split any merged "Others ... Total" rows
#     # --------------------------
#     processed = []
#     for r in rows:
#         cat = r["Category"].strip()
#         # If category contains both Others and Total (merged), split them:
#         if re.search(r'\bOthers\b', cat, re.IGNORECASE) and re.search(r'\bTotal\b', cat, re.IGNORECASE):
#             # treat this row's numeric values as belonging to Total
#             total_row = {
#                 "Category": "Total",
#                 "Number of directors at the beginning of the year": r["Number of directors at the beginning of the year"],
#                 "Number of directors at the end of the year": r["Number of directors at the end of the year"],
#                 "Percentage of shares held by directors as at the end of year": r["Percentage of shares held by directors as at the end of year"]
#             }
#             # create an Others row with blanks
#             others_row = {
#                 "Category": "v Others",
#                 "Number of directors at the beginning of the year": {"Executive": '', "Non-executive": ''},
#                 "Number of directors at the end of the year": {"Executive": '', "Non-executive": ''},
#                 "Percentage of shares held by directors as at the end of year": {"Executive": '', "Non-executive": ''}
#             }
#             processed.append(others_row)
#             processed.append(total_row)
#             continue
#
#         # If category looks like "v Others" but has numbers — keep numbers (some PDFs do have numbers)
#         # Otherwise keep as-is
#         processed.append(r)
#
#     # Ensure ordering: place Total at end if present; else append blank Total
#     total_idx = next((i for i, x in enumerate(processed) if re.search(r'\bTotal\b', x["Category"], re.IGNORECASE)), None)
#     if total_idx is not None and total_idx != len(processed) - 1:
#         total_row = processed.pop(total_idx)
#         processed.append(total_row)
#
#     if not any(re.search(r'\bTotal\b', x["Category"], re.IGNORECASE) for x in processed):
#         processed.append({
#             "Category": "Total",
#             "Number of directors at the beginning of the year": {"Executive": '', "Non-executive": ''},
#             "Number of directors at the end of the year": {"Executive": '', "Non-executive": ''},
#             "Percentage of shares held by directors as at the end of year": {"Executive": '', "Non-executive": ''}
#         })
#
#     # Ensure 'v Others' exists (insert before Total if missing)
#     if not any(re.search(r'\bOthers\b', x["Category"], re.IGNORECASE) for x in processed):
#         # insert just before last row (Total)
#         processed.insert(len(processed) - 1, {
#             "Category": "v Others",
#             "Number of directors at the beginning of the year": {"Executive": '', "Non-executive": ''},
#             "Number of directors at the end of the year": {"Executive": '', "Non-executive": ''},
#             "Percentage of shares held by directors as at the end of year": {"Executive": '', "Non-executive": ''}
#         })
#
#     # Final cleanup: strip categories and dedupe minor header leftovers
#     final = []
#     seen = set()
#     for r in processed:
#         cat = re.sub(r'\s+', ' ', r["Category"]).strip()
#         if not cat or cat.lower().startswith("category"):
#             continue
#         if cat.lower() in seen:
#             continue
#         seen.add(cat.lower())
#         r["Category"] = cat
#         final.append(r)
#
#     return {"A Composition of Board of Directors": final}

import fitz
import re
from pathlib import Path


HEADERS = [
    "Category",
    "Begin Exec", "Begin NonExec",
    "End Exec", "End NonExec",
    "Share Exec", "Share NonExec"
]


def find_board_section_pages(pdf_path: str):
    doc = fitz.open(pdf_path)
    start = end = None

    for pno in range(len(doc)):
        text = doc[pno].get_text()
        if "A Composition of Board of Directors" in text and start is None:
            start = pno
        if "Details of directors and Key managerial personnel" in text and start is not None:
            end = pno
            break

    doc.close()
    return start, end


def extract_tables_from_pages(pdf_path, start, end):
    doc = fitz.open(pdf_path)
    all_tables = []

    for pno in range(start, end + 1):
        page = doc[pno]
        tables = page.find_tables()
        for t in tables:
            all_tables.append(t.extract())

    doc.close()
    return all_tables


def clean_and_merge_board_tables(tables):
    rows = []

    for tab in tables:
        for row in tab:
            if len(row) < 7:
                continue

            cleaned = [str(c).replace("\n", " ").strip() for c in row[:7]]
            first = cleaned[0]

            # Skip headers
            if first.lower() == "category" or "number of directors" in first.lower():
                continue

            if not first or first.lower() in ["nan", "none"]:
                continue

            nums = []
            for v in cleaned[1:]:
                v = v.replace(",", "").strip()
                nums.append(v)

            rows.append((first, nums))

    return rows


def build_board_json(rows):
    result = []

    for title, values in rows:
        data = dict(zip(HEADERS[1:], values))

        result.append({
            "Category": title,
            "Number of directors at the beginning of the year": {
                "Executive": data["Begin Exec"],
                "Non-executive": data["Begin NonExec"]
            },
            "Number of directors at the end of the year": {
                "Executive": data["End Exec"],
                "Non-executive": data["End NonExec"]
            },
            "Percentage of shares held by directors as at the end of year": {
                "Executive": data["Share Exec"],
                "Non-executive": data["Share NonExec"]
            }
        })

    return {"A Composition of Board of Directors": result}


def process_board_of_directors(pdf_path: str):
    start, end = find_board_section_pages(pdf_path)
    if start is None:
        print("Section not found")
        return None

    if end is None:
        end = start

    tables = extract_tables_from_pages(pdf_path, start, end)
    if not tables:
        print("No tables found")
        return None

    rows = clean_and_merge_board_tables(tables)
    if not rows:
        print("No valid rows")
        return None

    return build_board_json(rows)