"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Building2, Settings, UserCheck } from "lucide-react";
import { DemoAccounts } from "@/components/auth/DemoAccounts";
import { RoleToggle, RoleOption } from "@/components/auth/RoleToggle";
import { DemoCredential } from "@/lib/demo-credentials";

type Role = "bidder" | "officer" | "admin";

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
    <div className="mx-auto mt-12 max-w-xl space-y-6">
      <div className="text-center">
        <span className="mx-auto mb-3 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-blue-700 text-lg font-bold text-white shadow-sm shadow-blue-900/20">B</span>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Welcome to BidSure AI</h1>
        <p className="mt-1 text-sm text-slate-500">Sign in to your procurement workspace</p>
      </div>

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
  );
}
