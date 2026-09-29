"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";

/* useLayoutEffect warns during server rendering, so fall back to useEffect
   there. The value is only zeroed on the client, before paint. */
const useIsomorphicLayoutEffect =
  typeof window !== "undefined" ? useLayoutEffect : useEffect;

/* Counts up to `value` when it scrolls into view. Renders the final value in
   the markup, so with no JavaScript, or with reduced motion, the correct
   number is simply there. */
export function CountUp({ value, duration = 1000 }: { value: number; duration?: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [display, setDisplay] = useState(value);
  const [animate, setAnimate] = useState(false);

  useIsomorphicLayoutEffect(() => {
    const reduced =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced || typeof IntersectionObserver === "undefined") return;
    // Zero it before the browser paints, so the final value never flashes.
    setDisplay(0);
    setAnimate(true);
  }, []);

  useEffect(() => {
    const el = ref.current;
    if (!animate || !el) return;

    let frame = 0;
    let start = 0;

    const run = (now: number) => {
      if (!start) start = now;
      const progress = Math.min((now - start) / duration, 1);
      // ease-out: fast first, settles at the end
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(value * eased));
      if (progress < 1) frame = requestAnimationFrame(run);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            frame = requestAnimationFrame(run);
            observer.disconnect();
          }
        }
      },
      { threshold: 0.4 },
    );

    observer.observe(el);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [animate, value, duration]);

  return (
    <span ref={ref} className="tabular-nums">
      {display}
    </span>
  );
}
