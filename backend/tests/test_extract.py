from app.pipeline.classify import classify_doc
from app.pipeline.extract import extract_fields

GST_CERT_TEXT = """
Government of India
Form GST REG-06
Goods and Services Tax Registration Certificate
Registration Number : 07AAECS1234F1Z5
Legal Name : SHAKTI FACILITY SERVICES PRIVATE LIMITED
Date of Liability : 12/06/2018
"""

PAN_TEXT = """
INCOME TAX DEPARTMENT   GOVT. OF INDIA
Permanent Account Number Card
AAECS1234F
SHAKTI FACILITY SERVICES PRIVATE LIMITED
"""

UDYAM_TEXT = """
Ministry of Micro, Small and Medium Enterprises
UDYAM REGISTRATION CERTIFICATE
Registration Number: UDYAM-DL-01-0012345
"""

EPFO_TEXT = """
Employees' Provident Fund Organisation
Establishment Code: DLCPM0012345000
Valid Until: 31/03/2027
"""

PSARA_TEXT = """
Licence under the Private Security Agencies (Regulation) Act, 2005
License No: PSARA/DL/2023/04412
Valid upto: 31/12/2026
"""


def test_classify():
    assert classify_doc(GST_CERT_TEXT) == "GST_CERT"
    assert classify_doc(PAN_TEXT) == "PAN_CARD"
    assert classify_doc(UDYAM_TEXT) == "UDYAM_CERT"
    assert classify_doc(EPFO_TEXT) == "EPFO_REG"
    assert classify_doc(PSARA_TEXT) == "PSARA_LICENSE"
    assert classify_doc("random invoice text") == "OTHER"


def _get(fields, name):
    return next((f["value"] for f in fields if f["field"] == name), None)


def test_extract_gstin_and_not_pan_inside_gstin():
    fields = extract_fields(GST_CERT_TEXT, "GST_CERT")
    assert _get(fields, "gstin") == "07AAECS1234F1Z5"
    # PAN appears only inside the GSTIN here, so no standalone PAN
    assert _get(fields, "pan") is None


def test_extract_pan():
    fields = extract_fields(PAN_TEXT, "PAN_CARD")
    assert _get(fields, "pan") == "AAECS1234F"
    assert fields[0]["confidence"] > 0.9
    assert "chars" in fields[0]["evidence_location"]


def test_extract_udyam():
    assert _get(extract_fields(UDYAM_TEXT, "UDYAM_CERT"), "udyam") == "UDYAM-DL-01-0012345"


def test_extract_epfo_valid_until():
    fields = extract_fields(EPFO_TEXT, "EPFO_REG")
    assert _get(fields, "epfo_code") == "DLCPM0012345000"
    assert _get(fields, "valid_until") == "31/03/2027"


def test_extract_psara_license():
    fields = extract_fields(PSARA_TEXT, "PSARA_LICENSE")
    assert _get(fields, "license_no") == "PSARA/DL/2023/04412"
