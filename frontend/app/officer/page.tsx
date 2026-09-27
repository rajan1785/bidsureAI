"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, ComparisonRow, riskColor, Tender } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Trash2 } from "lucide-react";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

export default function OfficerDashboard() {
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [rows, setRows] = useState<ComparisonRow[]>([]);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("");
  const [deletingTender, setDeletingTender] = useState<number | null>(null);
  const [deletingBid, setDeletingBid] = useState<number | null>(null);

  const refresh = useCallback(async () => {
    try {
      const ts = await api.listTenders();
      setTenders(ts);
      const sel = selected ?? ts[0]?.id ?? null;
      if (sel !== null) {
        setSelected(sel);
        setRows(await api.comparison(sel));
      }
    } catch (e) {
      setError(String(e));
    }
  }, [selected]);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, [refresh]);

  async function removeTender(e: React.MouseEvent, id: number, title: string) {
    e.stopPropagation();
    if (!window.confirm(`Delete "${title}" and all its bids and documents? This cannot be undone.`)) return;
    setDeletingTender(id);
    setError("");
    try {
      await api.deleteTender(id);
      if (selected === id) {
        setSelected(null);
        setRows([]);
      }
      await refresh();
    } catch (e) {
      setError(`Could not delete tender: ${String(e)}`);
    } finally {
      setDeletingTender(null);
    }
  }

  async function removeBid(id: number, bidder: string) {
    if (!window.confirm(`Delete ${bidder}'s bid and its uploaded documents? The audit trail will record this action.`)) return;
    setDeletingBid(id);
    setError("");
    try {
      await api.deleteBid(id);
      setRows((current) => current.filter((row) => row.bid_id !== id));
      const refreshed = await api.comparison(selected!);
      setRows(refreshed);
    } catch (e) {
      setError(`Could not delete bid: ${String(e)}`);
    } finally {
      setDeletingBid(null);
    }
  }

  return (
    <div className="space-y-6 pb-8">
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-700">Procurement workspace</p><h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Officer Dashboard</h1><p className="mt-1 text-sm text-slate-500">Manage tender reviews and evaluate submitted bids.</p></div>
        <Link href="/officer/tenders/new">
          <Button className="h-10 gap-2 bg-blue-700 px-4 hover:bg-blue-800">+ New Tender</Button>
        </Link>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"><p className="text-xs font-medium text-slate-500">All tenders</p><p className="mt-1 text-2xl font-semibold text-slate-900">{tenders.length}</p></div>
        <div className="rounded-xl border border-amber-200/80 bg-amber-50/60 p-4 shadow-sm"><p className="text-xs font-medium text-amber-800">Needs review</p><p className="mt-1 text-2xl font-semibold text-amber-900">{tenders.filter((t) => t.status === "REVIEW").length}</p></div>
        <div className="rounded-xl border border-emerald-200/80 bg-emerald-50/60 p-4 shadow-sm"><p className="text-xs font-medium text-emerald-800">Approved and open</p><p className="mt-1 text-2xl font-semibold text-emerald-900">{tenders.filter((t) => t.status === "APPROVED").length}</p></div>
      </div>

      {error && <p className="text-sm text-red-600">Unable to load dashboard data: {error}</p>}

      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center justify-between">
            <span className="font-semibold">Tender register</span>
            {tenders.length > 4 && (
              <Input placeholder="Search tenders…" value={filter}
                onChange={(e) => setFilter(e.target.value)} className="h-8 w-56" />
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="max-h-72 overflow-y-auto divide-y">
            {tenders
              .filter((t) => !filter ||
                (t.title + t.organization + t.ref_no).toLowerCase().includes(filter.toLowerCase()))
              .map((t) => (
                <div key={t.id} role="button" tabIndex={0}
                  onClick={() => setSelected(t.id)}
                  onKeyDown={(e) => e.key === "Enter" && setSelected(t.id)}
                  className={`w-full text-left px-4 py-3 flex items-center gap-3 flex-wrap transition cursor-pointer
                    ${selected === t.id ? "bg-blue-50/80 border-l-[3px] border-blue-600" : "hover:bg-slate-50"}`}>
                  <span className="font-medium text-sm flex-1 min-w-48">{t.title}</span>
                  <span className="text-xs text-slate-500 hidden sm:inline">{t.organization}</span>
                  <Badge variant={t.status === "APPROVED" ? "default" : "secondary"}>{t.status}</Badge>
                  <span className="text-xs text-slate-500">{t.requirements.length} reqs</span>
                  {t.deadline && <span className="text-xs text-slate-500">Closes {new Date(t.deadline).toLocaleDateString()}</span>}
                  {t.status === "REVIEW" ? (
                    <Link href={`/officer/tenders/${t.id}`} onClick={(e) => e.stopPropagation()}
                      className="text-blue-700 text-xs font-medium">
                      Review →
                    </Link>
                  ) : (
                    <Link href={`/officer/tenders/${t.id}`} onClick={(e) => e.stopPropagation()}
                      className="text-slate-400 text-xs">
                      view
                    </Link>
                  )}
                  <button onClick={(e) => removeTender(e, t.id, t.title)} disabled={deletingTender === t.id}
                    title="Delete tender and all its bids"
                    className="rounded-md px-2 py-1 text-xs text-red-600 hover:bg-red-50 hover:text-red-700 disabled:opacity-50">
                    {deletingTender === t.id ? "Deleting…" : "Delete"}
                  </button>
                </div>
              ))}
            {tenders.length === 0 && !error && (
              <p className="text-slate-500 text-sm p-4">No tenders yet — upload one to get started.</p>
            )}
          </div>
        </CardContent>
      </Card>

      {selected !== null && (
        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="font-semibold">Bidder comparison</CardTitle>
            <p className="text-sm text-slate-500">{tenders.find((t) => t.id === selected)?.title ?? "Selected tender"}</p>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Bidder</TableHead>
                  <TableHead>Pipeline</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Risk</TableHead>
                  <TableHead>Issues</TableHead>
                  <TableHead>Decision</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((r) => (
                  <TableRow key={r.bid_id}>
                    <TableCell className="font-medium whitespace-nowrap">{r.bidder}</TableCell>
                    <TableCell>
                      <Badge variant={r.pipeline_status === "DONE" ? "outline" : "secondary"}>
                        {r.pipeline_status}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-semibold whitespace-nowrap">
                      {r.score !== null ? `${r.score}/100` : "—"}
                    </TableCell>
                    <TableCell>
                      {r.risk ? (
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${riskColor[r.risk]}`}>
                          {r.risk}
                        </span>
                      ) : "—"}
                    </TableCell>
                    <TableCell className="text-sm text-slate-600 max-w-56">
                      {r.issues.length
                        ? r.issues.slice(0, 3).join(", ") +
                          (r.issues.length > 3 ? ` +${r.issues.length - 3} more` : "")
                        : "none"}
                    </TableCell>
                    <TableCell>
                      {r.decision ? <Badge>{r.decision}</Badge> : <span className="text-slate-400 text-sm">pending</span>}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Link href={`/officer/bids/${r.bid_id}`} className="text-blue-700 text-sm font-medium">Inspect →</Link>
                        <button type="button" title="Delete bid and its documents" aria-label={`Delete ${r.bidder}'s bid`}
                          disabled={deletingBid === r.bid_id} onClick={() => removeBid(r.bid_id, r.bidder)}
                          className="rounded-md p-1.5 text-slate-400 transition hover:bg-red-50 hover:text-red-700 disabled:opacity-50">
                          {deletingBid === r.bid_id ? <span className="text-xs">…</span> : <Trash2 size={15} />}
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {rows.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-slate-500">
                      No bids submitted for this tender yet.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
