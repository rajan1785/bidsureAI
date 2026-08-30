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
  title: "ComplyGeM",
  description: "AI-powered bid compliance verification for GeM procurement",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900">
        <header className="border-b bg-white sticky top-0 z-10">
          <div className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-blue-700 text-white font-bold">
                C
              </span>
              <span className="font-semibold text-lg tracking-tight">
                Comply<span className="text-blue-700">GeM</span>
              </span>
            </Link>
            <nav className="flex items-center gap-5 text-sm font-medium text-slate-600">
              <Link href="/officer" className="hover:text-blue-700">Officer Dashboard</Link>
              <Link href="/bidder" className="hover:text-blue-700">Bidder Portal</Link>
              <Link href="/officer/audit" className="hover:text-blue-700">Audit Log</Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl w-full px-4 py-8 flex-1">{children}</main>
        <footer className="border-t bg-white py-4 text-center text-xs text-slate-500">
          ComplyGeM prototype — SIH 2026 · Government verifications use a mock API replica
        </footer>
      </body>
    </html>
  );
}
