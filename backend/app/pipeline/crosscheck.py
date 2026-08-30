"""Cross-verification of bidder documents vs government source data (FR-C01..04).

Outcomes: MATCH | MISMATCH | EXPIRED | MISSING | SOURCE_UNAVAILABLE | HIT
(HIT is blacklist-specific: an active debarment record exists.)
"""
from datetime import date, datetime


def _parse_date(s: str):
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _field(extracted_by_doc: dict, doc_type: str, field: str):
    for f in extracted_by_doc.get(doc_type, []):
        if f["field"] == field:
            return f
    return None


def _record(govt_records: list, source: str):
    return next((r for r in govt_records if r["source"] == source), None)


def crosscheck(extracted_by_doc: dict, registered: dict, govt_records: list,
               today: date | None = None) -> list[dict]:
    """extracted_by_doc: {doc_type: [field dicts]}; registered: bidder identifiers.

    Returns checks: {check, doc_value, registered_value, source_value,
                     source_status, outcome, note}
    """
    today = today or date.today()
    checks = []

    def add(check, doc_value, registered_value, source_value, source_status, outcome, note=""):
        checks.append({
            "check": check, "doc_value": doc_value, "registered_value": registered_value,
            "source_value": source_value, "source_status": source_status,
            "outcome": outcome, "note": note,
        })

    # --- identifier checks: doc value vs registered vs source ---
    id_specs = [
        ("gstin", "GST_CERT", "gstin", "GST"),
        ("pan", "PAN_CARD", "pan", "PAN"),
        ("udyam", "UDYAM_CERT", "udyam", "UDYAM"),
        ("epfo", "EPFO_REG", "epfo_code", "EPFO"),
    ]
    for check, doc_type, reg_key, source in id_specs:
        f = _field(extracted_by_doc, doc_type, reg_key if reg_key != "epfo_code" else "epfo_code")
        doc_value = f["value"] if f else None
        reg_value = (registered.get(reg_key) or "").strip() or None
        rec = _record(govt_records, source)
        source_status = rec["status"] if rec else "UNAVAILABLE"
        source_payload = rec["payload"] if rec else {}

        if doc_value is None:
            add(check, None, reg_value, None, source_status, "MISSING",
                f"No {check.upper()} found in submitted documents")
            continue
        if source_status != "SUCCESS":
            add(check, doc_value, reg_value, None, source_status, "SOURCE_UNAVAILABLE",
                "Government source could not verify this identifier")
            continue
        if reg_value and doc_value.upper() != reg_value.upper():
            add(check, doc_value, reg_value, reg_value, source_status, "MISMATCH",
                f"Document shows {doc_value} but registered/verified identifier is {reg_value}")
            continue

        # status / validity on the source record
        status = str(source_payload.get("status", "")).lower()
        if status and status not in ("active", "valid"):
            add(check, doc_value, reg_value, status, source_status, "MISMATCH",
                f"Source status is '{source_payload.get('status')}'")
            continue

        valid_until = _parse_date(str(source_payload.get("valid_until", "")))
        doc_valid_f = _field(extracted_by_doc, doc_type, "valid_until")
        doc_valid = _parse_date(doc_valid_f["value"]) if doc_valid_f else None
        expiry = valid_until or doc_valid
        if expiry and expiry < today:
            add(check, doc_value, reg_value, str(expiry), source_status, "EXPIRED",
                f"Validity ended on {expiry.isoformat()}")
            continue

        add(check, doc_value, reg_value, doc_value, source_status, "MATCH")

    # --- blacklist ---
    rec = _record(govt_records, "BLACKLIST")
    if rec is None or rec["status"] != "SUCCESS":
        add("blacklist", None, registered.get("pan"), None, "UNAVAILABLE",
            "SOURCE_UNAVAILABLE", "Debarment source not reachable")
    else:
        active = [r for r in rec["payload"].get("records", [])
                  if str(r.get("status", "")).lower() == "active"]
        if active:
            add("blacklist", None, registered.get("pan"),
                active[0].get("authority", ""), "SUCCESS", "HIT",
                f"Active debarment by {active[0].get('authority')} until {active[0].get('debarment_end')}")
        else:
            add("blacklist", None, registered.get("pan"), "clean", "SUCCESS", "MATCH",
                "No active debarment record")

    # --- document presence checks (PSARA license etc.) ---
    for doc_type, check_name in (("PSARA_LICENSE", "psara_license"),):
        fields = extracted_by_doc.get(doc_type)
        if fields is None:
            add(check_name, None, None, None, "N/A", "MISSING",
                f"Mandatory document {doc_type} not submitted")
        else:
            lic = _field(extracted_by_doc, doc_type, "license_no")
            vu_f = _field(extracted_by_doc, doc_type, "valid_until")
            vu = _parse_date(vu_f["value"]) if vu_f else None
            if vu and vu < today:
                add(check_name, lic["value"] if lic else "present", None, None, "N/A",
                    "EXPIRED", f"Licence validity ended {vu.isoformat()}")
            else:
                add(check_name, lic["value"] if lic else "present", None, None, "N/A", "MATCH",
                    "Licence document present" + (f", valid until {vu.isoformat()}" if vu else ""))

    # --- local content declaration (may live in a dedicated decl or a company profile) ---
    lc = (_field(extracted_by_doc, "LOCAL_CONTENT_DECL", "local_content_pct")
          or _field(extracted_by_doc, "COMPANY_PROFILE", "local_content_pct"))
    if lc:
        add("local_content", lc["value"], None, None, "N/A", "MATCH",
            f"Declared local content {lc['value']}%")
    else:
        add("local_content", None, None, None, "N/A", "MISSING",
            "No local content declaration submitted")

    return checks
