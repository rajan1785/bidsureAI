"use client";

import { RequireBidder } from "@/components/auth/RequireRole";

export default function BidderLayout({ children }: { children: React.ReactNode }) {
  return <RequireBidder>{children}</RequireBidder>;
}