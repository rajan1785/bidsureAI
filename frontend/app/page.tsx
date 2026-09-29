"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { VerificationIllustration } from "@/components/Illustration";
import { Reveal } from "@/components/Reveal";
import { CountUp } from "@/components/CountUp";
import {
  BidderIcon,
  DocumentIcon,
  GavelIcon,
  OfficerIcon,
  ShieldCheckIcon,
  UploadIcon,
} from "@/components/Icons";

const stats = [
  { figure: 40, label: "clauses in a typical tender" },
  { figure: 15, label: "documents per bidder" },
  { figure: 4, label: "government records checked" },
  { figure: 0, label: "automatic rejections" },
];

const steps = [
  {
    Icon: DocumentIcon,
    title: "Tender is read",
    detail:
      "BidSure turns the tender notice into a checklist of requirements, citing the rulebook behind each one. Nothing runs until the officer approves it.",
  },
  {
    Icon: UploadIcon,
    title: "Documents come in",
    detail:
      "Digital PDFs are read from their text layer. Scans go through OCR that suppresses seal ink, and PAN and GSTIN misreads are corrected by position.",
  },
  {
    Icon: ShieldCheckIcon,
    title: "Records are checked",
    detail:
      "Every field is put to the authority that issued it, and cross-checked for contradictions between one document and another.",
  },
  {
    Icon: GavelIcon,
    title: "Officer decides",
    detail:
      "A score, the risks and a recommendation, each line traceable to its source. The decision and its audit trail belong to the officer.",
  },
];

const checks = [
  { source: "GSTN", verified: "GSTIN validity, registration status and legal name" },
  { source: "Income Tax", verified: "PAN validity and the name it is held in" },
  { source: "Udyam", verified: "MSE registration number and enterprise category" },
  { source: "MCA", verified: "Company standing and director details" },
];

const notices = [
  {
    date: "29 September 2026",
    text: "Demo data is reset periodically. Documents uploaded to the prototype are not retained.",
  },
  {
    date: "28 September 2026",
    text: "Sample tender and bidder documents are available for testing.",
  },
  {
    date: "26 September 2026",
    text: "Record checks run against a mock API in this prototype, not live government systems.",
  },
];

export default function Home() {
  const { user, loading } = useAuth();

  if (loading) {
    return <p className="py-16 text-center text-gov-muted">Loading…</p>;
  }

  if (user) {
    const isOfficer = user.role === "officer" || user.role === "admin";
    const cards: { href: string; label: string; detail: string; Icon: typeof DocumentIcon }[] = [];

    if (isOfficer) {
      cards.push({
        href: "/officer",
        label: "Officer dashboard",
        detail: "Tenders in review, bids awaiting a decision, and the audit trail.",
        Icon: OfficerIcon,
      });
      cards.push({
        href: "/officer/tenders/new",
        label: "Create a tender",
        detail: "Upload a notice and approve the requirements taken from it.",
        Icon: UploadIcon,
      });
    }
    if (user.role === "bidder") {
      cards.push({
        href: "/bidder",
        label: "Bidder portal",
        detail: "Your firm, your documents, and the bids you have submitted.",
        Icon: BidderIcon,
      });
    }
    if (user.role === "admin") {
      cards.push({
        href: "/admin",
        label: "Manage users",
        detail: "Approve registrations and set roles for your organisation.",
        Icon: ShieldCheckIcon,
      });
    }

    return (
      <div className="py-4">
        <h1 className="text-2xl font-bold text-gov-heading sm:text-3xl">
          Welcome, {user.full_name || user.email}
        </h1>
        <p className="mt-2 text-gov-muted">Signed in as {user.role}.</p>

        <h2 className="mt-8 text-lg font-semibold text-gov-heading">Where to next</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          {cards.map(({ href, label, detail, Icon }) => (
            <Link
              key={href}
              href={href}
              className="group rounded-xl border border-gov-border bg-gov-surface p-5 shadow-sm transition hover:border-gov-blue hover:shadow-md"
            >
              <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-gov-blue-soft text-gov-blue">
                <Icon className="h-6 w-6" />
              </span>
              <span className="mt-4 block font-semibold text-gov-heading group-hover:text-gov-blue">
                {label}
              </span>
              <span className="mt-1 block text-sm leading-relaxed text-gov-muted">{detail}</span>
            </Link>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-12 py-4">
      {/* Hero */}
      <section className="overflow-hidden rounded-2xl border border-gov-border bg-gov-blue-soft">
        <div className="grid items-center gap-8 p-6 sm:p-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,26rem)] lg:gap-12">
          <div>
            <p className="inline-flex items-center gap-2 rounded-full border border-gov-border bg-gov-surface px-3 py-1 text-sm font-medium text-gov-blue">
              <ShieldCheckIcon className="h-4 w-4" />
              Built for GeM procurement
            </p>
            <h1 className="mt-4 text-3xl font-bold leading-tight text-gov-heading sm:text-4xl lg:text-[2.75rem]">
              Verify every bid against the record.
            </h1>
            <p className="mt-4 max-w-[58ch] text-base leading-7 text-gov-text">
              An officer checks ten to fifteen documents per bidder by hand. BidSure
              reads the tender, verifies each document against the authority that
              issued it, and returns an evidence-backed report. The decision stays
              with the officer.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link
                href="/login?redirect=/officer"
                className="inline-flex min-h-12 items-center rounded-lg bg-gov-blue px-6 font-semibold text-gov-on-blue shadow-sm transition hover:bg-gov-blue-dark"
              >
                Sign in as officer
              </Link>
              <Link
                href="/login?redirect=/bidder"
                className="inline-flex min-h-12 items-center rounded-lg border border-gov-border bg-gov-surface px-6 font-semibold text-gov-heading transition hover:border-gov-blue hover:text-gov-blue"
              >
                Sign in as bidder
              </Link>
            </div>
          </div>
          <VerificationIllustration className="mx-auto h-auto w-full max-w-md" />
        </div>
      </section>

      {/* Stats */}
      <Reveal as="section" aria-label="BidSure at a glance">
        <dl className="grid grid-cols-2 divide-gov-border overflow-hidden rounded-2xl border border-gov-border bg-gov-surface shadow-sm sm:grid-cols-4 sm:divide-x">
          {stats.map((stat) => (
            <div key={stat.label} className="border-b border-gov-border p-5 text-center sm:border-b-0">
              <dt className="sr-only">{stat.label}</dt>
              <dd>
                <span className="block text-3xl font-bold tabular-nums text-gov-blue">
                  <CountUp value={stat.figure} />
                </span>
                <span className="mt-1 block text-sm leading-snug text-gov-muted">
                  {stat.label}
                </span>
              </dd>
            </div>
          ))}
        </dl>
      </Reveal>

      {/* Path selection */}
      <Reveal as="section">
        <h2 className="text-xl font-bold text-gov-heading sm:text-2xl">
          Choose how you want to continue
        </h2>
        <div className="mt-5 grid gap-5 sm:grid-cols-2">
          <div className="rounded-2xl border border-gov-border bg-gov-surface p-6 shadow-sm">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-gov-blue-soft text-gov-blue">
              <OfficerIcon className="h-6 w-6" />
            </span>
            <h3 className="mt-4 text-lg font-semibold text-gov-heading">
              I am a procurement officer
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-gov-muted">
              Upload a tender, approve the requirements taken from it, and work through
              bids with the evidence behind every check.
            </p>
            <Link
              href="/login?redirect=/officer"
              className="mt-5 inline-flex min-h-11 items-center rounded-lg bg-gov-blue px-5 font-medium text-gov-on-blue transition hover:bg-gov-blue-dark"
            >
              Sign in as officer
            </Link>
          </div>

          <div className="rounded-2xl border border-gov-border bg-gov-surface p-6 shadow-sm">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-gov-green-soft text-gov-green">
              <BidderIcon className="h-6 w-6" />
            </span>
            <h3 className="mt-4 text-lg font-semibold text-gov-heading">I am a bidder</h3>
            <p className="mt-2 text-sm leading-relaxed text-gov-muted">
              Register your firm, upload your documents once, and submit against an open
              tender. See what was read from each document before it goes in.
            </p>
            <Link
              href="/login?redirect=/bidder"
              className="mt-5 inline-flex min-h-11 items-center rounded-lg border border-gov-border bg-gov-surface px-5 font-medium text-gov-heading transition hover:border-gov-blue hover:text-gov-blue"
            >
              Sign in as bidder
            </Link>
          </div>
        </div>
      </Reveal>

      {/* How it works */}
      <Reveal as="section" id="how-it-works">
        <h2 className="text-xl font-bold text-gov-heading sm:text-2xl">How it works</h2>
        <ol className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map(({ Icon, title, detail }, i) => (
            <Reveal
              as="li"
              key={title}
              delay={i * 60}
              className="rounded-2xl border border-gov-border bg-gov-surface p-5 shadow-sm"
            >
              <div className="flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-gov-blue-soft text-gov-blue">
                  <Icon className="h-6 w-6" />
                </span>
                <span className="text-sm font-semibold tabular-nums text-gov-muted">
                  Step {i + 1}
                </span>
              </div>
              <h3 className="mt-4 font-semibold text-gov-heading">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-gov-muted">{detail}</p>
            </Reveal>
          ))}
        </ol>
      </Reveal>

      {/* What is checked */}
      <Reveal as="section" id="what-is-checked">
        <h2 className="text-xl font-bold text-gov-heading sm:text-2xl">
          What is checked, and against which record
        </h2>
        <div className="mt-5 overflow-hidden rounded-2xl border border-gov-border bg-gov-surface shadow-sm">
          <table className="w-full text-left">
            <caption className="sr-only">
              Government records BidSure verifies bidder documents against
            </caption>
            <thead>
              <tr className="bg-gov-blue-soft">
                <th scope="col" className="px-5 py-3 text-sm font-semibold text-gov-heading">
                  Record
                </th>
                <th scope="col" className="px-5 py-3 text-sm font-semibold text-gov-heading">
                  What is verified
                </th>
              </tr>
            </thead>
            <tbody>
              {checks.map((row) => (
                <tr key={row.source} className="border-t border-gov-border">
                  <th
                    scope="row"
                    className="px-5 py-4 align-top font-semibold text-gov-heading"
                  >
                    {row.source}
                  </th>
                  <td className="px-5 py-4 text-gov-muted">{row.verified}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Reveal>

      {/* Notices */}
      <Reveal as="section">
        <h2 className="text-xl font-bold text-gov-heading sm:text-2xl">Notices</h2>
        <ul className="mt-5 overflow-hidden rounded-2xl border border-gov-border bg-gov-surface shadow-sm">
          {notices.map((notice, i) => (
            <li
              key={notice.date}
              className={`px-5 py-4 sm:flex sm:gap-6 ${i > 0 ? "border-t border-gov-border" : ""}`}
            >
              <span className="block shrink-0 text-sm tabular-nums text-gov-blue sm:w-44">
                {notice.date}
              </span>
              <span className="mt-1 block text-sm leading-relaxed text-gov-text sm:mt-0">
                {notice.text}
              </span>
            </li>
          ))}
        </ul>
      </Reveal>

      {/* Sample documents */}
      <Reveal as="section" className="rounded-2xl border border-gov-saffron/40 bg-gov-saffron-soft p-6 sm:flex sm:items-center sm:justify-between sm:gap-6">
        <div>
          <h2 className="text-lg font-semibold text-gov-heading">Trying the prototype?</h2>
          <p className="mt-1 max-w-[60ch] text-sm leading-relaxed text-gov-text">
            Sample tender and bidder documents are available if you need paperwork to
            upload.
          </p>
        </div>
        <a
          href="https://drive.google.com/drive/folders/1jusSpynh7eabU4uxHaunR0Of82V6NobM?usp=drive_link"
          target="_blank"
          rel="noreferrer"
          className="mt-4 inline-flex min-h-11 shrink-0 items-center rounded-lg border border-gov-saffron bg-gov-surface px-5 font-medium text-gov-saffron-ink transition hover:bg-gov-saffron-soft sm:mt-0"
        >
          Download samples (new tab)
        </a>
      </Reveal>
    </div>
  );
}
