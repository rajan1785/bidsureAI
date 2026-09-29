"use client";

import { useEffect, useRef, useState } from "react";

type RevealTag = "div" | "section" | "li";

type RevealProps = {
  children: React.ReactNode;
  /** Renders as this element. `li` matters: a div inside <ol> is invalid. */
  as?: RevealTag;
  /** Stagger within a group, in ms. 30-50ms per item reads best. */
  delay?: number;
  className?: string;
  id?: string;
  "aria-label"?: string;
};

/* Reveals its children the first time they scroll into view.

   Three things keep this from becoming an accessibility problem: the hidden
   state only exists under html.js, which the pre-paint script sets, so content
   is never stuck invisible if the script fails; anyone asking for reduced
   motion is shown everything at once; and only opacity and transform move, so
   nothing reflows and CLS stays at zero. */
export function Reveal({
  children,
  as: Tag = "div",
  delay = 0,
  className = "",
  ...rest
}: RevealProps) {
  const ref = useRef<HTMLElement | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const reduced =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (reduced || typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }

    // Already on screen at load: show it rather than wait for a scroll that
    // may never come.
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight && rect.bottom > 0) {
      setVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setVisible(true);
            observer.disconnect();
          }
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <Tag
      // One ref callback covers every tag this renders as.
      ref={(node: HTMLElement | null) => {
        ref.current = node;
      }}
      className={`reveal ${className}`.trim()}
      data-visible={visible ? "true" : undefined}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
      {...rest}
    >
      {children}
    </Tag>
  );
}
