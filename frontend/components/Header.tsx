"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { ClipboardCheck, FilePlus2, LayoutDashboard, ShieldCheck } from "lucide-react";

export function Header() {
  const { user, logout, loading } = useAuth();

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
      <div className="mx-auto max-w-6xl px-4 min-h-[68px] py-2 flex items-center justify-between flex-wrap gap-x-4 gap-y-2">
        <Link href="/" className="flex items-center gap-2.5 group">
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-blue-700 text-white font-bold shadow-sm shadow-blue-900/20 group-hover:bg-blue-800 transition">
            B
          </span>
          <span className="font-semibold text-lg tracking-tight text-slate-900">
            Bid<span className="text-blue-700">Sure AI</span>
          </span>
        </Link>
        <nav className="flex items-center gap-1 sm:gap-2 text-sm font-medium text-slate-600 flex-wrap">
          {!loading && !user && (
            <>
              <Link href="/login" className="rounded-lg px-3 py-2 hover:bg-slate-100 hover:text-blue-700 transition">Login</Link>
              <Link href="/register" className="rounded-lg bg-blue-700 px-3 py-2 text-white hover:bg-blue-800 transition">Create account</Link>
            </>
          )}
          {!loading && user && user.role === "officer" && (
            <>
              <Link href="/officer" className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-blue-50 hover:text-blue-700 transition"><LayoutDashboard size={16} />Dashboard</Link>
              <Link href="/officer/audit" className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-blue-50 hover:text-blue-700 transition"><ClipboardCheck size={16} />Audit</Link>
              <Link href="/officer/tenders/new" className="flex items-center gap-2 rounded-lg bg-blue-700 px-3 py-2 text-white hover:bg-blue-800 transition"><FilePlus2 size={16} />New tender</Link>
            </>
          )}
          {!loading && user && user.role === "bidder" && (
            <Link href="/bidder" className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-blue-50 hover:text-blue-700 transition"><ClipboardCheck size={16} />Bidder portal</Link>
          )}
          {!loading && user && user.role === "admin" && (
            <>
              <Link href="/officer" className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-blue-50 hover:text-blue-700 transition"><LayoutDashboard size={16} />Dashboard</Link>
              <Link href="/admin" className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-blue-50 hover:text-blue-700 transition"><ShieldCheck size={16} />Admin</Link>
            </>
          )}
          {!loading && user && (
            <div className="ml-1 flex items-center gap-2 border-l border-slate-200 pl-3">
              <span className="hidden text-xs text-slate-500 md:inline">{user.email}</span>
              <Button variant="ghost" size="sm" className="text-slate-600 hover:text-red-700" onClick={logout}>Logout</Button>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
