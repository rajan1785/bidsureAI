import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "BidSure AI",
  description: "AI-powered bid compliance verification for GeM procurement",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900 font-sans">
        <header className="border-b bg-white sticky top-0 z-10">
          <div className="mx-auto max-w-6xl px-4 min-h-14 py-2 flex items-center justify-between flex-wrap gap-x-4 gap-y-1">
            <Link href="/" className="flex items-center gap-2">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-blue-700 text-white font-bold">
                B
              </span>
              <span className="font-semibold text-lg tracking-tight">
                Bid<span className="text-blue-700">Sure AI</span>
              </span>
            </Link>
            <nav className="flex items-center gap-3 sm:gap-5 text-xs sm:text-sm font-medium text-slate-600 flex-wrap">
              <Link href="/officer" className="hover:text-blue-700">Officer Dashboard</Link>
              <Link href="/bidder" className="hover:text-blue-700">Bidder Portal</Link>
              <Link href="/officer/audit" className="hover:text-blue-700">Audit Log</Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl w-full px-4 py-8 flex-1">{children}</main>
        <footer className="border-t bg-white py-4 text-center text-xs text-slate-500">
          BidSure AI prototype — SIH 2026
        </footer>
      </body>
    </html>
  );
}
