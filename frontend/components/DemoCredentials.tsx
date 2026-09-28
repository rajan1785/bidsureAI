"use client";

import { useState } from "react";
import { DEMO_CREDENTIALS } from "@/lib/demo-credentials";

/** Seeded sign-in details, surfaced so reviewers can try the prototype. */
export function DemoCredentials() {
  const [copied, setCopied] = useState<string | null>(null);

  async function copy(value: string, key: string) {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(key);
      setTimeout(() => setCopied((c) => (c === key ? null : c)), 1500);
    } catch {
      // Clipboard is unavailable outside a secure context; the values stay
      // visible on screen so the user can still copy them manually.
    }
  }

  return (
    <section className="mx-auto max-w-3xl rounded-lg border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-semibold text-slate-900">Test accounts</p>
        <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800">
          Demo data — not real credentials
        </span>
      </div>
      <p className="mt-1 text-sm text-slate-600">
        Sign in with any of the seeded accounts below to explore the prototype.
      </p>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {DEMO_CREDENTIALS.map((cred) => (
          <div key={cred.role} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-sm font-semibold text-slate-900">{cred.label}</p>
            <p className="mt-0.5 text-xs text-slate-500">{cred.description}</p>
            <dl className="mt-2 space-y-1 text-xs">
              <div className="flex items-center justify-between gap-2">
                <dt className="text-slate-500">Email</dt>
                <dd className="font-mono text-slate-800 truncate" title={cred.email}>{cred.email}</dd>
              </div>
              <div className="flex items-center justify-between gap-2">
                <dt className="text-slate-500">Password</dt>
                <dd className="font-mono text-slate-800">{cred.password}</dd>
              </div>
            </dl>
            <button
              type="button"
              onClick={() => copy(`${cred.email} / ${cred.password}`, cred.role)}
              className="mt-2 w-full rounded-md border border-slate-300 bg-white px-2 py-1 text-xs font-medium text-slate-700 transition hover:border-blue-300 hover:text-blue-700"
            >
              {copied === cred.role ? "Copied ✓" : "Copy email & password"}
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
