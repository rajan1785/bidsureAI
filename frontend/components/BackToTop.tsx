"use client";

import { useEffect, useState } from "react";

/* Appears once the page has been scrolled past roughly one screen. Long
   public service pages are expected to offer this. */
export function BackToTop() {
  const [shown, setShown] = useState(false);

  useEffect(() => {
    let frame = 0;
    const onScroll = () => {
      if (frame) return;
      frame = requestAnimationFrame(() => {
        setShown(window.scrollY > 700);
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

  const toTop = () => {
    const reduced =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
  };

  return (
    <button
      type="button"
      onClick={toTop}
      aria-label="Back to top"
      // Hidden from the tab order until it is actually on screen.
      tabIndex={shown ? 0 : -1}
      aria-hidden={!shown}
      className={`fixed bottom-6 right-6 z-40 inline-flex h-12 w-12 items-center justify-center rounded-full border border-gov-border bg-gov-surface text-gov-blue shadow-lg transition-opacity duration-200 hover:bg-gov-blue-soft ${
        shown ? "opacity-100" : "pointer-events-none opacity-0"
      }`}
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        focusable="false"
        className="h-5 w-5"
      >
        <path d="M12 19V5M5 12l7-7 7 7" />
      </svg>
    </button>
  );
}
