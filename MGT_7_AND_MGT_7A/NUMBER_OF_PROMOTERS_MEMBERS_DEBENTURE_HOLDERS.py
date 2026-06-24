# import fitz
# import re
# from typing import List, Dict, Any
#
# def vii_number_of_promoters_member_debenture(pdf_path):
#     """
#     Extracts the 'VII NUMBER OF PROMOTERS, MEMBERS, DEBENTURE HOLDERS'
#     section from the MGT-7 form and returns structured data.
#     """
#     doc = fitz.open(pdf_path)
#     pages_text = []
#     for page in doc:
#         t = page.get_text("text")
#         # Remove footers like "Page 10 of 23"
#         t = re.sub(r'Page\s*\d+\s*(of|/)\s*\d+', ' ', t, flags=re.IGNORECASE)
#         pages_text.append(t)
#
#     full_text = "\n".join(pages_text)
#     full_text = re.sub(r'\s+', ' ', full_text).strip()
#
#     # --- Define start and end markers for this section ---
#     start_pat = re.compile(
#         r'VII\s+NUMBER\s+OF\s+PROMOTERS,\s*MEMBERS,\s*DEBENTURE\s*HOLDERS\s*\[Details\s*of\s*Promoters,\s*Members\s*\(other\s*than\s*promoters\),\s*Debenture\s*holders\]',
#         re.IGNORECASE
#     )
#     end_pat = re.compile(
#         r'VIII\s+DETAILS\s+OF\s+DIRECTORS\s+AND\s+KEY\s+MANAGERIAL\s+PERSONNEL',
#         re.IGNORECASE
#     )
#
#     start_m = start_pat.search(full_text)
#     end_m = end_pat.search(full_text)
#
#     if not start_m:
#         raise SystemExit("❌ Could not find start of 'VII NUMBER OF PROMOTERS...' section.")
#     if not end_m:
#         raise SystemExit("❌ Could not find 'VIII DETAILS OF DIRECTORS AND KEY MANAGERIAL PERSONNEL' section.")
#
#     section_text = full_text[start_m.end():end_m.start()]
#     section_text = re.sub(r'\s+', ' ', section_text).strip()
#
#     # Example pattern:
#     # Promoters 5 5 Members (other than promoters) 28 28 Debenture holders 0 0
#     pattern = re.compile(
#         r'Promoters\s+(\d+)\s+(\d+).*?Members\s*\(other\s*than\s*promoters\)\s+(\d+)\s+(\d+).*?Debenture\s*holders\s+(\d+)\s+(\d+)',
#         re.IGNORECASE
#     )
#
#     match = pattern.search(section_text)
#     if not match:
#         raise SystemExit("❌ Could not find expected numeric pattern for this section.")
#
#     promoters_begin, promoters_end, members_begin, members_end, debentures_begin, debentures_end = match.groups()
#
#     result = {
#         "VII NUMBER OF PROMOTERS": [
#             {
#                 "Promoters": {
#                     "At the beginning of the year": promoters_begin,
#                     "At the end of the year": promoters_end
#                 }
#             },
#             {
#                 "Members (other than promoters)": {
#                     "At the beginning of the year": members_begin,
#                     "At the end of the year": members_end
#                 }
#             },
#             {
#                 "Debenture holders": {
#                     "At the beginning of the year": debentures_begin,
#                     "At the end of the year": debentures_end
#                 }
#             }
#         ]
#     }
import fitz
import re

def vii_number_of_promoters_member_debenture(pdf_path):
    doc = fitz.open(pdf_path)
    pages_text = []

    for page in doc:
        t = page.get_text("text")
        t = re.sub(r'Page\s*\d+\s*(of|/)\s*\d+', ' ', t, flags=re.IGNORECASE)
        pages_text.append(t)

    full_text = "\n".join(pages_text)
    full_text = re.sub(r'\s+', ' ', full_text).strip()

    # -------- Flexible start heading --------
    start_pat = re.compile(
        r'VII\s+NUMBER\s+OF\s+PROMOTERS,\s*MEMBERS,\s*DEBENTURE\s*HOLDERS',
        re.IGNORECASE
    )

    # -------- Flexible end heading --------
    end_pat = re.compile(
        r'VIII\s+(DETAILS\s+OF\s+DIRECTORS\s+AND\s+KEY\s+MANAGERIAL\s+PERSONNEL|'
        r'MEETINGS\s+OF\s+MEMBERS|MEETINGS\s+OF\s+MEMBERS/CLASS)',
        re.IGNORECASE
    )

    start_m = start_pat.search(full_text)
    end_m = end_pat.search(full_text)

    if not start_m:
        raise SystemExit("❌ Could not find start of 'VII NUMBER OF PROMOTERS...' section.")
    if not end_m:
        raise SystemExit("❌ Could not find end of section after VII.")

    section_text = full_text[start_m.end():end_m.start()]
    section_text = re.sub(r'\s+', ' ', section_text).strip()

    # -------- Extract numbers --------
    pattern = re.compile(
        r'Promoters\s+(\d+)\s+(\d+).*?'
        r'Members\s*\(other\s*than\s*promoters\)\s+(\d+)\s+(\d+).*?'
        r'Debenture\s*holders\s+(\d+)\s+(\d+)',
        re.IGNORECASE
    )

    match = pattern.search(section_text)
    if not match:
        raise SystemExit("❌ Could not find numeric rows inside VII section.")

    promoters_begin, promoters_end, members_begin, members_end, debentures_begin, debentures_end = match.groups()

    return {
        "VII NUMBER OF PROMOTERS": [
            {
                "Promoters": {
                    "At the beginning of the year": promoters_begin,
                    "At the end of the year": promoters_end
                }
            },
            {
                "Members (other than promoters)": {
                    "At the beginning of the year": members_begin,
                    "At the end of the year": members_end
                }
            },
            {
                "Debenture holders": {
                    "At the beginning of the year": debentures_begin,
                    "At the end of the year": debentures_end
                }
            }
        ]
    }



#
# # # ------------------ RUN ------------------
# if __name__ == "__main__":
#     pdf = r"D:\MGT7A\MGT-7A\MGT-7A_Form MGT7A_05_09_2025.pdf"
#     data = vii_number_of_promoters_member_debenture(pdf)
#     print(data)