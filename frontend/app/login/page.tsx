"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  BarChart3, Building2, Check, CheckSquare, Eye, EyeOff, FileText, Lock, Mail,
  Settings, ShieldCheck, Sparkles, UserCheck, Users,
} from "lucide-react";

type Role = "admin" | "officer" | "bidder";

const ROLES = [
  { value: "admin", label: "Admin", blurb: "Manage users & settings", Icon: Settings },
  { value: "officer", label: "Procurement Officer", blurb: "Verify bids & compliance", Icon: UserCheck },
  { value: "bidder", label: "Bidder / Supplier", blurb: "Submit & track bids", Icon: Users },
] as const;

// Must stay in sync with DEMO_* in backend/app/autoseed.py — these accounts are
// only created when the backend runs with AUTO_SEED=1.
const DEMO: Record<Role, { email: string; password: string }> = {
  admin: { email: "admin@demo.gov.in", password: "Demo@123" },
  officer: { email: "officer@demo.gov.in", password: "Demo@123" },
  bidder: { email: "bidder@demo.gov.in", password: "Demo@123" },
};

const FEATURES = [
  { Icon: FileText, title: "Intelligent document analysis", body: "Extract requirements from tender documents" },
  { Icon: ShieldCheck, title: "Automated compliance verification", body: "Validate against government APIs and rules" },
  { Icon: BarChart3, title: "Detailed reports & risk assessment", body: "Clear compliance results and insights" },
  { Icon: Users, title: "Role-based workflow", body: "Admin, Officer and Bidder/Supplier access" },
];

/** A stale /bidder or /admin redirect should preselect the matching role. */
function roleFromRedirect(redirect: string | null): Role {
  if (redirect?.startsWith("/bidder")) return "bidder";
  if (redirect?.startsWith("/admin")) return "admin";
  return "officer";
}

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const requestedRedirect = searchParams.get("redirect");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>(() => roleFromRedirect(requestedRedirect));
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setNotice("");
    setBusy(true);
    try {
      const signedInUser = await login(email, password, role);
      const roleHome =
        signedInUser.role === "bidder" ? "/bidder" : signedInUser.role === "admin" ? "/admin" : "/officer";
      // A stale or generic /officer redirect must never send a bidder into
      // the officer dashboard and trigger role-protected comparison requests.
      router.push(requestedRedirect && signedInUser.role !== "bidder" ? requestedRedirect : roleHome);
      router.refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  /** Fills the form only — signing in stays an explicit click on Continue. */
  function fillDemo(demoRole: Role) {
    const creds = DEMO[demoRole];
    setRole(demoRole);
    setEmail(creds.email);
    setPassword(creds.password);
    setError("");
    setNotice(`${ROLES.find((r) => r.value === demoRole)!.label} credentials filled in — press Continue to sign in.`);
  }

  return (
    // -my-8 cancels the padding on <main>; the panel then runs edge to edge and
    // fills the viewport between header (68px) and footer (~45px).
    <div className="relative left-1/2 -my-8 flex w-screen -translate-x-1/2 items-center overflow-hidden bg-gradient-to-b from-white via-blue-50/50 to-blue-100/50 lg:min-h-[calc(100vh-113px)]">
      <div className="mx-auto grid w-full max-w-[1500px] items-center gap-8 px-5 py-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,560px)] xl:grid-cols-[minmax(0,0.85fr)_minmax(0,580px)_minmax(0,0.85fr)] xl:gap-6">
        {/* Left — marketing */}
        <section className="order-2 lg:order-1">
          <h2 className="text-2xl font-bold leading-tight tracking-tight text-slate-900 xl:text-3xl">
            Simplifying <span className="text-blue-700">Procurement</span> with AI
          </h2>
          <p className="mt-2 max-w-sm text-sm leading-6 text-slate-600">
            Extract requirements, verify documents, and assess compliance — all in one place.
          </p>
          <ul className="mt-5 space-y-3.5">
            {FEATURES.map(({ Icon, title, body }) => (
              <li key={title} className="flex gap-3">
                <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-100/80 text-blue-700">
                  <Icon size={17} />
                </span>
                <div className="max-w-[17rem]">
                  <p className="text-sm font-semibold leading-5 text-slate-900">{title}</p>
                  <p className="text-xs leading-5 text-slate-600">{body}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        {/* Center — sign in */}
        <section className="order-1 lg:order-2">
          <div className="text-center">
            <span className="mx-auto mb-2 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-blue-700 text-lg font-bold text-white shadow-md shadow-blue-900/25">
              B
            </span>
            <h1 className="text-xl font-bold tracking-tight text-slate-900">Welcome to BidSure AI</h1>
            <p className="text-xs text-slate-500">AI-Powered Compliance Verification</p>
          </div>

          <div className="mt-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-xl shadow-slate-900/5">
            <h3 className="text-sm font-semibold text-slate-900">Choose your role</h3>

            {/* Role toggle — replaces the old <Select> dropdown */}
            <div role="radiogroup" aria-label="Choose your role" className="mt-2 grid grid-cols-3 gap-2">
              {ROLES.map(({ value, label, blurb, Icon }) => {
                const selected = role === value;
                return (
                  <button
                    key={value}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    onClick={() => setRole(value)}
                    className={`relative rounded-xl border px-2 py-2.5 text-center transition ${
                      selected
                        ? "border-blue-500 bg-blue-50 ring-1 ring-blue-500"
                        : "border-slate-200 bg-slate-50/70 hover:border-slate-300 hover:bg-slate-100"
                    }`}
                  >
                    {selected && (
                      <span className="absolute -right-1.5 -top-1.5 inline-flex h-4 w-4 items-center justify-center rounded-full bg-blue-600 text-white">
                        <Check size={10} strokeWidth={3} />
                      </span>
                    )}
                    <Icon size={18} className={`mx-auto ${selected ? "text-blue-700" : "text-slate-500"}`} />
                    <span className="mt-1 block text-xs font-semibold leading-4 text-slate-900">{label}</span>
                    <span className="block text-[10px] leading-[13px] text-slate-500">{blurb}</span>
                  </button>
                );
              })}
            </div>

            <form onSubmit={submit} className="mt-3.5 space-y-3">
              <div className="space-y-1">
                <Label htmlFor="email" className="text-xs">Email address</Label>
                <div className="relative">
                  <Mail size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <Input
                    id="email"
                    type="email"
                    autoComplete="username"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="name@organization.com"
                    className="h-10 rounded-xl bg-slate-50 pl-9 text-sm"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-baseline justify-between">
                  <Label htmlFor="password" className="text-xs">Password</Label>
                  <button
                    type="button"
                    onClick={() => setNotice("Password reset isn't enabled in the prototype — use a demo account below, or ask an admin to reset it.")}
                    className="text-xs text-blue-700 hover:underline"
                  >
                    Forgot password?
                  </button>
                </div>
                <div className="relative">
                  <Lock size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="h-10 rounded-xl bg-slate-50 pl-9 pr-9 text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-slate-600"
                  >
                    {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>

              {notice && (
                <p className="rounded-lg border border-blue-200 bg-blue-50 px-2.5 py-1.5 text-xs leading-5 text-blue-800">{notice}</p>
              )}
              {error && (
                <p role="alert" className="rounded-lg border border-red-200 bg-red-50 px-2.5 py-1.5 text-xs leading-5 text-red-700">
                  {error.replace(/^Error: /, "")}
                </p>
              )}

              <Button type="submit" disabled={busy} className="h-10 w-full rounded-xl bg-blue-600 text-sm font-semibold hover:bg-blue-700">
                {busy ? "Signing in…" : "Continue"}
              </Button>
            </form>

            {/* Demo accounts — fill only, never auto-submit */}
            <div className="mt-4 flex items-center gap-2.5">
              <span className="h-px flex-1 bg-slate-200" />
              <span className="text-[11px] font-medium text-slate-500">
                Demo Accounts <span className="text-slate-400">(For testing only)</span>
              </span>
              <span className="h-px flex-1 bg-slate-200" />
            </div>

            <div className="mt-2.5 grid grid-cols-3 gap-2">
              {ROLES.map(({ value, label, Icon }) => (
                <div key={value} className="rounded-xl border border-slate-200 bg-slate-50/70 p-2">
                  <div className="flex items-center gap-1.5">
                    <Icon size={13} className="shrink-0 text-blue-700" />
                    <span className="truncate text-[11px] font-semibold text-slate-900">{label}</span>
                  </div>
                  <p className="mt-1.5 truncate font-mono text-[10px] text-slate-600" title={DEMO[value].email}>
                    {DEMO[value].email}
                  </p>
                  <p className="font-mono text-[10px] text-slate-600">{DEMO[value].password}</p>
                  <button
                    type="button"
                    onClick={() => fillDemo(value)}
                    className="mt-2 w-full rounded-lg border border-blue-200 bg-white px-1.5 py-1 text-[11px] font-semibold text-blue-700 transition hover:bg-blue-50"
                  >
                    Use Demo Account
                  </button>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Right — decorative, wide screens only */}
        <section aria-hidden className="order-3 hidden xl:block">
          <div className="relative mx-auto h-[330px] w-full max-w-sm">
            <div className="absolute inset-x-8 top-5 rounded-2xl border border-blue-100 bg-white/80 p-4 shadow-lg shadow-blue-900/5 backdrop-blur">
              <div className="h-2 w-24 rounded-full bg-blue-200" />
              <div className="mt-3 space-y-2">
                {[100, 88, 94, 72].map((w, i) => (
                  <div key={i} className="h-1.5 rounded-full bg-slate-200" style={{ width: `${w}%` }} />
                ))}
              </div>
              <div className="mt-4 space-y-2">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="inline-flex h-4 w-4 items-center justify-center rounded bg-blue-100 text-blue-700">
                      <Check size={10} strokeWidth={3} />
                    </span>
                    <div className="h-1.5 flex-1 rounded-full bg-slate-200" />
                  </div>
                ))}
              </div>
            </div>

            <div className="absolute bottom-3 right-2 inline-flex h-24 w-24 items-center justify-center rounded-3xl bg-gradient-to-br from-blue-500 to-blue-700 text-white shadow-2xl shadow-blue-900/25">
              <ShieldCheck size={44} strokeWidth={1.75} />
            </div>

            {[
              { Icon: FileText, cls: "left-0 top-0" },
              { Icon: Building2, cls: "right-0 top-12" },
              { Icon: Users, cls: "bottom-20 left-0" },
              { Icon: CheckSquare, cls: "bottom-1 left-20" },
              { Icon: Sparkles, cls: "right-5 top-0" },
            ].map(({ Icon, cls }, i) => (
              <span
                key={i}
                className={`absolute ${cls} inline-flex h-9 w-9 items-center justify-center rounded-xl border border-blue-100 bg-white/90 text-blue-500 shadow-md shadow-blue-900/5`}
              >
                <Icon size={16} />
              </span>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
