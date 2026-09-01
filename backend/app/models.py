from datetime import datetime, timezone

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class Tender(Base):
    __tablename__ = "tenders"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    organization: Mapped[str] = mapped_column(String, default="")
    ref_no: Mapped[str] = mapped_column(String, default="")
    file_path: Mapped[str] = mapped_column(String, default="")
    # DRAFT -> EXTRACTING -> REVIEW (requirements ready) -> APPROVED
    status: Mapped[str] = mapped_column(String, default="DRAFT")
    ruleset_version: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[str] = mapped_column(String, default=utcnow)
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    ocr_method: Mapped[str] = mapped_column(String, default="")
    ocr_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    requirements: Mapped[list["Requirement"]] = relationship(back_populates="tender")


class Requirement(Base):
    __tablename__ = "requirements"
    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id"))
    text: Mapped[str] = mapped_column(Text)
    # ELIGIBILITY | STATUTORY | TENDER_SPECIFIC
    type: Mapped[str] = mapped_column(String, default="STATUTORY")
    priority: Mapped[str] = mapped_column(String, default="MANDATORY")  # MANDATORY | OPTIONAL
    applicability: Mapped[str] = mapped_column(String, default="ALL")
    rule_key: Mapped[str] = mapped_column(String, default="")  # links to YAML rule id
    approved: Mapped[int] = mapped_column(Integer, default=0)

    tender: Mapped["Tender"] = relationship(back_populates="requirements")


class DynamicRule(Base):
    """AI-drafted rule for a tender-specific clause no built-in rule covers.

    Drafted at tender upload, evaluated only after the officer approves the
    linked requirement. Executed by the deterministic executors in rule_forge.
    """
    __tablename__ = "dynamic_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id"))
    requirement_id: Mapped[int] = mapped_column(ForeignKey("requirements.id"))
    rule_type: Mapped[str] = mapped_column(String)  # DOC_PRESENCE | THRESHOLD | DECLARATION
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    threshold: Mapped[float] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String, default="")
    comparator: Mapped[str] = mapped_column(String, default=">=")
    weight: Mapped[int] = mapped_column(Integer, default=1)
    critical: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[str] = mapped_column(String, default="dyn-v1")
    approved: Mapped[int] = mapped_column(Integer, default=0)
    legal_basis: Mapped[dict] = mapped_column(JSON, nullable=True)
    generated_code: Mapped[str] = mapped_column(Text, default="")
    exemptions: Mapped[list] = mapped_column(JSON, default=list)


class Bidder(Base):
    __tablename__ = "bidders"
    id: Mapped[int] = mapped_column(primary_key=True)
    legal_name: Mapped[str] = mapped_column(String)
    pan: Mapped[str] = mapped_column(String, default="")
    gstin: Mapped[str] = mapped_column(String, default="")
    udyam: Mapped[str] = mapped_column(String, default="")
    epfo_code: Mapped[str] = mapped_column(String, default="")
    contact_email: Mapped[str] = mapped_column(String, default="")


class Bid(Base):
    __tablename__ = "bids"
    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id"))
    bidder_id: Mapped[int] = mapped_column(ForeignKey("bidders.id"))
    submitted_at: Mapped[str] = mapped_column(String, default="")
    # DRAFT -> then pipeline stages: OCR, EXTRACT, GOVT_VERIFY, CROSSCHECK,
    # RULES, SCORING, RECOMMEND, DONE, ERROR
    pipeline_status: Mapped[str] = mapped_column(String, default="DRAFT")

    bidder: Mapped["Bidder"] = relationship()
    documents: Mapped[list["Document"]] = relationship(back_populates="bid")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    bid_id: Mapped[int] = mapped_column(ForeignKey("bids.id"))
    doc_type: Mapped[str] = mapped_column(String, default="OTHER")
    filename: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    sha256: Mapped[str] = mapped_column(String, default="")
    ocr_method: Mapped[str] = mapped_column(String, default="")
    ocr_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String, default="UPLOADED")  # UPLOADED|PROCESSED|UNREADABLE

    bid: Mapped["Bid"] = relationship(back_populates="documents")
    fields: Mapped[list["ExtractedField"]] = relationship(back_populates="document")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    field: Mapped[str] = mapped_column(String)
    value: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    evidence_location: Mapped[str] = mapped_column(String, default="")

    document: Mapped["Document"] = relationship(back_populates="fields")


class GovtRecord(Base):
    __tablename__ = "govt_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    bid_id: Mapped[int] = mapped_column(ForeignKey("bids.id"))
    source: Mapped[str] = mapped_column(String)
    identifier: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)  # SUCCESS | UNAVAILABLE
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    retrieved_at: Mapped[str] = mapped_column(String, default=utcnow)
    mock: Mapped[int] = mapped_column(Integer, default=1)


class ComplianceResult(Base):
    __tablename__ = "compliance_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    bid_id: Mapped[int] = mapped_column(ForeignKey("bids.id"))
    requirement_key: Mapped[str] = mapped_column(String)
    requirement_text: Mapped[str] = mapped_column(Text, default="")
    # Compliant | Review Required | Non-Compliant | Not Applicable | Verification Unavailable
    status: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text, default="")
    rule_id: Mapped[str] = mapped_column(String, default="")
    rule_version: Mapped[str] = mapped_column(String, default="")
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    critical: Mapped[int] = mapped_column(Integer, default=0)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    bid_id: Mapped[int] = mapped_column(ForeignKey("bids.id"))
    score: Mapped[float] = mapped_column(Float)
    risk: Mapped[str] = mapped_column(String)  # Low | Medium | High
    factors: Mapped[list] = mapped_column(JSON, default=list)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[int] = mapped_column(primary_key=True)
    bid_id: Mapped[int] = mapped_column(ForeignKey("bids.id"))
    text: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String, default="")
    grounded_refs: Mapped[list] = mapped_column(JSON, default=list)


class OfficerDecision(Base):
    __tablename__ = "officer_decisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    bid_id: Mapped[int] = mapped_column(ForeignKey("bids.id"))
    decision: Mapped[str] = mapped_column(String)  # Qualified | Disqualified | Seek Clarification
    remarks: Mapped[str] = mapped_column(Text, default="")
    officer: Mapped[str] = mapped_column(String, default="Procurement Officer")
    timestamp: Mapped[str] = mapped_column(String, default=utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    entity: Mapped[str] = mapped_column(String)
    details: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[str] = mapped_column(String, default=utcnow)
