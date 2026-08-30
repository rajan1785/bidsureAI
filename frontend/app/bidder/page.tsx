"use client";

import { useEffect, useRef, useState } from "react";
import { api, Tender } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const STAGES = [
  ["OCR", "Reading documents (OCR)"],
  ["EXTRACT", "Extracting fields"],
  ["GOVT_VERIFY", "Querying government sources"],
  ["CROSSCHECK", "Cross-checking claims"],
  ["RULES", "Evaluating compliance rules"],
  ["SCORING", "Calculating score & risk"],
  ["RECOMMEND", "Writing AI recommendation"],
  ["DONE", "Verification complete"],
] as const;

export default function BidderPortal() {
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [tenderId, setTenderId] = useState<number | null>(null);
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({
    legal_name: "", pan: "", gstin: "", udyam: "", epfo_code: "",
  });
  const [bidId, setBidId] = useState<number | null>(null);
  const [uploads, setUploads] = useState<string[]>([]);
  const [pipeline, setPipeline] = useState("");
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.listTenders()
      .then((ts) => setTenders(ts.filter((t) => t.status === "APPROVED")))
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!bidId || !pipeline || pipeline === "DONE" || pipeline === "ERROR") return;
    const t = setInterval(async () => {
      const s = await api.bidStatus(bidId);
      setPipeline(s.pipeline_status);
    }, 700);
    return () => clearInterval(t);
  }, [bidId, pipeline]);

  async function register(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const bidder = await api.createBidder(form);
      const bid = await api.createBid(tenderId!, bidder.id);
      setBidId(bid.id);
      setStep(3);
    } catch (err) { setError(String(err)); }
  }

  async function upload() {
    const files = fileRef.current?.files;
    if (!files?.length || !bidId) return;
    for (const f of Array.from(files)) {
      const fd = new FormData();
      fd.append("file", f);
      await api.uploadDocument(bidId, fd);
      setUploads((u) => [...u, f.name]);
    }
    if (fileRef.current) fileRef.current.value = "";
  }

  async function submit() {
    if (!bidId) return;
    await api.submitBid(bidId);
    setPipeline("QUEUED");
    setStep(4);
  }

  const stageIndex = STAGES.findIndex(([k]) => k === pipeline);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Bidder Portal</h1>
        <p className="text-sm text-slate-500 mt-1">
          Bid participation simulation — register, upload documents, submit, and watch the
          verification pipeline run.
        </p>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}

      {/* Step 1: choose tender */}
      {step === 1 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Step 1 — Select a tender</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {tenders.map((t) => (
              <button key={t.id}
                onClick={() => { setTenderId(t.id); setStep(2); }}
                className="w-full text-left rounded-lg border p-3 hover:border-blue-600 transition">
                <p className="font-medium text-sm">{t.title}</p>
                <p className="text-xs text-slate-500 mt-1">
                  {t.organization} · {t.requirements.length} compliance requirements
                </p>
              </button>
            ))}
            {tenders.length === 0 && (
              <p className="text-sm text-slate-500">No approved tenders open for bidding yet.</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 2: register */}
      {step === 2 && (
        <Card>
          <CardHeader><CardTitle className="text-base">Step 2 — Register your firm</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={register} className="space-y-3">
              {([
                ["legal_name", "Legal Name", "Shakti Facility Services Pvt Ltd"],
                ["pan", "PAN", "AAECS1234F"],
                ["gstin", "GSTIN", "07AAECS1234F1Z5"],
                ["udyam", "Udyam Registration No.", "UDYAM-DL-01-0012345"],
                ["epfo_code", "EPFO Establishment Code", "DLCPM0012345000"],
              ] as const).map(([key, label, ph]) => (
                <div key={key} className="space-y-1">
                  <Label htmlFor={key}>{label}</Label>
                  <Input id={key} placeholder={ph} required={key === "legal_name" || key === "pan"}
                    value={form[key]}
                    onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
                </div>
              ))}
              <Button type="submit" className="w-full">Register & Start Bid</Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Step 3: documents */}
      {step === 3 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Step 3 — Upload supporting documents</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-500">
              GST certificate, PAN card, Udyam certificate, EPFO registration, PSARA licence…
            </p>
            <div className="flex gap-2">
              <Input type="file" multiple ref={fileRef} accept=".pdf,.png,.jpg,.jpeg,.txt" />
              <Button variant="outline" onClick={upload}>Add</Button>
            </div>
            {uploads.length > 0 && (
              <ul className="text-sm space-y-1">
                {uploads.map((u, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <Badge variant="outline">uploaded</Badge>{u}
                  </li>
                ))}
              </ul>
            )}
            <Button className="w-full" disabled={uploads.length === 0} onClick={submit}>
              Submit Bid for Verification
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 4: pipeline */}
      {step === 4 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Verification pipeline</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {STAGES.map(([key, label], i) => {
              const isDone = pipeline === "DONE" ? true : i < stageIndex;
              const active = key === pipeline;
              return (
                <div key={key}
                  className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition
                    ${active ? "bg-blue-50 border border-blue-300" : isDone ? "text-slate-500" : "text-slate-400"}`}>
                  <span className={`inline-flex h-5 w-5 items-center justify-center rounded-full text-xs font-bold
                    ${isDone ? "bg-emerald-600 text-white" : active ? "bg-blue-600 text-white animate-pulse" : "bg-slate-200"}`}>
                    {isDone ? "✓" : i + 1}
                  </span>
                  {label}
                </div>
              );
            })}
            {pipeline === "DONE" && (
              <p className="text-sm text-emerald-700 font-medium pt-2">
                Verification complete. The Procurement Officer can now review your bid on the
                officer dashboard.
              </p>
            )}
            {pipeline === "ERROR" && (
              <p className="text-sm text-red-600 pt-2">Pipeline error — check backend logs.</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
