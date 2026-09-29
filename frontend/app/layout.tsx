import type { Metadata } from "next";
import Link from "next/link";
import Script from "next/script";
import { Noto_Sans } from "next/font/google";
import { AuthProvider } from "@/lib/auth";
import { Header } from "@/components/Header";
import { AccessibilityBar } from "@/components/AccessibilityBar";
import { BackToTop } from "@/components/BackToTop";
import "./globals.css";

/* One family. Noto Sans is what Indian public service portals use, and it
   carries Devanagari for a Hindi version of this site later. */
const notoSans = Noto_Sans({
  variable: "--font-noto-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "BidSure AI — Bid compliance verification for GeM procurement",
  description:
    "Extract tender requirements, verify bidder documents against issuing authorities, and give procurement officers an evidence-backed compliance report.",
};

const footerLinks: { heading: string; links: { href: string; label: string }[] }[] = [
  {
    heading: "Use BidSure",
    links: [
      { href: "/login", label: "Sign in" },
      { href: "/register", label: "Register" },
    ],
  },
  {
    heading: "About",
    links: [
      { href: "/#how-it-works", label: "How it works" },
      { href: "/#what-is-checked", label: "What is checked" },
    ],
  },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${notoSans.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="flex min-h-full flex-col bg-gov-bg font-sans text-gov-text">
        {/* Applies the saved accessibility choices before the page paints, so a
            visitor who chose high contrast never sees a flash of the default
            theme. Must go through next/script: a raw <script> element inside an
            App Router component is not executed and logs an error. */}
        <Script id="bidsure-a11y-preferences" strategy="beforeInteractive">
          {`document.documentElement.classList.add("js");try{var c=localStorage.getItem("bidsure:contrast"),s=localStorage.getItem("bidsure:textsize");if(c==="high")document.documentElement.dataset.contrast="high";if(s&&s!=="normal")document.documentElement.dataset.textsize=s}catch(e){}`}
        </Script>
        <AuthProvider>
          <AccessibilityBar />
          <Header />
          <main id="main-content" className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
            {children}
          </main>

          <footer className="mt-8 border-t-4 border-gov-blue bg-gov-navy text-white">
            <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:grid-cols-3">
              {footerLinks.map((column) => (
                <div key={column.heading}>
                  <h2 className="text-sm font-semibold">{column.heading}</h2>
                  <ul className="mt-3 space-y-2">
                    {column.links.map((link) => (
                      <li key={link.href}>
                        <Link
                          href={link.href}
                          className="inline-flex min-h-11 items-center text-sm text-slate-200 underline underline-offset-4 hover:text-white"
                        >
                          {link.label}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}

              <div>
                <h2 className="text-sm font-semibold">Accessibility</h2>
                <p className="mt-3 max-w-[40ch] text-sm leading-relaxed text-slate-200">
                  This site aims to meet WCAG 2.1 level AA. Text size and a
                  high-contrast mode are in the bar at the top of every page, and
                  the whole site can be used with a keyboard alone.
                </p>
              </div>
            </div>

            <div className="border-t border-white/20">
              <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-4 text-sm text-slate-200">
                <p>
                  Prototype for Smart India Hackathon 2026 (PS 26100). Not an
                  official Government of India service.
                </p>
                <p>Content last reviewed: 29 September 2026</p>
              </div>
            </div>
          </footer>

          <BackToTop />
        </AuthProvider>
      </body>
    </html>
  );
}
