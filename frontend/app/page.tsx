"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { DemoCredentials } from "@/components/DemoCredentials";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (user) {
    const redirect = user.role === "officer" || user.role === "admin" ? "/officer" : "/bidder";
    return (
      <div className="space-y-10">
        <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-950 via-blue-900 to-blue-700 px-6 py-10 text-center text-white shadow-lg shadow-blue-950/10 sm:py-14">
          <div className="pointer-events-none absolute -right-16 -top-28 h-72 w-72 rounded-full border-[30px] border-white/5" />
          <div className="relative mx-auto max-w-2xl space-y-4">
            <p className="inline-flex items-center rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium uppercase tracking-wide text-blue-100">
              AI-powered bid compliance workspace
            </p>
            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Welcome back, <span className="text-blue-200">{user.full_name || user.email}</span>
            </h1>
            <p className="mx-auto max-w-xl text-sm leading-6 text-blue-100/90">
              Signed in as <span className="font-semibold capitalize text-white">{user.role}</span>. Pick up where you left off.
            </p>
          </div>
        </section>

        <section className="grid gap-6 sm:grid-cols-2 max-w-3xl mx-auto">
          {(user.role === "officer" || user.role === "admin") && (
            <Link href="/officer">
              <Card className="h-full border-slate-200 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-lg hover:shadow-blue-950/5">
                <CardHeader>
                  <CardTitle>Officer Dashboard</CardTitle>
                  <CardDescription>
                    Manage tenders, review bids, compare bidders and record decisions.
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-sm text-blue-700 font-medium">
                  Open dashboard →
                </CardContent>
              </Card>
            </Link>
          )}
          {(user.role === "officer" || user.role === "admin") && (
            <Link href="/officer/tenders/new">
              <Card className="h-full border-slate-200 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-lg hover:shadow-blue-950/5">
                <CardHeader>
                  <CardTitle>Create New Tender</CardTitle>
                  <CardDescription>
                    Upload a tender document and extract compliance requirements.
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-sm text-blue-700 font-medium">
                  Upload tender →
                </CardContent>
              </Card>
            </Link>
          )}
          {user.role === "bidder" && (
            <Link href="/bidder">
              <Card className="h-full border-slate-200 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-lg hover:shadow-blue-950/5">
                <CardHeader>
                  <CardTitle>Bidder Portal</CardTitle>
                  <CardDescription>
                    Register your firm, upload documents and submit bids for verification.
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-sm text-blue-700 font-medium">
                  Open portal →
                </CardContent>
              </Card>
            </Link>
          )}
          {(user.role === "admin" || user.role === "officer") && (
            <Link href="/admin">
              <Card className="hover:border-blue-600 hover:shadow-md transition cursor-pointer h-full">
                <CardHeader>
                  <CardTitle>Admin Panel</CardTitle>
                  <CardDescription>
                    Manage users and approve pending registrations.
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-sm text-blue-700 font-medium">
                  Open admin →
                </CardContent>
              </Card>
            </Link>
          )}
        </section>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-950 via-blue-900 to-blue-700 px-6 py-12 text-center text-white shadow-lg shadow-blue-950/10 sm:py-16">
        <div className="pointer-events-none absolute -right-16 -top-28 h-72 w-72 rounded-full border-[30px] border-white/5" />
        <div className="pointer-events-none absolute -bottom-36 left-10 h-64 w-64 rounded-full border-[26px] border-white/5" />
        <div className="relative mx-auto max-w-3xl space-y-5">
          <p className="inline-flex items-center rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium uppercase tracking-wide text-blue-100">
            AI-powered bid compliance verification
          </p>
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Verify every bid.<br className="sm:hidden" /> <span className="text-blue-200">Trust every decision.</span>
          </h1>
          <p className="mx-auto max-w-2xl text-sm leading-6 text-blue-100/90 sm:text-base">
            Extract tender requirements, verify bidder documents against government sources, and give procurement officers an evidence-backed compliance report—with the final decision always in human hands.
          </p>
          <div className="flex flex-wrap justify-center gap-3 pt-1">
            <Link href="/login?redirect=/officer" className="rounded-lg bg-white px-4 py-2.5 text-sm font-semibold text-blue-900 shadow-sm transition hover:bg-blue-50">Officer sign in</Link>
            <Link href="/login?redirect=/bidder" className="rounded-lg border border-white/25 bg-white/10 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-white/20">Bidder sign in</Link>
          </div>
        </div>
      </section>

      <section className="grid gap-6 sm:grid-cols-2 max-w-3xl mx-auto">
        <Link href="/login?redirect=/officer">
            <Card className="h-full border-slate-200 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-lg hover:shadow-blue-950/5">
            <CardHeader>
              <CardTitle>Procurement Officer</CardTitle>
              <CardDescription>
                Upload tenders, review AI-extracted requirements, compare bidders and
                record the final decision.
              </CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-blue-700 font-medium">
              Login as officer →
            </CardContent>
          </Card>
        </Link>
        <Link href="/login?redirect=/bidder">
            <Card className="h-full border-slate-200 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-lg hover:shadow-blue-950/5">
            <CardHeader>
              <CardTitle>Bidder</CardTitle>
              <CardDescription>
                Participate in a tender: register your firm, upload supporting documents
                and submit your bid for verification.
              </CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-blue-700 font-medium">
              Login as bidder →
            </CardContent>
          </Card>
        </Link>
      </section>

      <DemoCredentials />

      <section className="mx-auto max-w-3xl rounded-lg border border-blue-100 bg-blue-50 p-5 text-center">
        <p className="font-semibold text-slate-900">Need documents to try the prototype?</p>
        <p className="mt-1 text-sm text-slate-600">
          Download the sample tender and bidder documents from the shared test folder.
        </p>
        <a
          href="https://drive.google.com/drive/folders/1jusSpynh7eabU4uxHaunR0Of82V6NobM?usp=drive_link"
          target="_blank"
          rel="noreferrer"
          className="mt-3 inline-block font-medium text-blue-700 hover:text-blue-900 hover:underline"
        >
          Download sample documents →
        </a>
      </section>

      <section className="grid gap-4 sm:grid-cols-4 text-center text-sm">
        {[
          ["1. Tender", "Requirements extracted by AI, approved by the officer"],
          ["2. Bid Documents", "OCR + field extraction with confidence scores"],
          ["3. Verification", "Cross-checked against government source records"],
          ["4. Decision", "Score, risk & AI recommendation — officer decides"],
        ].map(([t, d]) => (
          <div key={t} className="rounded-lg border bg-white p-4">
            <p className="font-semibold">{t}</p>
            <p className="text-slate-500 mt-1">{d}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
