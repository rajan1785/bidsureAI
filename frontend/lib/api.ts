const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function req(path: string, init?: RequestInit) {
  const r = await fetch(`${API}${path}`, init);
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
  return r.json();
}

export type LegalBasis = { source: string; provision: string; title: string };

export type DynamicRule = {
  id: number;
  rule_type: string;
  keywords: string[];
  threshold: number | null;
  unit: string;
  comparator: string;
  version: string;
  approved: boolean;
  legal_basis: LegalBasis | null;
};

export type Requirement = {
  id: number;
  text: string;
  type: string;
  priority: string;
  rule_key: string;
  approved: boolean;
  dynamic_rule: DynamicRule | null;
};

export type Tender = {
  id: number;
  title: string;
  organization: string;
  ref_no: string;
  status: string;
  ruleset_version: string;
  requirements: Requirement[];
};

export type ComparisonRow = {
  bid_id: number;
  bidder: string;
  pipeline_status: string;
  score: number | null;
  risk: string | null;
  status_counts: Record<string, number>;
  issues: string[];
  decision: string | null;
};

export type BidDetail = {
  id: number;
  tender_id: number;
  pipeline_status: string;
  submitted_at: string;
  bidder: { id: number; legal_name: string; pan: string; gstin: string; udyam: string; epfo_code: string };
  documents: {
    id: number; filename: string; doc_type: string; status: string;
    ocr_method: string; ocr_confidence: number; sha256: string;
    fields: { field: string; value: string; confidence: number; evidence_location: string }[];
  }[];
  govt_records: { source: string; identifier: string; status: string; payload: Record<string, unknown>; retrieved_at: string; mock: boolean }[];
  results: { requirement_key: string; requirement_text: string; status: string; reason: string; rule_id: string; rule_version: string; critical: boolean; evidence: { legal_basis?: LegalBasis | string } & Record<string, unknown> }[];
  risk: { score: number; risk: string; factors: string[] } | null;
  recommendation: { text: string; model: string; grounded_refs: string[] } | null;
  decision: { decision: string; remarks: string; officer: string; timestamp: string } | null;
};

export type AuditEvent = {
  id: number; actor: string; action: string; entity: string; details: string; timestamp: string;
};

export const api = {
  listTenders: (): Promise<Tender[]> => req("/tenders"),
  getTender: (id: number): Promise<Tender> => req(`/tenders/${id}`),
  createTender: (form: FormData): Promise<Tender> => req("/tenders", { method: "POST", body: form }),
  updateRequirement: (tenderId: number, reqId: number, body: Partial<Requirement>) =>
    req(`/tenders/${tenderId}/requirements/${reqId}`, {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    }),
  deleteRequirement: (tenderId: number, reqId: number) =>
    req(`/tenders/${tenderId}/requirements/${reqId}`, { method: "DELETE" }),
  approveTender: (id: number): Promise<Tender> => req(`/tenders/${id}/approve`, { method: "POST" }),

  createBidder: (body: Record<string, string>) =>
    req("/bidders", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }),
  createBid: (tender_id: number, bidder_id: number): Promise<{ id: number }> =>
    req("/bids", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ tender_id, bidder_id }) }),
  uploadDocument: (bidId: number, form: FormData) =>
    req(`/bids/${bidId}/documents`, { method: "POST", body: form }),
  submitBid: (bidId: number) => req(`/bids/${bidId}/submit`, { method: "POST" }),
  bidStatus: (bidId: number): Promise<{ pipeline_status: string }> => req(`/bids/${bidId}/status`),
  bidDetail: (bidId: number): Promise<BidDetail> => req(`/bids/${bidId}`),
  recordDecision: (bidId: number, decision: string, remarks: string) =>
    req(`/bids/${bidId}/decision`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ decision, remarks }),
    }),
  comparison: (tenderId: number): Promise<ComparisonRow[]> => req(`/tenders/${tenderId}/comparison`),
  audit: (): Promise<AuditEvent[]> => req("/audit"),
};

export const statusColor: Record<string, string> = {
  "Compliant": "bg-emerald-100 text-emerald-800 border-emerald-200",
  "Review Required": "bg-amber-100 text-amber-800 border-amber-200",
  "Non-Compliant": "bg-red-100 text-red-800 border-red-200",
  "Not Applicable": "bg-slate-100 text-slate-600 border-slate-200",
  "Verification Unavailable": "bg-violet-100 text-violet-800 border-violet-200",
};

export const riskColor: Record<string, string> = {
  Low: "bg-emerald-600 text-white",
  Medium: "bg-amber-500 text-white",
  High: "bg-red-600 text-white",
};
