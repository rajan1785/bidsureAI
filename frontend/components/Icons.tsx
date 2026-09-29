/* One icon family, hand-drawn on a 24 grid with a single 1.75 stroke so they
   read as a set. Decorative throughout: every icon sits beside its own label. */
type IconProps = { className?: string };

const base = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true as const,
  focusable: "false" as const,
};

export function DocumentIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5M9 13h6M9 17h4" />
    </svg>
  );
}

export function UploadIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
      <path d="M12 15V4M8 8l4-4 4 4" />
    </svg>
  );
}

export function ShieldCheckIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M12 3l7 3v6c0 4.2-2.8 7.8-7 9-4.2-1.2-7-4.8-7-9V6z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}

export function GavelIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M5 20h9M7.5 14.5l4-4M4 12.5l5-5M9.5 6l3.5 3.5M13 4.5L17.5 9" />
      <path d="M14.5 10.5L20 16l-2 2-5.5-5.5z" />
    </svg>
  );
}

export function OfficerIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M12 3l8 3.5v5c0 4.5-3.2 8.3-8 9.5-4.8-1.2-8-5-8-9.5v-5z" />
      <circle cx="12" cy="10.5" r="2.5" />
      <path d="M8 17c.8-1.8 2.3-2.8 4-2.8s3.2 1 4 2.8" />
    </svg>
  );
}

export function BidderIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M4 20V7l6-3 6 3v13M4 20h16M10 20v-4h4v4" />
      <path d="M7.5 10h1M7.5 13.5h1M12.5 10h1M12.5 13.5h1" />
    </svg>
  );
}
