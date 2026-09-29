"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  BarChart3,
  Building2,
  Eye,
  EyeOff,
  FileSearch,
  Lock,
  Mail,
  Settings,
  ShieldCheck,
  UserCheck,
  Users,
} from "lucide-react";
import { DemoAccounts } from "@/components/auth/DemoAccounts";
import { LoginArtwork } from "@/components/auth/LoginArtwork";
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
  const [showPassword, setShowPassword] = useState(false);
  const [hint, setHint] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  /** Fill the form with a seeded account instead of making the user type it. */
  function useDemoAccount(credential: DemoCredential) {
    setRole(credential.role);
    setEmail(credential.email);
    setPassword(credential.password);
    setError("");
    setHint("");
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
    <div className="relative">
      {/* Soft page wash behind the whole sign-in view. */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 -z-10 bg-gradient-to-b from-white via-slate-50 to-blue-100/50"
      />

      <div className="text-center">
        <span className="mx-auto inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-700 text-xl font-bold text-white shadow-md shadow-blue-900/20">
          B
        </span>
        <h1 className="mt-3 text-2xl font-bold tracking-tight text-slate-900">Welcome to BidSure AI</h1>
        <p className="mt-1 text-sm text-slate-500">Sign in to your account using email and password</p>
      </div>

      <div className="mt-6 grid items-center gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,30rem)_minmax(0,1fr)]">
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
                <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-blue-100/70 text-blue-700">
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

        <Card className="border-slate-200 bg-white shadow-xl shadow-slate-900/5">
          <CardContent className="pt-1">
            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-2">
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
                <Label htmlFor="email">Email address</Label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
                  <Input
                    id="email"
                    type="email"
                    autoComplete="username"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="name@organization.com"
                    className="h-11 rounded-lg bg-slate-50 pl-9"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <Label htmlFor="password">Password</Label>
                  <button
                    type="button"
                    onClick={() => setHint("Password resets are handled by your administrator — ask them to reset it for you.")}
                    className="text-xs font-medium text-blue-700 hover:underline"
                  >
                    Forgot password?
                  </button>
                </div>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="h-11 rounded-lg bg-slate-50 px-9"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    className="absolute right-1 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded text-slate-400 transition hover:text-slate-600"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {hint && <p className="text-xs text-slate-500">{hint}</p>}
              </div>

              {error && (
                <p role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                  {error.replace(/^Error: /, "")}
                </p>
              )}

              <Button type="submit" disabled={busy} className="h-11 w-full rounded-lg bg-blue-700 text-sm font-semibold hover:bg-blue-800">
                {busy ? "Signing in…" : "Continue"}
              </Button>
            </form>

            <DemoAccounts onUse={useDemoAccount} />

            <p className="mt-5 border-t border-slate-100 pt-4 text-center text-sm text-slate-500">
              Don&apos;t have an account?{" "}
              <Link href="/register" className="font-medium text-blue-700 hover:underline">Register</Link>
            </p>
          </CardContent>
        </Card>

        <LoginArtwork />
      </div>
    </div>
  );
}
