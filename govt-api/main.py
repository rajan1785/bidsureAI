"""ComplyGeM Government API Replica.

Mock adapters for representative government data sources (GST, PAN/IT,
Udyam, MCA, EPFO, blacklist/debarment). Response envelopes are modeled on
API Setu style. In production these are replaced by officially authorized
integrations behind the same interface (SRS §16).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

SEED = json.loads((Path(__file__).parent / "seed_data.json").read_text())

app = FastAPI(
    title="ComplyGeM Government API Replica",
    description="Mock replica of government verification sources (API Setu style). "
    "All data is synthetic. mock=true on every response.",
    version="1.0.0",
)


def envelope(source: str, identifier: str, data):
    return {
        "source": source,
        "identifier": identifier,
        "status": "SUCCESS",
        "data": data,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "mock": True,
    }


def not_found(source: str, identifier: str):
    return JSONResponse(
        status_code=404,
        content={
            "source": source,
            "identifier": identifier,
            "status": "ERROR",
            "error": {"code": "RECORD_NOT_FOUND", "message": f"No {source} record for {identifier}"},
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "mock": True,
        },
    )


@app.get("/gst/{gstin}")
def gst(gstin: str):
    rec = SEED["gst"].get(gstin.upper())
    return envelope("GST", gstin.upper(), rec) if rec else not_found("GST", gstin.upper())


@app.get("/pan/{pan}")
def pan(pan: str):
    rec = SEED["pan"].get(pan.upper())
    return envelope("PAN", pan.upper(), rec) if rec else not_found("PAN", pan.upper())


@app.get("/udyam/{udyam_no}")
def udyam(udyam_no: str):
    rec = SEED["udyam"].get(udyam_no.upper())
    return envelope("UDYAM", udyam_no.upper(), rec) if rec else not_found("UDYAM", udyam_no.upper())


@app.get("/mca/{cin}")
def mca(cin: str):
    rec = SEED["mca"].get(cin.upper())
    return envelope("MCA", cin.upper(), rec) if rec else not_found("MCA", cin.upper())


@app.get("/epfo/{est_code}")
def epfo(est_code: str):
    rec = SEED["epfo"].get(est_code.upper())
    return envelope("EPFO", est_code.upper(), rec) if rec else not_found("EPFO", est_code.upper())


@app.get("/blacklist/{pan}")
def blacklist(pan: str):
    # Empty list = clean. This endpoint never 404s: absence of a record is
    # a positive "no debarment found", unlike the identity sources above.
    records = SEED["blacklist"].get(pan.upper(), [])
    return envelope("BLACKLIST", pan.upper(), {"records": records, "clean": not records})
