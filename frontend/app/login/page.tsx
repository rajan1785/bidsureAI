"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { BarChart3, Building2, FileSearch, Settings, ShieldCheck, UserCheck, Users } from "lucide-react";
import { DemoAccounts } from "@/components/auth/DemoAccounts";
import { RoleToggle, RoleOption } from "@/components/auth/RoleToggle";
import { DemoCredential } from "@/lib/demo-credentials";

type Role = "bidder" | "officer" | "admin";

const HIGHLIGHTS = [
  {
    icon: FileSearch,
    title: "Intelligent document analysis",
    description: "Extract requirements from tender documents",
  },
  {
    icon: ShieldCheck,
    title: "Automated compliance verification",
    description: "Validate against government APIs and rules",
  },
  {
    icon: BarChart3,
    title: "Detailed reports & risk assessment",
    description: "Clear compliance results and insights",
  },
  {
    icon: Users,
    title: "Role-based workflow",
    description: "Admin, Officer and Bidder/Supplier access",
  },
];

const ROLE_OPTIONS: RoleOption<Role>[] = [
  { value: "admin", label: "Admin", hint: "Manage users & settings", icon: Settings },
  { value: "officer", label: "Procurement Officer", hint: "Verify bids & compliance", icon: UserCheck },
  { value: "bidder", label: "Bidder / Supplier", hint: "Submit & track bids", icon: Building2 },
];

export default function LoginPage() {
  // useSearchParams opts the subtree out of prerendering, so it needs a
  // Suspense boundary for the production build to succeed.
  return (
    <Suspense fallback={<p className="mt-12 text-center text-sm text-slate-500">Loading…</p>}>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const requestedRedirect = searchParams.get("redirect");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("bidder");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  /** Fill the form with a seeded account instead of making the user type it. */
  function useDemoAccount(credential: DemoCredential) {
    setRole(credential.role);
    setEmail(credential.email);
    setPassword(credential.password);
    setError("");
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const signedInUser = await login(email, password, role);
      const roleHome = signedInUser.role === "bidder" ? "/bidder" : signedInUser.role === "admin" ? "/admin" : "/officer";
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

  return (
    <div className="space-y-8">
      {/* Same decorative language as the landing hero: deep blue gradient
          with translucent rings bleeding past the edges. */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-950 via-blue-900 to-blue-700 px-6 py-10 text-center text-white shadow-lg shadow-blue-950/10">
        <div className="pointer-events-none absolute -right-16 -top-28 h-72 w-72 rounded-full border-[30px] border-white/5" />
        <div className="pointer-events-none absolute -bottom-36 left-10 h-64 w-64 rounded-full border-[26px] border-white/5" />
        <div className="relative mx-auto max-w-2xl space-y-3">
          <span className="mx-auto inline-flex h-11 w-11 items-center justify-center rounded-xl bg-white text-lg font-bold text-blue-800 shadow-sm">B</span>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Welcome to BidSure AI</h1>
          <p className="inline-flex items-center rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium uppercase tracking-wide text-blue-100">
            AI-powered compliance verification
          </p>
        </div>
      </section>

      <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,32rem)]">
        <aside className="hidden lg:block">
          <h2 className="text-3xl font-bold leading-tight tracking-tight text-slate-900">
            Simplifying <span className="text-blue-700">Procurement</span> with AI
          </h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Extract requirements, verify documents, and assess compliance — all in one place.
          </p>
          <ul className="mt-6 space-y-4">
            {HIGHLIGHTS.map(({ icon: Icon, title, description }) => (
              <li key={title} className="flex gap-3">
                <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-blue-50 text-blue-700">
                  <Icon className="h-4 w-4" aria-hidden />
                </span>
                <div>
                  <p className="text-sm font-semibold text-slate-900">{title}</p>
                  <p className="text-sm text-slate-500">{description}</p>
                </div>
              </li>
            ))}
          </ul>
        </aside>

        <Card className="border-slate-200 shadow-md shadow-slate-900/5">
        <CardHeader className="border-b border-slate-100 pb-4">
          <CardTitle className="text-base font-semibold">Sign in</CardTitle>
          <p className="text-sm text-slate-500">Use your registered email and password.</p>
        </CardHeader>
        <CardContent className="pt-5">
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="role">Choose your role</Label>
              <RoleToggle
                id="role"
                value={role}
                onChange={setRole}
                disabled={busy}
                options={ROLE_OPTIONS}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="name@organization.com" className="h-10 rounded-lg bg-white" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required className="h-10 rounded-lg bg-white" />
            </div>
            {error && <p role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error.replace(/^Error: /, "")}</p>}
            <Button type="submit" disabled={busy} className="h-10 w-full bg-blue-700 font-semibold hover:bg-blue-800">
              {busy ? "Signing in…" : `Continue as ${role === "officer" ? "Officer" : role === "admin" ? "Admin" : "Bidder"}`}
            </Button>
          </form>

          <DemoAccounts onUse={useDemoAccount} />

          <p className="mt-5 border-t border-slate-100 pt-4 text-center text-sm text-slate-500">
            Don't have an account? <Link href="/register" className="text-blue-700 hover:underline">Register</Link>
          </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
