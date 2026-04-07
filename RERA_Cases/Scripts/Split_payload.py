
# ===== split if respondent or Applicant contain multiple company =======================


def split_payload(payload):
    result = []
    keys_to_check = ['Applicant', 'Respondent']

    for key in keys_to_check:
        if key in payload and payload[key]:
            companies = [c.strip().replace('M/s.', '').replace('M/S', '').replace('M/s', '').strip()
                         for c in payload[key].split(',') if c.strip()]
            if len(companies) > 1:
                for company in companies:
                    new_payload = payload.copy()
                    new_payload[key] = company
                    result.append(new_payload)
                return result  # If split is successful, return early
    result.append(payload)
    return result