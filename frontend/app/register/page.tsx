"use client";

import { useState } from "react";
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
  ShieldCheck,
  User,
  UserCheck,
  Users,
} from "lucide-react";
import { RoleToggle, RoleOption } from "@/components/auth/RoleToggle";

type Role = "bidder" | "officer";

/* Same panel as the sign-in page, so the two halves of the front door read as
   one product rather than two. */
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
  { value: "bidder", label: "Bidder / Supplier", hint: "Submit & track bids", icon: Building2 },
  { value: "officer", label: "Procurement Officer", hint: "Verify bids & compliance", icon: UserCheck },
];

export default function RegisterPage() {
  const { register } = useAuth();

  const [form, setForm] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    full_name: "",
    role: "bidder" as Role,
    organization_name: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (form.password !== form.confirmPassword) {
      return setError("Passwords do not match. Retype them and try again.");
    }
    if (form.password.length < 8) {
      return setError("Password must be at least 8 characters.");
    }
    setBusy(true);
    try {
      await register({
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        role: form.role,
        organization_name: form.organization_name,
      });
      setSuccess(
        "Account created. An administrator has to approve it before you can sign in.",
      );
      setForm({
        email: "",
        password: "",
        confirmPassword: "",
        full_name: "",
        role: "bidder",
        organization_name: "",
      });
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative">
      {/* Soft page wash behind the whole view, matching sign-in. */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 -z-10 bg-gradient-to-b from-white via-slate-50 to-blue-100/50"
      />

      <div className="grid items-start gap-10 lg:grid-cols-2 lg:items-center lg:gap-16">
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

        <div className="mx-auto w-full max-w-xl">
        <div className="text-center">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Create your BidSure AI account
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Register your organisation to submit or verify bids
          </p>
        </div>

          <Card className="mt-6 border-slate-200 bg-white shadow-xl shadow-slate-900/5">
          <CardContent className="pt-1">
            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="role">Choose your role</Label>
                <RoleToggle
                  id="role"
                  value={form.role}
                  onChange={(role) => setForm({ ...form, role })}
                  disabled={busy}
                  options={ROLE_OPTIONS}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="email">Email address</Label>
                <div className="relative">
                  <Mail
                    className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                    aria-hidden
                  />
                  <Input
                    id="email"
                    type="email"
                    autoComplete="username"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    required
                    placeholder="name@organization.com"
                    className="h-11 rounded-lg bg-slate-50 pl-9"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="full_name">Full name</Label>
                <div className="relative">
                  <User
                    className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                    aria-hidden
                  />
                  <Input
                    id="full_name"
                    autoComplete="name"
                    value={form.full_name}
                    onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                    required
                    placeholder="Your name"
                    className="h-11 rounded-lg bg-slate-50 pl-9"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="organization_name">Organisation name</Label>
                <div className="relative">
                  <Building2
                    className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                    aria-hidden
                  />
                  <Input
                    id="organization_name"
                    autoComplete="organization"
                    value={form.organization_name}
                    onChange={(e) => setForm({ ...form, organization_name: e.target.value })}
                    required
                    placeholder="University of Delhi"
                    className="h-11 rounded-lg bg-slate-50 pl-9"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock
                    className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                    aria-hidden
                  />
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    required
                    aria-describedby="password-help"
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
                <p id="password-help" className="text-xs text-slate-500">
                  At least 8 characters.
                </p>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="confirmPassword">Confirm password</Label>
                <div className="relative">
                  <Lock
                    className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                    aria-hidden
                  />
                  <Input
                    id="confirmPassword"
                    type={showConfirm ? "text" : "password"}
                    autoComplete="new-password"
                    value={form.confirmPassword}
                    onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
                    required
                    className="h-11 rounded-lg bg-slate-50 px-9"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm((v) => !v)}
                    aria-label={showConfirm ? "Hide password" : "Show password"}
                    className="absolute right-1 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded text-slate-400 transition hover:text-slate-600"
                  >
                    {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {error && (
                <p
                  role="alert"
                  className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
                >
                  {error.replace(/^Error: /, "")}
                </p>
              )}

              {success && (
                <p
                  role="status"
                  className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800"
                >
                  {success}
                </p>
              )}

              <Button
                type="submit"
                disabled={busy}
                className="h-11 w-full rounded-lg bg-blue-700 text-sm font-semibold hover:bg-blue-800"
              >
                {busy ? "Creating account…" : "Create account"}
              </Button>
            </form>

            <p className="mt-5 rounded-lg bg-slate-50 px-3 py-2 text-center text-xs text-slate-500">
              New accounts need administrator approval before the first sign-in.
            </p>

            <p className="mt-4 border-t border-slate-100 pt-4 text-center text-sm text-slate-500">
              Already have an account?{" "}
              <Link href="/login" className="font-medium text-blue-700 hover:underline">
                Sign in
              </Link>
            </p>
          </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
