export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";

async function req(path: string, init?: RequestInit) {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const headers = new Headers(init?.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const r = await fetch(`${API}${path}`, { ...init, headers });
  if (r.status === 401) {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    throw new Error("Session expired");
  }
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
  generated_code: string;
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

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: "bidder" | "officer" | "admin";
  organization_id: number;
  is_active: number;
  created_at: string;
};

export type RegisterData = {
  email: string;
  password: string;
  full_name: string;
  role: "bidder" | "officer";
  organization_name: string;
};

export const api = {
  // Auth
  login: (email: string, password: string) => req("/auth/login", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  }),
  register: (data: RegisterData) => req("/auth/register", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  }),
  getMe: (): Promise<User> => req("/auth/me"),

  // Tenders
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
  deleteTender: (id: number) => req(`/tenders/${id}`, { method: "DELETE" }),
  addRequirement: (tenderId: number, text: string): Promise<Tender> =>
    req(`/tenders/${tenderId}/requirements`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }),
    }),
  tenderFileUrl: (tenderId: number) => `${API}/tenders/${tenderId}/file`,
  tenderTextUrl: (tenderId: number) => `${API}/tenders/${tenderId}/extracted-text`,

  // Bidders
  createBidder: (body: Record<string, string>) =>
    req("/bidders", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }),
  listBidders: () => req("/bidders"),

  // Bids
  myBids: (): Promise<{ id: number; tender_id: number; tender_title: string; pipeline_status: string; submitted_at: string; documents: string[] }[]> => req("/bids/mine"),
  createBid: (tender_id: number, bidder_id: number): Promise<{ id: number; pipeline_status: string; existing?: boolean }> =>
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

  // Admin
  listUsers: () => req("/auth/admin/users"),
  listPendingUsers: () => req("/auth/admin/users/pending"),
  approveUser: (userId: number, isActive: boolean) =>
    req(`/auth/admin/users/${userId}/approve`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user_id: userId, is_active: isActive }),
    }),
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
