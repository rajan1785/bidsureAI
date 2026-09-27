"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const requestedRedirect = searchParams.get("redirect");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const signedInUser = await login(email, password);
      const roleHome = signedInUser.role === "bidder" ? "/bidder" : "/officer";
      // A stale or generic /officer redirect must never send a bidder into
      // the officer dashboard and trigger role-protected comparison requests.
      router.push(signedInUser.role === "bidder" ? roleHome : requestedRedirect || roleHome);
      router.refresh();
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
        <p className="text-slate-500 mt-1">Sign in to continue</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Login</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="officer@org.gov.in" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <Button type="submit" disabled={busy} className="w-full">
              {busy ? "Signing in…" : "Sign In"}
            </Button>
          </form>
          <p className="text-center text-sm text-slate-500 mt-4">
            Don't have an account? <Link href="/register" className="text-blue-700 hover:underline">Register</Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
