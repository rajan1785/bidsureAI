"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function NewTender() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [organization, setOrganization] = useState("");
  const [refNo, setRefNo] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return setError("Select the tender PDF first.");
    setBusy(true);
    setError("");
    try {
      const form = new FormData();
      form.append("title", title);
      form.append("organization", organization);
      form.append("ref_no", refNo);
      form.append("file", file);
      const tender = await api.createTender(form);
      router.push(`/officer/tenders/${tender.id}`);
    } catch (err) {
      setError(String(err));
      setBusy(false);
    }
  }

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Upload Tender</h1>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            The system will read the tender and extract candidate compliance requirements
            for your review.
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="title">Tender Title</Label>
              <Input id="title" value={title} onChange={(e) => setTitle(e.target.value)} required
                placeholder="Security Services Tender — University of Delhi" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="org">Organization</Label>
              <Input id="org" value={organization} onChange={(e) => setOrganization(e.target.value)}
                placeholder="University of Delhi" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="ref">Reference No.</Label>
              <Input id="ref" value={refNo} onChange={(e) => setRefNo(e.target.value)}
                placeholder="GB-SDC/074/Security Services/2024-25" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="file">Tender Document (PDF)</Label>
              <Input id="file" type="file" accept=".pdf,.txt,.docx"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)} required />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <Button type="submit" disabled={busy} className="w-full">
              {busy ? "Extracting requirements… (reading the document)" : "Upload & Extract Requirements"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
