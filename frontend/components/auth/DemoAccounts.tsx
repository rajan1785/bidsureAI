"use client";

import { Building2, Settings, UserCheck } from "lucide-react";
import { DEMO_CREDENTIALS, DemoCredential } from "@/lib/demo-credentials";

const ICONS = {
  admin: Settings,
  officer: UserCheck,
  bidder: Building2,
} as const;

/**
 * Seeded sign-in details shown under the login form. Picking one fills the
 * form fields so a reviewer can sign in without typing anything.
 */
export function DemoAccounts({ onUse }: { onUse: (credential: DemoCredential) => void }) {
  return (
    <div className="pt-5">
      <div className="flex items-center gap-3">
        <span className="h-px flex-1 bg-slate-200" />
        <p className="text-xs text-slate-500">
          Demo Accounts <span className="text-slate-400">(For testing only)</span>
        </p>
        <span className="h-px flex-1 bg-slate-200" />
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-3">
        {DEMO_CREDENTIALS.map((cred) => {
          const Icon = ICONS[cred.role];
          return (
            <div key={cred.role} className="rounded-lg border border-slate-200 bg-white p-3">
              <p className="flex items-center gap-1.5 whitespace-nowrap text-[11px] font-semibold text-slate-900">
                <Icon className="h-3.5 w-3.5 shrink-0 text-slate-500" aria-hidden />
                {cred.label}
              </p>
              <p className="mt-2 font-mono text-[10px] tracking-tighter text-slate-500" title={cred.email}>
                {cred.email}
              </p>
              <p className="font-mono text-[10px] tracking-tighter text-slate-500">{cred.password}</p>
              <button
                type="button"
                onClick={() => onUse(cred)}
                className="mt-2 w-full whitespace-nowrap rounded-md border border-slate-300 bg-white px-1 py-1 text-[11px] font-medium text-blue-700 transition hover:border-blue-400 hover:bg-blue-50"
              >
                Use Demo Account
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
