"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Building2, UserCheck } from "lucide-react";
import { RoleToggle } from "@/components/auth/RoleToggle";

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();

  const [form, setForm] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    full_name: "",
    role: "bidder" as "bidder" | "officer",
    organization_name: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (form.password !== form.confirmPassword) {
      return setError("Passwords do not match");
    }
    if (form.password.length < 8) {
      return setError("Password must be at least 8 characters");
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
      setSuccess("Registration successful! Your account is pending admin approval. You will be able to login once approved.");
      setForm({ email: "", password: "", confirmPassword: "", full_name: "", role: "bidder", organization_name: "" });
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-md mx-auto space-y-6 mt-16">
      <div className="text-center">
        <h1 className="text-2xl font-bold">BidSure AI</h1>
        <p className="text-slate-500 mt-1">Create your account</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Register</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required placeholder="officer@org.gov.in" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="full_name">Full Name</Label>
              <Input id="full_name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required placeholder="John Doe" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="organization_name">Organization Name</Label>
              <Input id="organization_name" value={form.organization_name} onChange={(e) => setForm({ ...form, organization_name: e.target.value })} required placeholder="University of Delhi" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="role">Role</Label>
              <RoleToggle
                id="role"
                value={form.role}
                onChange={(role) => setForm({ ...form, role })}
                disabled={busy}
                options={[
                  { value: "bidder", label: "Bidder / Supplier", hint: "Submit & track bids", icon: Building2 },
                  { value: "officer", label: "Procurement Officer", hint: "Verify bids & compliance", icon: UserCheck },
                ]}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password (min 8 chars)</Label>
              <Input id="password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input id="confirmPassword" type="password" value={form.confirmPassword} onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })} required />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            {success && <p className="text-sm text-emerald-700">{success}</p>}
            <Button type="submit" disabled={busy} className="w-full">
              {busy ? "Registering…" : "Register"}
            </Button>
          </form>
          <p className="text-center text-sm text-slate-500 mt-4">
            Already have an account? <Link href="/login" className="text-blue-700 hover:underline">Sign In</Link>
          </p>
          <p className="text-center text-xs text-slate-500 mt-2">
            Note: All accounts require admin approval before you can login.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}