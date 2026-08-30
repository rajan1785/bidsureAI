"use client";

import { useEffect, useState } from "react";
import { api, AuditEvent } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

const actorVariant: Record<string, "default" | "secondary" | "outline"> = {
  system: "secondary",
  officer: "default",
  bidder: "outline",
};

export default function AuditLog() {
  const [events, setEvents] = useState<AuditEvent[]>([]);

  useEffect(() => {
    const load = () => api.audit().then(setEvents).catch(() => {});
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Audit Trail</h1>
      <p className="text-sm text-slate-500">
        Every document processed, source queried, rule evaluated and officer action — with actor and timestamp.
      </p>
      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Time (UTC)</TableHead>
              <TableHead>Actor</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Entity</TableHead>
              <TableHead>Details</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {events.map((e) => (
              <TableRow key={e.id}>
                <TableCell className="text-xs text-slate-500 whitespace-nowrap">
                  {e.timestamp.replace("T", " ").slice(0, 19)}
                </TableCell>
                <TableCell><Badge variant={actorVariant[e.actor] ?? "secondary"}>{e.actor}</Badge></TableCell>
                <TableCell className="font-mono text-xs">{e.action}</TableCell>
                <TableCell className="font-mono text-xs">{e.entity}</TableCell>
                <TableCell className="text-xs text-slate-600 max-w-md truncate">{e.details}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
