"use client";

import { use, useCallback, useEffect, useState } from "react";
import { api, BidDetail, riskColor, statusColor } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

export default function BidDrilldown({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const bidId = Number(id);
  const [bid, setBid] = useState<BidDetail | null>(null);
  const [remarks, setRemarks] = useState("");
  const [saved, setSaved] = useState("");

  const refresh = useCallback(async () => {
    setBid(await api.bidDetail(bidId));
  }, [bidId]);

  useEffect(() => { refresh(); }, [refresh]);

  // Keep polling while the verification pipeline is still running
  const running = bid !== null && !["DONE", "ERROR", "DRAFT"].includes(bid.pipeline_status);
  useEffect(() => {
    if (!running) return;
    const t = setInterval(refresh, 1200);
    return () => clearInterval(t);
  }, [running, refresh]);

  if (!bid) return <p className="text-slate-500">Loading…</p>;

  async function decide(decision: string) {
    await api.recordDecision(bidId, decision, remarks);
    setSaved(decision);
    refresh();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">{bid.bidder.legal_name}</h1>
          <p className="text-sm text-slate-500 mt-1">
            PAN {bid.bidder.pan} · GSTIN {bid.bidder.gstin} · {bid.bidder.udyam}
          </p>
        </div>
        {bid.risk && (
          <div className="text-right">
            <p className="text-3xl font-bold">{bid.risk.score}<span className="text-base font-normal text-slate-500">/100</span></p>
            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${riskColor[bid.risk.risk]}`}>
              {bid.risk.risk} Risk
            </span>
          </div>
        )}
      </div>

      {bid.pipeline_status === "DRAFT" && (
        <div className="rounded-lg border border-slate-300 bg-slate-100 p-4 text-sm text-slate-600">
          This bid has not been submitted yet — no verification has run. Results will
          appear here after the bidder submits.
        </div>
      )}
      {bid.pipeline_status === "ERROR" && (
        <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-700">
          The verification pipeline hit an error for this bid. Check the audit log for
          details, or re-submit the bid.
        </div>
      )}
      {running && (
        <div className="rounded-lg border border-blue-300 bg-blue-50 p-4 text-sm text-blue-800 flex items-center gap-3">
          <span className="inline-flex h-4 w-4 rounded-full bg-blue-600 animate-pulse" />
          Verification in progress — current stage:{" "}
          <span className="font-mono font-semibold">{bid.pipeline_status}</span>. This
          page updates automatically.
        </div>
      )}

      <Tabs defaultValue="results">
        <TabsList>
          <TabsTrigger value="results">Compliance Results</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="govt">Government Records</TabsTrigger>
          <TabsTrigger value="decision">Recommendation & Decision</TabsTrigger>
        </TabsList>

        <TabsContent value="results" className="space-y-3 pt-4">
          {bid.results.map((r) => (
            <div key={r.rule_id} className="rounded-lg border bg-white p-4 space-y-1.5">
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <p className="font-medium text-sm">{r.requirement_text}</p>
                <span className={`px-2 py-0.5 rounded border text-xs font-semibold ${statusColor[r.status]}`}>
                  {r.status}
                </span>
              </div>
              <p className="text-sm text-slate-600">{r.reason}</p>
              <p className="text-xs text-slate-400">
                Rule {r.rule_id} ({r.rule_version}){r.critical && " · CRITICAL"}
                {r.evidence?.legal_basis && (
                  <span className="ml-2 text-amber-700">
                    § {typeof r.evidence.legal_basis === "string"
                      ? r.evidence.legal_basis
                      : `${r.evidence.legal_basis.source}, ${r.evidence.legal_basis.provision}`}
                  </span>
                )}
              </p>
            </div>
          ))}
          {bid.risk && (
            <div className="rounded-lg border bg-slate-100 p-4">
              <p className="text-sm font-semibold mb-2">Score & risk factors</p>
              <ul className="text-sm text-slate-600 list-disc pl-5 space-y-1">
                {bid.risk.factors.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          )}
        </TabsContent>

        <TabsContent value="documents" className="space-y-3 pt-4">
          {bid.documents.map((d) => (
            <Card key={d.id}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center justify-between">
                  <span>{d.filename}</span>
                  <span className="flex gap-2">
                    <Badge variant="secondary">{d.doc_type}</Badge>
                    <Badge variant={d.status === "PROCESSED" ? "outline" : "destructive"}>{d.status}</Badge>
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm space-y-1">
                <p className="text-xs text-slate-400">
                  read via {d.ocr_method} (confidence {Math.round(d.ocr_confidence * 100)}%) ·
                  sha256 {d.sha256.slice(0, 16)}…
                </p>
                {d.fields.map((f, i) => (
                  <p key={i} className="flex justify-between border-b py-1 last:border-0">
                    <span className="text-slate-500">{f.field}</span>
                    <span className="font-mono">{f.value}
                      <span className="text-xs text-slate-400 ml-2">({f.evidence_location})</span>
                    </span>
                  </p>
                ))}
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="govt" className="space-y-3 pt-4">
          {bid.govt_records.map((g, i) => (
            <div key={i} className="rounded-lg border bg-white p-4">
              <div className="flex items-center justify-between">
                <p className="font-semibold text-sm">{g.source} <span className="font-mono font-normal text-slate-500">{g.identifier}</span></p>
                <span className="flex gap-2 items-center">
                  {g.mock && <Badge variant="secondary">mock source</Badge>}
                  <Badge variant={g.status === "SUCCESS" ? "outline" : "destructive"}>{g.status}</Badge>
                </span>
              </div>
              <pre className="text-xs text-slate-600 mt-2 bg-slate-50 rounded p-2 overflow-x-auto">
                {JSON.stringify(g.payload, null, 2)}
              </pre>
              <p className="text-xs text-slate-400 mt-1">retrieved {g.retrieved_at}</p>
            </div>
          ))}
        </TabsContent>

        <TabsContent value="decision" className="space-y-4 pt-4">
          {bid.recommendation && (
            <Card className="border-blue-200 bg-blue-50/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  AI Recommendation
                  <Badge variant="secondary">AI-generated decision support — not a decision</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm whitespace-pre-line">{bid.recommendation.text}</p>
                <p className="text-xs text-slate-400 mt-2">
                  model: {bid.recommendation.model} · grounded in rules {bid.recommendation.grounded_refs.join(", ")}
                </p>
              </CardContent>
            </Card>
          )}

          {bid.decision ? (
            <Card className="border-emerald-300">
              <CardContent className="pt-6">
                <p className="font-semibold">Officer decision: {bid.decision.decision}</p>
                {bid.decision.remarks && <p className="text-sm text-slate-600 mt-1">{bid.decision.remarks}</p>}
                <p className="text-xs text-slate-400 mt-2">{bid.decision.officer} · {bid.decision.timestamp}</p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Record final decision (Procurement Officer)</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Textarea placeholder="Remarks…" value={remarks} onChange={(e) => setRemarks(e.target.value)} />
                <div className="flex gap-2 flex-wrap">
                  <Button onClick={() => decide("Qualified")} className="bg-emerald-600 hover:bg-emerald-700">
                    Qualified
                  </Button>
                  <Button onClick={() => decide("Seek Clarification")} variant="outline">
                    Seek Clarification
                  </Button>
                  <Button onClick={() => decide("Disqualified")} variant="destructive">
                    Disqualified
                  </Button>
                </div>
                {saved && <p className="text-sm text-emerald-700">Decision recorded: {saved}</p>}
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
