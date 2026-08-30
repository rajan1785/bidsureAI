"use client";

import { use, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, Requirement, Tender } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

export default function TenderReview({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const tenderId = Number(id);
  const router = useRouter();
  const [tender, setTender] = useState<Tender | null>(null);
  const [editing, setEditing] = useState<number | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setTender(await api.getTender(tenderId));
  }, [tenderId]);

  useEffect(() => { refresh(); }, [refresh]);

  if (!tender) return <p className="text-slate-500">Loading…</p>;

  async function saveEdit(r: Requirement) {
    await api.updateRequirement(tenderId, r.id, { text: draft });
    setEditing(null);
    refresh();
  }

  async function remove(r: Requirement) {
    await api.deleteRequirement(tenderId, r.id);
    refresh();
  }

  async function approve() {
    setBusy(true);
    await api.approveTender(tenderId);
    router.push("/officer");
  }

  const typeBadge: Record<string, string> = {
    ELIGIBILITY: "bg-blue-100 text-blue-800",
    STATUTORY: "bg-purple-100 text-purple-800",
    TENDER_SPECIFIC: "bg-teal-100 text-teal-800",
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold">{tender.title}</h1>
        <p className="text-slate-500 text-sm mt-1">
          {tender.organization} · <Badge variant="secondary">{tender.status}</Badge>
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            AI-extracted requirements — review, edit and approve
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {tender.requirements.map((r, i) => (
            <div key={r.id} className="rounded-lg border p-3 bg-white space-y-2">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  {editing === r.id ? (
                    <Textarea value={draft} onChange={(e) => setDraft(e.target.value)} rows={2} />
                  ) : (
                    <p className="text-sm">{i + 1}. {r.text}</p>
                  )}
                </div>
                <div className="flex gap-1 shrink-0">
                  {editing === r.id ? (
                    <Button size="sm" onClick={() => saveEdit(r)}>Save</Button>
                  ) : (
                    <Button size="sm" variant="outline"
                      onClick={() => { setEditing(r.id); setDraft(r.text); }}>
                      Edit
                    </Button>
                  )}
                  <Button size="sm" variant="ghost" className="text-red-600" onClick={() => remove(r)}>
                    Remove
                  </Button>
                </div>
              </div>
              <div className="flex gap-2 text-xs">
                <span className={`px-2 py-0.5 rounded font-medium ${typeBadge[r.type] ?? "bg-slate-100"}`}>
                  {r.type}
                </span>
                <span className="px-2 py-0.5 rounded bg-slate-100 font-medium">{r.priority}</span>
                {r.rule_key && (
                  <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-500">
                    rule: {r.rule_key}
                  </span>
                )}
                {r.dynamic_rule && (
                  <span className="px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 font-medium">
                    ✨ AI-drafted rule · {r.dynamic_rule.rule_type.toLowerCase().replace("_", " ")}
                    {r.dynamic_rule.threshold !== null &&
                      ` ${r.dynamic_rule.comparator} ${r.dynamic_rule.threshold.toLocaleString()} ${r.dynamic_rule.unit}`}
                    {" · checks: "}{r.dynamic_rule.keywords.join(", ")}
                  </span>
                )}
                {r.dynamic_rule?.legal_basis && (
                  <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                    § {r.dynamic_rule.legal_basis.source}, {r.dynamic_rule.legal_basis.provision}
                  </span>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {tender.status !== "APPROVED" ? (
        <Button className="w-full" size="lg" onClick={approve} disabled={busy}>
          Approve Requirements & Create Rule Set
        </Button>
      ) : (
        <p className="text-center text-sm text-emerald-700 font-medium">
          Approved — rule set {tender.ruleset_version} active. Bids will be checked against these requirements.
        </p>
      )}
    </div>
  );
}
