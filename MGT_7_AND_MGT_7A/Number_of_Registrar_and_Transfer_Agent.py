import pdfplumber
import re


def extract_clean_registrar_info(file_path):
    """
    Extracts and cleans 'viii Number of Registrar and Transfer Agent' table from MGT-7 PDF.
    Returns a clean dictionary.
    """
    in_section = False
    table = []

    try:
        with pdfplumber.open(file_path) as doc:
            for page in doc.pages:
                text = page.extract_text() or ""
                if "viii Number of Registrar and Transfer Agent" in text or in_section:
                    in_section = True
                    tables = page.extract_tables()
                    for t in tables:
                        cleaned = [[cell.strip() if cell else "" for cell in row] for row in t]
                        flat = " ".join(" ".join(row) for row in cleaned)

                        if re.search(
                            r'CIN of the Registrar|Name of the Registrar|Registered office address|SEBI registration number',
                            flat,
                            re.IGNORECASE,
                        ):
                            table.extend(cleaned)

                        if re.search(r'Whether Annual General Meeting \(AGM\) held', flat, re.IGNORECASE):
                            break

                if "ix * (a) Whether Annual General Meeting (AGM) held" in text:
                    break

        # ---- Convert to Dictionary ----
        registrar_data = {}

        if table and len(table) >= 2:
            headers = [re.sub(r'\s+', ' ', h.strip()) for h in table[0]]
            values = [re.sub(r'\s+', ' ', v.strip()) for v in table[1]]

            # Clean newline artifacts, double commas, trailing digits
            def clean_text(txt):
                txt = txt.replace("\n", " ")
                txt = re.sub(r'\s+', ' ', txt)
                txt = re.sub(r',\s*,+', ', ', txt)
                txt = re.sub(r'\s*,\s*', ', ', txt)
                txt = txt.strip().rstrip(',')
                # Fix addresses ending with stray numbers
                txt = re.sub(r',?\s*\b(\d{1,2})\b$', '', txt)
                return txt.strip()

            for key, val in zip(headers, values):
                registrar_data[clean_text(key)] = clean_text(val)

        return registrar_data

    except Exception as e:
        raise ValueError(f"Error processing PDF: {e}")