"use client";

import { useEffect, useRef, useState } from "react";

const CLAUSE_LINES = [104, 134, 164, 194, 224];

/* Hero illustration: a tender document whose clauses resolve into verified
   records, with one still open for the officer.

   The static, finished state is what the markup renders. Animation only
   engages once `hero-play` is added, which happens when the SVG is on screen
   and the visitor has not asked for reduced motion — so it can never be left
   half-drawn. */
export function VerificationIllustration({ className }: { className?: string }) {
  const ref = useRef<SVGSVGElement>(null);
  const [play, setPlay] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const reduced =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced || typeof IntersectionObserver === "undefined") return;

    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight && rect.bottom > 0) {
      setPlay(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setPlay(true);
            observer.disconnect();
          }
        }
      },
      { threshold: 0.25 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <svg
      ref={ref}
      viewBox="0 0 420 320"
      role="img"
      aria-label="A tender document beside two verified records and one decision still open"
      className={`${className ?? ""} ${play ? "hero-play" : ""}`.trim()}
    >
      {/* connectors, drawn behind the cards */}
      <g className="hd-wire">
        <path
          d="M200 150h18a10 10 0 0 1 10 10v20"
          pathLength={1}
          className="fill-none stroke-gov-blue"
          strokeWidth="2.4"
          strokeLinecap="round"
          style={{ animationDelay: "700ms" }}
        />
        <path
          d="M200 150h18a10 10 0 0 0 10-10V83"
          pathLength={1}
          className="fill-none stroke-gov-blue"
          strokeWidth="2.4"
          strokeLinecap="round"
          style={{ animationDelay: "760ms" }}
        />
        <path
          d="M200 150h28"
          pathLength={1}
          className="fill-none stroke-gov-blue"
          strokeWidth="2.4"
          strokeLinecap="round"
          style={{ animationDelay: "640ms" }}
        />
      </g>
      <circle cx="200" cy="150" r="5.5" className="hd-node fill-gov-blue" />

      {/* first verified record */}
      <g className="hd-card" style={{ animationDelay: "1000ms" }}>
        <rect x="236" y="54" width="150" height="46" rx="8" className="fill-gov-surface" />
        <rect
          x="236" y="54" width="150" height="46" rx="8"
          className="fill-none stroke-gov-border" strokeWidth="2"
        />
        <circle cx="262" cy="77" r="11" className="fill-gov-green-soft" />
        <path
          d="M257 77.5l3.5 3.5 6.5-7"
          pathLength={1}
          className="hd-check fill-none stroke-gov-green"
          strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"
          style={{ animationDelay: "1300ms" }}
        />
        <rect x="282" y="69" width="80" height="6" rx="3" className="fill-gov-border" />
        <rect x="282" y="81" width="54" height="6" rx="3" className="fill-gov-border" />
      </g>

      {/* second verified record */}
      <g className="hd-card" style={{ animationDelay: "1250ms" }}>
        <rect x="236" y="112" width="150" height="46" rx="8" className="fill-gov-surface" />
        <rect
          x="236" y="112" width="150" height="46" rx="8"
          className="fill-none stroke-gov-border" strokeWidth="2"
        />
        <circle cx="262" cy="135" r="11" className="fill-gov-green-soft" />
        <path
          d="M257 135.5l3.5 3.5 6.5-7"
          pathLength={1}
          className="hd-check fill-none stroke-gov-green"
          strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"
          style={{ animationDelay: "1550ms" }}
        />
        <rect x="282" y="127" width="64" height="6" rx="3" className="fill-gov-border" />
        <rect x="282" y="139" width="86" height="6" rx="3" className="fill-gov-border" />
      </g>

      {/* the one still open: it arrives last and keeps breathing */}
      <g className="hd-card" style={{ animationDelay: "1500ms" }}>
        <rect x="236" y="170" width="150" height="46" rx="8" className="fill-gov-saffron-soft" />
        <rect
          x="236" y="170" width="150" height="46" rx="8"
          className="fill-none stroke-gov-saffron" strokeWidth="2"
        />
        <rect
          x="252" y="183" width="20" height="20" rx="4"
          className="hd-pending fill-none stroke-gov-saffron" strokeWidth="2.4"
        />
        <rect x="282" y="185" width="72" height="6" rx="3" className="fill-gov-saffron" opacity="0.45" />
        <rect x="282" y="197" width="48" height="6" rx="3" className="fill-gov-saffron" opacity="0.45" />
      </g>

      {/* the tender document, in front */}
      <g className="hd-doc">
        <rect x="24" y="30" width="176" height="238" rx="12" className="fill-gov-surface" />
        <rect
          x="24" y="30" width="176" height="238" rx="12"
          className="fill-none stroke-gov-border" strokeWidth="2"
        />
        <rect x="24" y="30" width="176" height="46" rx="12" className="fill-gov-blue" />
        <rect x="24" y="64" width="176" height="12" className="fill-gov-blue" />
        <rect x="44" y="47" width="88" height="7" rx="3.5" className="fill-gov-on-blue" opacity="0.95" />
        <rect x="44" y="60" width="52" height="5" rx="2.5" className="fill-gov-on-blue" opacity="0.6" />

        {CLAUSE_LINES.map((y, i) => (
          <rect
            key={y}
            x="44" y={y}
            width={i % 2 === 0 ? 116 : 92}
            height="7" rx="3.5"
            className="hd-line fill-gov-border"
            style={{ animationDelay: `${300 + i * 80}ms` }}
          />
        ))}
      </g>
    </svg>
  );
}
