import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="space-y-10">
      <section className="text-center space-y-4 py-8">
        <p className="text-sm font-semibold text-blue-700 uppercase tracking-wide">
          AI-Powered Bid Compliance Verification
        </p>
        <h1 className="text-4xl font-bold tracking-tight">
          Verify every bid. <span className="text-blue-700">Trust every decision.</span>
        </h1>
        <p className="mx-auto max-w-2xl text-slate-600">
          BidSure AI extracts tender requirements, reads bidder documents, verifies them
          against government sources, and gives procurement officers an evidence-backed
          compliance report — with the final decision always in human hands.
        </p>
      </section>

      <section className="grid gap-6 sm:grid-cols-2 max-w-3xl mx-auto">
        <Link href="/officer">
          <Card className="hover:border-blue-600 hover:shadow-md transition cursor-pointer h-full">
            <CardHeader>
              <CardTitle>Procurement Officer</CardTitle>
              <CardDescription>
                Upload tenders, review AI-extracted requirements, compare bidders and
                record the final decision.
              </CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-blue-700 font-medium">
              Open officer dashboard →
            </CardContent>
          </Card>
        </Link>
        <Link href="/bidder">
          <Card className="hover:border-blue-600 hover:shadow-md transition cursor-pointer h-full">
            <CardHeader>
              <CardTitle>Bidder</CardTitle>
              <CardDescription>
                Participate in a tender: register your firm, upload supporting documents
                and submit your bid for verification.
              </CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-blue-700 font-medium">
              Open bidder portal →
            </CardContent>
          </Card>
        </Link>
      </section>

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
