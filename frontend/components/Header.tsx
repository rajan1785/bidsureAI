"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";

type NavItem = { href: string; label: string };

export function Header() {
  const { user, logout, loading } = useAuth();
  const pathname = usePathname();
  // Lifts the masthead onto a shadow once the page moves, so it reads as a
  // layer above the content rather than part of it.
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    let frame = 0;
    const onScroll = () => {
      if (frame) return;
      frame = requestAnimationFrame(() => {
        setScrolled(window.scrollY > 8);
        frame = 0;
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => {
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(frame);
    };
  }, []);

  let nav: NavItem[] = [];
  if (!loading && user) {
    if (user.role === "officer" || user.role === "admin") {
      nav = [
        { href: "/officer", label: "Dashboard" },
        { href: "/officer/tenders/new", label: "New tender" },
        { href: "/officer/audit", label: "Audit trail" },
      ];
      if (user.role === "admin") nav.push({ href: "/admin", label: "Users" });
    } else if (user.role === "bidder") {
      nav = [{ href: "/bidder", label: "Bidder portal" }];
    }
  }

  return (
    <header className="sticky top-0 z-30">
      {/* Masthead. No state emblem and no government branding: this is a
          prototype. The badge says so here, the footer says it in full. */}
      <div
        className={`border-b border-gov-border bg-gov-surface transition-shadow duration-200 ${
          scrolled ? "shadow-md" : ""
        }`}
      >
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-3 sm:px-6 sm:py-4">
          <Link href="/" className="flex items-center gap-3">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gov-blue text-lg font-bold text-gov-on-blue">
              B
            </span>
            <span>
              <span className="flex items-center gap-2">
                <span className="text-lg font-bold leading-tight text-gov-heading">
                  BidSure AI
                </span>
                <span className="rounded-full bg-gov-saffron-soft px-2 py-0.5 text-xs font-semibold text-gov-saffron-ink">
                  Prototype
                </span>
              </span>
              <span className="block text-sm leading-tight text-gov-muted">
                Bid compliance verification for GeM procurement
              </span>
            </span>
          </Link>

          {!loading && (
            <div className="flex items-center gap-3">
              {user ? (
                <>
                  <span className="hidden text-sm text-gov-muted md:inline">
                    {user.email}
                  </span>
                  <button
                    type="button"
                    onClick={logout}
                    className="inline-flex min-h-11 items-center rounded-lg border border-gov-border px-4 text-sm font-medium text-gov-heading transition hover:border-gov-blue hover:text-gov-blue"
                  >
                    Sign out
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="inline-flex min-h-11 items-center rounded-lg border border-gov-border px-4 text-sm font-medium text-gov-heading transition hover:border-gov-blue hover:text-gov-blue"
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/register"
                    className="inline-flex min-h-11 items-center rounded-lg bg-gov-blue px-4 text-sm font-semibold text-gov-on-blue transition hover:bg-gov-blue-dark"
                  >
                    Register
                  </Link>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {nav.length > 0 && (
        <nav aria-label="Main" className="bg-gov-blue">
          <ul className="mx-auto flex max-w-6xl flex-wrap px-4">
            {nav.map((item) => {
              const current = pathname === item.href;
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={current ? "page" : undefined}
                    className={`inline-flex min-h-11 items-center px-4 text-sm font-medium text-white hover:bg-white/15 ${
                      current ? "bg-white/20 underline underline-offset-4" : ""
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      )}
    </header>
  );
}
