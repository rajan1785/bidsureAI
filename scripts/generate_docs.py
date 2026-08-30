"""Generate sample bidder document PDFs for the three demo companies.

All values are synthetic and line up with govt-api/seed_data.json, except the
deliberate defects: Nirmal's GST certificate shows a wrong GSTIN and their
EPFO coverage is expired; Apex has no PSARA licence document at all.

Run: python scripts/generate_docs.py
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

OUT = Path(__file__).parents[1] / "demo-assets" / "bidders"
W, H = A4


def cert(path: Path, header: str, title: str, rows: list[tuple[str, str]], footer: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    # border
    c.setLineWidth(2)
    c.rect(12 * mm, 12 * mm, W - 24 * mm, H - 24 * mm)
    c.setLineWidth(0.5)
    c.rect(14 * mm, 14 * mm, W - 28 * mm, H - 28 * mm)
    # header
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(W / 2, H - 30 * mm, header)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W / 2, H - 42 * mm, title)
    c.setLineWidth(1)
    c.line(40 * mm, H - 47 * mm, W - 40 * mm, H - 47 * mm)
    # rows
    y = H - 62 * mm
    for label, value in rows:
        c.setFont("Helvetica", 10)
        c.drawString(30 * mm, y, label)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(95 * mm, y, value)
        y -= 9 * mm
    # footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(W / 2, 25 * mm, footer)
    c.drawCentredString(W / 2, 20 * mm, "SAMPLE DOCUMENT - generated for SIH prototype demonstration only")
    c.save()


COMPANIES = {
    "A": {
        "name": "SHAKTI FACILITY SERVICES PRIVATE LIMITED",
        "gstin": "07AAECS1234F1Z5",
        "pan": "AAECS1234F",
        "udyam": "UDYAM-DL-01-0012345",
        "epfo": "DLCPM0012345000",
        "epfo_valid": "31/03/2027",
        "psara": ("PSARA/DL/2023/04412", "31/12/2026"),
        "gst_date": "12/06/2018",
    },
    "B": {
        "name": "NIRMAL SECURITY SOLUTIONS PRIVATE LIMITED",
        "gstin": "07AAFCN5678K1Z3",  # deliberate mismatch (govt record ends 1Z9)
        "pan": "AAFCN5678K",
        "udyam": "UDYAM-DL-02-0023456",
        "epfo": "DLCPM0023456000",
        "epfo_valid": "31/03/2026",  # expired
        "psara": ("PSARA/DL/2022/01199", "30/06/2027"),
        "gst_date": "03/11/2019",
    },
    "C": {
        "name": "APEX GUARDING CO PRIVATE LIMITED",
        "gstin": "07AAKCA9012M1Z7",
        "pan": "AAKCA9012M",
        "udyam": "UDYAM-DL-03-0034567",
        "epfo": "DLCPM0034567000",
        "epfo_valid": "31/03/2027",
        "psara": None,  # missing mandatory document
        "gst_date": "20/02/2017",
    },
}


def generate():
    for key, co in COMPANIES.items():
        d = OUT / key
        cert(
            d / "gst_registration_certificate.pdf",
            "Government of India - Form GST REG-06",
            "Goods and Services Tax Registration Certificate",
            [("Registration Number (GSTIN)", co["gstin"]),
             ("Legal Name", co["name"]),
             ("Trade Name", co["name"].title()),
             ("Constitution of Business", "Private Limited Company"),
             ("Date of Liability", co["gst_date"]),
             ("Type of Registration", "Regular"),
             ("State", "Delhi")],
            "This is a system generated registration certificate.",
        )
        cert(
            d / "pan_card.pdf",
            "INCOME TAX DEPARTMENT - GOVT. OF INDIA",
            "Permanent Account Number Card",
            [("Permanent Account Number", co["pan"]),
             ("Name", co["name"]),
             ("Category", "Company"),
             ("Date of Incorporation", co["gst_date"])],
            "Income Tax Department, Government of India",
        )
        cert(
            d / "udyam_registration.pdf",
            "Ministry of Micro, Small and Medium Enterprises (MSME)",
            "Udyam Registration Certificate",
            [("Udyam Registration Number", co["udyam"]),
             ("Name of Enterprise", co["name"]),
             ("Type of Enterprise", "Small"),
             ("Major Activity", "Services")],
            "Udyam Registration Portal, Ministry of MSME",
        )
        cert(
            d / "epfo_registration.pdf",
            "Employees' Provident Fund Organisation",
            "Establishment Registration Certificate",
            [("Establishment Code", co["epfo"]),
             ("Establishment Name", co["name"]),
             ("Coverage Status", "Active"),
             ("Valid Until", co["epfo_valid"])],
            "EPFO, Ministry of Labour and Employment",
        )
        if co["psara"]:
            lic, valid = co["psara"]
            cert(
                d / "psara_licence.pdf",
                "Government of NCT of Delhi - Home Department",
                "Licence under the Private Security Agencies (Regulation) Act, 2005",
                [("License No", lic),
                 ("Agency Name", co["name"]),
                 ("Area of Operation", "NCT of Delhi"),
                 ("Valid upto", valid)],
                "Controlling Authority, PSARA, Govt of NCT of Delhi",
            )
        print(f"Bidder {key}: {len(list(d.glob('*.pdf')))} documents in {d}")


if __name__ == "__main__":
    generate()
