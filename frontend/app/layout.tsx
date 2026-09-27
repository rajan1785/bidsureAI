import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AuthProvider } from "@/lib/auth";
import { Header } from "@/components/Header";
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

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900 font-sans">
        <AuthProvider>
          <Header />
          <main className="mx-auto max-w-6xl w-full px-4 py-8 flex-1">{children}</main>
          <footer className="border-t bg-white py-4 text-center text-xs text-slate-500">
            BidSure AI prototype — SIH 2026 · Government verifications use a mock API replica
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}