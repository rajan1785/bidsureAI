"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, ComparisonRow, riskColor, Tender } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

export default function OfficerDashboard() {
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [rows, setRows] = useState<ComparisonRow[]>([]);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("");

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
    if (!window.confirm(`Delete "${title}" and ALL its bids and documents? This cannot be undone.`)) return;
    await api.deleteTender(id);
    if (selected === id) {
      setSelected(null);
      setRows([]);
    }
    refresh();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-bold">Officer Dashboard</h1>
        <Link href="/officer/tenders/new">
          <Button>+ New Tender</Button>
        </Link>
      </div>

      {error && <p className="text-sm text-red-600">Backend not reachable: {error}</p>}

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center justify-between">
            <span>Tenders ({tenders.length})</span>
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
                <button key={t.id} onClick={() => setSelected(t.id)}
                  className={`w-full text-left px-4 py-2.5 flex items-center gap-3 flex-wrap transition
                    ${selected === t.id ? "bg-blue-50 border-l-2 border-blue-600" : "hover:bg-slate-50"}`}>
                  <span className="font-medium text-sm flex-1 min-w-48">{t.title}</span>
                  <span className="text-xs text-slate-500 hidden sm:inline">{t.organization}</span>
                  <Badge variant={t.status === "APPROVED" ? "default" : "secondary"}>{t.status}</Badge>
                  <span className="text-xs text-slate-500">{t.requirements.length} reqs</span>
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
                  <button onClick={(e) => removeTender(e, t.id, t.title)}
                    title="Delete tender and all its bids"
                    className="text-red-500 hover:text-red-700 text-xs px-1">
                    🗑
                  </button>
                </button>
              ))}
            {tenders.length === 0 && !error && (
              <p className="text-slate-500 text-sm p-4">No tenders yet — upload one to get started.</p>
            )}
          </div>
        </CardContent>
      </Card>

      {selected !== null && (
        <Card>
          <CardHeader>
            <CardTitle>Bidder Comparison</CardTitle>
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
                      <Link href={`/officer/bids/${r.bid_id}`} className="text-blue-700 text-sm font-medium">
                        Inspect →
                      </Link>
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
