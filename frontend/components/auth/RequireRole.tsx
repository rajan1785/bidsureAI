"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth";

interface RequireRoleProps {
  children: React.ReactNode;
  allowedRoles: ("bidder" | "officer" | "admin")[];
  fallback?: React.ReactNode;
}

export function RequireRole({ children, allowedRoles, fallback }: RequireRoleProps) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && (!user || !allowedRoles.includes(user.role))) {
      const redirect = user?.role === "bidder" ? "/bidder" : user?.role === "officer" ? "/officer" : "/login";
      router.push(redirect);
    }
  }, [user, loading, router, allowedRoles]);

  if (loading) {
    return fallback ?? (
      <div className="flex items-center justify-center min-h-[200px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!user || !allowedRoles.includes(user.role)) {
    return fallback ?? null;
  }

  return <>{children}</>;
}

export function RequireOfficer({ children }: { children: React.ReactNode }) {
  return <RequireRole allowedRoles={["officer", "admin"]}>{children}</RequireRole>;
}

export function RequireBidder({ children }: { children: React.ReactNode }) {
  return <RequireRole allowedRoles={["bidder"]}>{children}</RequireRole>;
}

export function RequireAdmin({ children }: { children: React.ReactNode }) {
  return <RequireRole allowedRoles={["admin"]}>{children}</RequireRole>;
}