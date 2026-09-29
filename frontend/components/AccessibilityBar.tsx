"use client";

import { useEffect, useState } from "react";

type TextSize = "normal" | "large" | "largest";

const SIZES: TextSize[] = ["normal", "large", "largest"];

/* The utility strip public service portals carry: a skip link, text resizing
   and a high-contrast mode. These are real controls, not decoration — each one
   writes to the <html> element and is remembered for the next visit. */
export function AccessibilityBar() {
  const [textSize, setTextSize] = useState<TextSize>("normal");
  const [highContrast, setHighContrast] = useState(false);
  // Nothing may be written back until the saved choice has been read, or the
  // first render's defaults overwrite it.
  const [restored, setRestored] = useState(false);

  // Restore whatever the visitor chose last time.
  useEffect(() => {
    try {
      const savedSize = localStorage.getItem("bidsure:textsize") as TextSize | null;
      if (savedSize && SIZES.includes(savedSize)) setTextSize(savedSize);
      setHighContrast(localStorage.getItem("bidsure:contrast") === "high");
    } catch {
      // Private browsing or blocked storage: defaults are fine.
    }
    setRestored(true);
  }, []);

  useEffect(() => {
    if (!restored) return;
    const root = document.documentElement;
    if (textSize === "normal") delete root.dataset.textsize;
    else root.dataset.textsize = textSize;
    try {
      localStorage.setItem("bidsure:textsize", textSize);
    } catch {}
  }, [restored, textSize]);

  useEffect(() => {
    if (!restored) return;
    const root = document.documentElement;
    if (highContrast) root.dataset.contrast = "high";
    else delete root.dataset.contrast;
    try {
      localStorage.setItem("bidsure:contrast", highContrast ? "high" : "normal");
    } catch {}
  }, [restored, highContrast]);

  const step = (direction: -1 | 1) => {
    const next = SIZES.indexOf(textSize) + direction;
    if (next >= 0 && next < SIZES.length) setTextSize(SIZES[next]);
  };

  const control =
    "inline-flex min-h-11 min-w-11 items-center justify-center px-2 text-sm text-gov-text hover:bg-gov-border/60";

  return (
    <div className="border-b border-gov-border bg-gov-surface">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-end gap-x-1 px-4">
        {/* First thing in the tab order, as WCAG 2.4.1 asks. */}
        <a
          href="#main-content"
          className="sr-only mr-auto focus:not-sr-only focus:inline-flex focus:min-h-11 focus:items-center focus:bg-gov-blue focus:px-3 focus:font-medium focus:text-gov-on-blue"
        >
          Skip to main content
        </a>

        <span className="mr-1 hidden text-sm text-gov-muted sm:inline">Text size</span>
        <button
          type="button"
          onClick={() => step(-1)}
          disabled={textSize === "normal"}
          aria-label="Decrease text size"
          className={`${control} disabled:cursor-not-allowed disabled:opacity-40`}
        >
          A<span aria-hidden="true">&minus;</span>
        </button>
        <button
          type="button"
          onClick={() => setTextSize("normal")}
          aria-label="Reset text size to normal"
          className={control}
        >
          A
        </button>
        <button
          type="button"
          onClick={() => step(1)}
          disabled={textSize === "largest"}
          aria-label="Increase text size"
          className={`${control} disabled:cursor-not-allowed disabled:opacity-40`}
        >
          A<span aria-hidden="true">+</span>
        </button>

        <span className="mx-1 hidden h-5 w-px bg-gov-border sm:block" />

        <button
          type="button"
          onClick={() => setHighContrast((on) => !on)}
          aria-pressed={highContrast}
          className={control}
        >
          High contrast
        </button>
      </div>
    </div>
  );
}
