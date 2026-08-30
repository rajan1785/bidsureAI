"""Synthetic training corpus for the document classifier.

Generates realistic text variants of each Indian procurement document type
(layout noise, header variations, OCR-style artifacts) so the classifier
learns document structure, not one fixed template.
"""
import random

FIRST = ["SHAKTI", "NIRMAL", "APEX", "BHARAT", "OMKAR", "SHREE", "NATIONAL",
         "PRIME", "EAGLE", "SAFEGUARD", "VIGIL", "TRIDENT", "SENTINEL"]
SECOND = ["FACILITY SERVICES", "SECURITY SOLUTIONS", "GUARDING CO", "PROTECTION SERVICES",
          "MANPOWER SERVICES", "SECURITAS", "ENTERPRISES", "SAFETY SYSTEMS"]
SUFFIX = ["PRIVATE LIMITED", "PVT LTD", "LLP", "& CO"]
STATES = [("07", "Delhi", "DL"), ("27", "Maharashtra", "MH"), ("29", "Karnataka", "KA"),
          ("09", "Uttar Pradesh", "UP"), ("06", "Haryana", "HR"), ("19", "West Bengal", "WB")]


def _company(rng):
    return f"{rng.choice(FIRST)} {rng.choice(SECOND)} {rng.choice(SUFFIX)}"


def _pan(rng):
    return ("".join(rng.choices("ABCDEFGHJKLMNPRSTUVWXYZ", k=3)) + "C"
            + rng.choice("ABCDEFGHJKLMNPRSTUVWXYZ") + f"{rng.randint(1000, 9999)}"
            + rng.choice("ABCDEFGHJKLMNPRSTUVWXYZ"))


def _date(rng):
    return f"{rng.randint(1, 28):02d}/{rng.randint(1, 12):02d}/{rng.randint(2015, 2027)}"


def _noise(rng, text):
    """OCR-ish artifacts: dropped lines, case flips, stray page furniture."""
    lines = text.splitlines()
    if rng.random() < 0.35 and len(lines) > 4:
        lines.pop(rng.randrange(len(lines)))
    if rng.random() < 0.3:
        lines.insert(0, rng.choice(["Page 1 of 2", "-- scanned copy --", "GOVERNMENT OF INDIA"]))
    if rng.random() < 0.25:
        i = rng.randrange(len(lines))
        lines[i] = lines[i].lower()
    return "\n".join(lines)


def make_doc(doc_type: str, rng) -> str:
    co = _company(rng)
    pan = _pan(rng)
    code, state, st = rng.choice(STATES)
    gstin = f"{code}{pan}1Z{rng.randint(1, 9)}"
    udyam = f"UDYAM-{st}-{rng.randint(1, 12):02d}-{rng.randint(1, 9999999):07d}"

    if doc_type == "GST_CERT":
        t = (f"{rng.choice(['Government of India', 'GOVT OF INDIA'])}\n"
             f"Form GST REG-{rng.choice(['06', '25'])}\n"
             f"{rng.choice(['Goods and Services Tax', 'GST'])} Registration Certificate\n"
             f"Registration Number (GSTIN): {gstin}\nLegal Name: {co}\n"
             f"Date of Liability: {_date(rng)}\nState: {state}\nType: Regular")
    elif doc_type == "PAN_CARD":
        t = (f"INCOME TAX DEPARTMENT {rng.choice(['GOVT. OF INDIA', 'Government of India'])}\n"
             f"Permanent Account Number {rng.choice(['Card', ''])}\n{pan}\n{co}\n"
             f"Date of Incorporation: {_date(rng)}")
    elif doc_type == "UDYAM_CERT":
        t = (f"Ministry of Micro, Small and Medium Enterprises\n"
             f"UDYAM REGISTRATION CERTIFICATE\nRegistration Number: {udyam}\n"
             f"Name of Enterprise: {co}\nType: {rng.choice(['Micro', 'Small', 'Medium'])}\n"
             f"Major Activity: Services\nMSME registration valid")
    elif doc_type == "EPFO_REG":
        t = (f"Employees' Provident Fund Organisation\n"
             f"{rng.choice(['Establishment Registration Certificate', 'Registration Intimation'])}\n"
             f"Establishment Code: {st}CPM{rng.randint(1000000, 9999999)}000\n"
             f"Establishment Name: {co}\nCoverage: {rng.choice(['Active', 'Live'])}\n"
             f"Valid Until: {_date(rng)}\nEmployees covered: {rng.randint(20, 900)}")
    elif doc_type == "PSARA_LICENSE":
        t = (f"Government of NCT of {state} - Home Department\n"
             f"Licence under the Private Security Agencies (Regulation) Act, 2005\n"
             f"License No: PSARA/{st}/{rng.randint(2018, 2026)}/{rng.randint(1000, 99999):05d}\n"
             f"Agency Name: {co}\nArea of Operation: {state}\nValid upto: {_date(rng)}")
    elif doc_type == "COMPANY_PROFILE":
        t = (f"{co}\nCompany Profile & Tender Declarations\n"
             f"Average Annual Turnover: Rs. {rng.randint(1, 20)}.{rng.randint(0, 99):02d} Crores\n"
             f"Work Experience: {rng.randint(2, 15)} years similar services\n"
             f"Earnest Money Deposit: Demand Draft for Rs. {rng.randint(1, 99)},{rng.randint(10, 99)},000 enclosed\n"
             f"Local Content: {rng.randint(20, 95)}% Make in India\n"
             f"Performance Security: Bank Guarantee will be furnished")
    else:  # OTHER — invoices, letters, random office documents
        t = rng.choice([
            f"TAX INVOICE\nInvoice No: INV-{rng.randint(100, 9999)}\n{co}\n"
            f"Total Amount: Rs. {rng.randint(1000, 900000)}\nThank you for your business",
            f"To,\nThe Manager\nSubject: Request for extension of delivery period\n"
            f"Respected Sir,\nWe request an extension of two weeks.\nRegards,\n{co}",
            f"MINUTES OF MEETING\nDate: {_date(rng)}\nAttendees: staff of {co}\n"
            f"Agenda: quarterly review and planning",
        ])
    return _noise(rng, t)


DOC_TYPES = ["GST_CERT", "PAN_CARD", "UDYAM_CERT", "EPFO_REG",
             "PSARA_LICENSE", "COMPANY_PROFILE", "OTHER"]


def build_corpus(per_class: int = 120, seed: int = 42):
    rng = random.Random(seed)
    texts, labels = [], []
    for dt in DOC_TYPES:
        for _ in range(per_class):
            texts.append(make_doc(dt, rng))
            labels.append(dt)
    return texts, labels
