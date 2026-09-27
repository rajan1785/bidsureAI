"use client";

import { useEffect, useRef, useState } from "react";
import { api, Tender } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AlertCircle, ArrowLeft, ArrowRight, Building2, CheckCircle2, Clock3, FileCheck2, FileText, LoaderCircle, ShieldCheck, UploadCloud } from "lucide-react";

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
  const [myBids, setMyBids] = useState<{ id: number; tender_id: number; tender_title: string; pipeline_status: string; submitted_at: string; documents: string[] }[]>([]);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    Promise.all([api.listTenders(), api.myBids()])
      .then(([ts, bids]) => { setTenders(ts.filter((t) => t.status === "APPROVED")); setMyBids(bids); })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!bidId || !pipeline || pipeline === "DONE" || pipeline === "ERROR") return;
    const t = setInterval(async () => {
      const s = await api.bidStatus(bidId);
      setPipeline(s.pipeline_status);
    }, 700);
    return () => clearInterval(t);
  }, [bidId, pipeline]);

  const ID_CHECKS: [keyof typeof form, RegExp, string][] = [
    ["pan", /^[A-Z]{5}\d{4}[A-Z]$/, "PAN should look like AAAAA9999A"],
    ["gstin", /^\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]$/, "GSTIN should be 15 characters like 07AAECS1234F1Z5"],
    ["udyam", /^UDYAM-[A-Z]{2}-\d{2}-\d{7}$/, "Udyam number should look like UDYAM-DL-01-0012345"],
    ["epfo_code", /^[A-Z]{5}\d{10}$/, "EPFO code should look like DLCPM0012345000"],
  ];

  async function register(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    for (const [key, pattern, message] of ID_CHECKS) {
      const value = form[key].trim().toUpperCase();
      if (value && !pattern.test(value)) return setError(message);
    }
    setBusy(true);
    try {
      const bidder = await api.createBidder(form);
      const bid = await api.createBid(tenderId!, bidder.id);
      setBidId(bid.id);
      if (bid.pipeline_status !== "DRAFT") {
        setPipeline(bid.pipeline_status);
        setStep(4);
      } else {
        const existing = myBids.find((b) => b.id === bid.id);
        if (existing) setUploads(existing.documents);
        setStep(3);
      }
    } catch (err) { setError(String(err)); }
    finally { setBusy(false); }
  }

  async function upload() {
    const files = fileRef.current?.files;
    if (!files?.length || !bidId) return;
    setBusy(true); setError("");
    try {
      for (const f of Array.from(files)) {
        const fd = new FormData();
        fd.append("file", f);
        await api.uploadDocument(bidId, fd);
        setUploads((u) => [...u, f.name]);
      }
      if (fileRef.current) fileRef.current.value = "";
    } catch (err) { setError(String(err)); }
    finally { setBusy(false); }
  }

  async function submit() {
    if (!bidId) return;
    setBusy(true); setError("");
    try {
      await api.submitBid(bidId);
      setPipeline("QUEUED");
      setStep(4);
    } catch (err) { setError(String(err)); }
    finally { setBusy(false); }
  }

  const stageIndex = STAGES.findIndex(([k]) => k === pipeline);

  return (
    <div className="mx-auto max-w-5xl space-y-7 pb-10">
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-950 via-blue-900 to-blue-700 px-6 py-7 text-white shadow-lg shadow-blue-950/10 sm:px-8 sm:py-9">
        <div className="pointer-events-none absolute -right-8 -top-20 h-64 w-64 rounded-full border-[28px] border-white/5" />
        <div className="pointer-events-none absolute -bottom-24 right-28 h-52 w-52 rounded-full border-[22px] border-white/5" />
        <div className="relative flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
          <div className="max-w-xl">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium text-blue-100">
              <ShieldCheck size={14} /> Secure bidder workspace
            </div>
            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Bidder Portal</h1>
            <p className="mt-2 max-w-lg text-sm leading-6 text-blue-100/90">
              Find an approved tender, submit your documents and follow verification progress in one place.
            </p>
          </div>
          <div className="flex gap-3">
            <div className="min-w-28 rounded-xl border border-white/15 bg-white/10 px-4 py-3 backdrop-blur">
              <p className="text-2xl font-semibold">{myBids.length}</p>
              <p className="mt-0.5 text-xs text-blue-100">Applications</p>
            </div>
            <div className="min-w-28 rounded-xl border border-white/15 bg-white/10 px-4 py-3 backdrop-blur">
              <p className="text-2xl font-semibold">{tenders.length}</p>
              <p className="mt-0.5 text-xs text-blue-100">Open tenders</p>
            </div>
          </div>
        </div>
      </section>

      {error && <div role="alert" className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"><AlertCircle size={17} className="mt-0.5 shrink-0" />{error}</div>}

      {step < 4 && (
        <div className="grid grid-cols-4 gap-2 sm:gap-3" aria-label="Application steps">
          {["Choose tender", "Firm details", "Documents", "Verification"].map((label, index) => {
            const number = index + 1;
            const complete = step > number;
            const active = step === number;
            return <div key={label} className={`flex items-center gap-2 rounded-xl border px-2 py-2.5 sm:px-3 ${active ? "border-blue-300 bg-blue-50 text-blue-800" : complete ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-slate-200 bg-white text-slate-400"}`}>
              <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${active ? "bg-blue-700 text-white" : complete ? "bg-emerald-600 text-white" : "bg-slate-100"}`}>{complete ? <CheckCircle2 size={15} /> : number}</span>
              <span className="hidden text-xs font-medium sm:inline">{label}</span>
            </div>;
          })}
        </div>
      )}

      {/* Step 1: choose tender */}
      {myBids.length > 0 && step === 1 && (
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between border-b border-slate-100 pb-4">
            <div><CardTitle className="text-base font-semibold">Your applications</CardTitle><p className="mt-1 text-xs text-slate-500">Track submitted bids and verification status</p></div>
            <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">{myBids.length} total</span>
          </CardHeader>
          <CardContent className="space-y-2 pt-4">
            {myBids.map((b) => <div key={b.id} className="flex flex-col justify-between gap-3 rounded-xl border border-slate-200 bg-white p-4 transition hover:border-blue-200 hover:shadow-sm sm:flex-row sm:items-center">
              <div className="flex min-w-0 items-start gap-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700"><Building2 size={19} /></span>
                <div className="min-w-0"><p className="font-semibold text-slate-900">{b.tender_title}</p><p className="mt-1 flex items-center gap-1.5 text-xs text-slate-500"><FileText size={13} />{b.documents.length} supporting documents <span className="text-slate-300">·</span> Application #{b.id}</p></div>
              </div>
              <Badge variant="outline" className={`w-fit gap-1.5 rounded-full px-3 py-1 ${b.pipeline_status === "DONE" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : b.pipeline_status === "ERROR" ? "border-red-200 bg-red-50 text-red-700" : "border-blue-200 bg-blue-50 text-blue-700"}`}>
                {b.pipeline_status === "DONE" ? <CheckCircle2 size={13} /> : <Clock3 size={13} />}{b.pipeline_status === "DONE" ? "Verified" : b.pipeline_status.replaceAll("_", " ")}
              </Badge>
            </div>)}
            {loading && <div className="flex items-center gap-2 py-4 text-sm text-slate-500"><LoaderCircle size={16} className="animate-spin" />Loading your applications…</div>}
          </CardContent>
        </Card>
      )}

      {step === 1 && (
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="border-b border-slate-100 pb-4"><CardTitle className="text-base font-semibold">Approved tenders</CardTitle><p className="text-sm text-slate-500">Choose a tender to start your application</p></CardHeader>
          <CardContent className="space-y-3 pt-4">
            {tenders.map((t) => (
              <button key={t.id}
                disabled={myBids.some((b) => b.tender_id === t.id)}
                onClick={() => { setTenderId(t.id); setStep(2); }}
                className={`group w-full rounded-xl border p-4 text-left transition ${myBids.some((b) => b.tender_id === t.id) ? "cursor-not-allowed border-slate-200 bg-slate-50/70" : "border-slate-200 bg-white hover:border-blue-300 hover:bg-blue-50/40 hover:shadow-sm focus-visible:ring-2 focus-visible:ring-blue-500"}`}>
                <div className="flex items-center gap-3">
                  <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${myBids.some((b) => b.tender_id === t.id) ? "bg-slate-100 text-slate-400" : "bg-blue-50 text-blue-700 group-hover:bg-blue-100"}`}><Building2 size={19} /></span>
                  <span className="min-w-0 flex-1"><span className="block font-semibold text-slate-900">{t.title}</span><span className="mt-1 block text-xs text-slate-500">{t.organization} <span className="mx-1 text-slate-300">·</span> {t.requirements.length} compliance requirements</span></span>
                  {myBids.some((b) => b.tender_id === t.id) ? <Badge variant="outline" className="gap-1 rounded-full border-emerald-200 bg-emerald-50 text-emerald-700"><CheckCircle2 size={13} />Applied</Badge> : <ArrowRight size={18} className="text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-blue-700" />}
                </div>
              </button>
            ))}
            {loading && <div className="flex items-center gap-2 rounded-xl border border-dashed p-6 text-sm text-slate-500"><LoaderCircle size={16} className="animate-spin" />Finding open tenders…</div>}
            {!loading && tenders.length === 0 && (
              <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/70 px-5 py-8 text-center"><Building2 size={24} className="mx-auto text-slate-400" /><p className="mt-2 font-medium text-slate-700">No tenders available right now</p><p className="mt-1 text-sm text-slate-500">Approved opportunities will appear here.</p></div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 2: register */}
      {step === 2 && (
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="border-b border-slate-100 pb-4"><CardTitle className="text-base font-semibold">Firm details</CardTitle><p className="text-sm text-slate-500">Enter your registered business information</p></CardHeader>
          <CardContent className="pt-5">
            <form onSubmit={register} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
              {([
                ["legal_name", "Legal Name", "Shakti Facility Services Pvt Ltd"],
                ["pan", "PAN", "AAECS1234F"],
                ["gstin", "GSTIN", "07AAECS1234F1Z5"],
                ["udyam", "Udyam Registration No.", "UDYAM-DL-01-0012345"],
                ["epfo_code", "EPFO Establishment Code", "DLCPM0012345000"],
              ] as const).map(([key, label, ph]) => (
                <div key={key} className={`space-y-1.5 ${key === "legal_name" ? "sm:col-span-2" : ""}`}>
                  <Label htmlFor={key} className="text-xs font-semibold text-slate-700">{label}{key === "legal_name" || key === "pan" ? <span className="ml-1 text-red-500">*</span> : <span className="ml-1 font-normal text-slate-400">(optional)</span>}</Label>
                  <Input id={key} placeholder={ph} required={key === "legal_name" || key === "pan"} className="h-10 rounded-lg bg-white"
                    value={form[key]}
                    onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
                </div>
              ))}
              </div>
              <div className="flex flex-col-reverse gap-2 border-t border-slate-100 pt-4 sm:flex-row sm:justify-between">
                <Button type="button" variant="ghost" onClick={() => setStep(1)} disabled={busy}><ArrowLeft size={16} />Back to tenders</Button>
                <Button type="submit" disabled={busy} className="bg-blue-700 px-5 hover:bg-blue-800">{busy ? <><LoaderCircle size={16} className="animate-spin" />Saving…</> : <>Save firm and continue<ArrowRight size={16} /></>}</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Step 3: documents */}
      {step === 3 && (
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="border-b border-slate-100 pb-4">
            <CardTitle className="text-base font-semibold">Supporting documents</CardTitle>
            <p className="text-sm text-slate-500">Upload readable PDF, Word, image or text files</p>
          </CardHeader>
          <CardContent className="space-y-5 pt-5">
            <div className="rounded-xl border border-dashed border-blue-200 bg-blue-50/50 p-4 sm:p-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white text-blue-700 shadow-sm"><UploadCloud size={21} /></span>
                <div className="min-w-0 flex-1"><p className="text-sm font-semibold text-slate-800">Choose documents to add</p><p className="mt-0.5 text-xs text-slate-500">GST, PAN, Udyam, EPFO, PSARA and other tender evidence</p></div>
                <Input type="file" multiple ref={fileRef} accept=".pdf,.docx,.png,.jpg,.jpeg,.txt" className="h-auto min-w-0 bg-white text-xs sm:max-w-64" />
                <Button variant="outline" onClick={upload} disabled={busy} className="border-blue-200 bg-white text-blue-800 hover:bg-blue-100">{busy ? <><LoaderCircle size={15} className="animate-spin" />Uploading</> : "Add files"}</Button>
              </div>
            </div>
            {uploads.length > 0 && (
              <ul className="grid gap-2 sm:grid-cols-2">
                {uploads.map((u, i) => (
                  <li key={`${u}-${i}`} className="flex min-w-0 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm">
                    <FileCheck2 size={17} className="shrink-0 text-emerald-600" /><span className="min-w-0 flex-1 truncate text-slate-700">{u}</span><CheckCircle2 size={14} className="shrink-0 text-emerald-600" />
                  </li>
                ))}
              </ul>
            )}
            <div className="flex flex-col-reverse gap-2 border-t border-slate-100 pt-4 sm:flex-row sm:justify-between sm:items-center">
              <Button variant="ghost" onClick={() => setStep(2)} disabled={busy}><ArrowLeft size={16} />Back</Button>
              <Button className="bg-blue-700 px-5 hover:bg-blue-800" disabled={uploads.length === 0 || busy} onClick={submit}>
                Submit for verification<ArrowRight size={16} />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 4: pipeline */}
      {step === 4 && (
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="border-b border-slate-100 pb-4"><CardTitle className="text-base font-semibold">Verification progress</CardTitle><p className="text-sm text-slate-500">We are processing your submitted documents</p></CardHeader>
          <CardContent className="space-y-2 pt-4">
            {STAGES.map(([key, label], i) => {
              const queued = pipeline === "QUEUED";
              const isDone = pipeline === "DONE" ? true : i < (queued ? 0 : stageIndex);
              const active = key === pipeline || (queued && key === "OCR");
              return (
                <div key={key}
                  className={`flex items-center gap-3 rounded-xl border px-3 py-3 text-sm transition
                    ${active ? "border-blue-200 bg-blue-50 text-blue-900" : isDone ? "border-emerald-100 bg-emerald-50/50 text-slate-600" : "border-transparent text-slate-400"}`}>
                  <span className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold
                    ${isDone ? "bg-emerald-600 text-white" : active ? "bg-blue-700 text-white" : "bg-slate-100 text-slate-500"}`}>
                    {isDone ? <CheckCircle2 size={16} /> : active && !queued ? <LoaderCircle size={15} className="animate-spin" /> : i + 1}
                  </span>
                  {label}
                </div>
              );
            })}
            {pipeline === "DONE" && (
              <p className="text-sm text-emerald-700 font-medium pt-2">
                Verification complete. Your bid is ready for Procurement Officer review.
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
