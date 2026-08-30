"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, ComparisonRow, riskColor, Tender } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

export default function OfficerDashboard() {
  const [tenders, setTenders] = useState<Tender[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [rows, setRows] = useState<ComparisonRow[]>([]);
  const [error, setError] = useState("");

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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Officer Dashboard</h1>
        <Link href="/officer/tenders/new">
          <Button>+ New Tender</Button>
        </Link>
      </div>

      {error && <p className="text-sm text-red-600">Backend not reachable: {error}</p>}

      <div className="grid gap-4 sm:grid-cols-3">
        {tenders.map((t) => (
          <Card
            key={t.id}
            onClick={() => setSelected(t.id)}
            className={`cursor-pointer transition ${selected === t.id ? "border-blue-600 shadow-sm" : "hover:border-slate-400"}`}
          >
            <CardHeader className="pb-2">
              <CardTitle className="text-base leading-snug">{t.title}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-500 space-y-1">
              <p>{t.organization}</p>
              <div className="flex gap-2 items-center">
                <Badge variant={t.status === "APPROVED" ? "default" : "secondary"}>{t.status}</Badge>
                <span>{t.requirements.length} requirements</span>
              </div>
              {t.status === "REVIEW" && (
                <Link href={`/officer/tenders/${t.id}`} className="text-blue-700 font-medium">
                  Review requirements →
                </Link>
              )}
            </CardContent>
          </Card>
        ))}
        {tenders.length === 0 && !error && (
          <p className="text-slate-500 text-sm col-span-3">
            No tenders yet — upload one to get started.
          </p>
        )}
      </div>

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
                    <TableCell className="font-medium">{r.bidder}</TableCell>
                    <TableCell>
                      <Badge variant={r.pipeline_status === "DONE" ? "outline" : "secondary"}>
                        {r.pipeline_status}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-semibold">
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
                      {r.issues.length ? r.issues.join(", ") : "none"}
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
