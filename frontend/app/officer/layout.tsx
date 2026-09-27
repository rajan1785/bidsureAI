"use client";

import { RequireOfficer } from "@/components/auth/RequireRole";

export default function OfficerLayout({ children }: { children: React.ReactNode }) {
  return <RequireOfficer>{children}</RequireOfficer>;
}