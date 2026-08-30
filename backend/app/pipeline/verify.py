"""Government source verification via the common adapter interface (FR-G01..04).

Queries the Government API Replica. An unreachable or 404 source is recorded
as UNAVAILABLE — never silently treated as compliant (FR-G04).
"""
import os

import httpx

GOVT_API = os.environ.get("GOVT_API_URL", "http://127.0.0.1:9000")

# source name -> (endpoint, which registered identifier to use)
SOURCES = [
    ("GST", "/api/v1/gstn/verify/{}", "gstin"),
    ("PAN", "/api/v1/pan/verify/{}", "pan"),
    ("UDYAM", "/api/v1/udyam/verify/{}", "udyam"),
    ("EPFO", "/api/v1/epfo/establishment/{}", "epfo_code"),
    ("BLACKLIST", "/api/v1/debarment/check/{}", "pan"),
]


def verify_identifiers(registered: dict) -> list[dict]:
    """registered: {'gstin':..,'pan':..,'udyam':..,'epfo_code':..} (may have blanks).

    Returns one record per source:
    {source, identifier, status: SUCCESS|UNAVAILABLE, payload, mock}
    """
    records = []
    with httpx.Client(timeout=10) as client:
        for source, path, key in SOURCES:
            identifier = (registered.get(key) or "").strip()
            if not identifier:
                records.append(
                    {"source": source, "identifier": "", "status": "UNAVAILABLE",
                     "payload": {"error": "no identifier provided"}, "mock": True}
                )
                continue
            try:
                r = client.get(GOVT_API + path.format(identifier))
                if r.status_code == 200:
                    body = r.json()
                    records.append(
                        {"source": source, "identifier": identifier, "status": "SUCCESS",
                         "payload": body.get("data", {}), "mock": body.get("mock", True)}
                    )
                else:
                    records.append(
                        {"source": source, "identifier": identifier, "status": "UNAVAILABLE",
                         "payload": r.json().get("error", {}), "mock": True}
                    )
            except Exception as e:
                records.append(
                    {"source": source, "identifier": identifier, "status": "UNAVAILABLE",
                     "payload": {"error": str(e)}, "mock": True}
                )
    return records
