import { Building2, FileText, ShieldCheck, Sparkles, SquarePen, Users } from "lucide-react";

/** Floating chip pinned around the document card. */
function Chip({ icon: Icon, className }: { icon: typeof FileText; className: string }) {
  return (
    <span
      className={`absolute grid h-9 w-9 place-items-center rounded-xl border border-slate-200/80 bg-white text-blue-600 shadow-sm ${className}`}
    >
      <Icon className="h-4 w-4" />
    </span>
  );
}

/** A bar of the mocked-up document, sized as a fraction of the card width. */
function Bar({ width, dark = false }: { width: string; dark?: boolean }) {
  return (
    <span
      className={`block h-2 rounded-full ${dark ? "bg-blue-200" : "bg-slate-200/80"}`}
      style={{ width }}
    />
  );
}

/**
 * Purely decorative illustration beside the sign-in form: a stylised
 * compliance report with verified lines, floating feature chips and the
 * shield that stands for the verification itself.
 */
export function LoginArtwork() {
  return (
    <div aria-hidden className="relative hidden h-80 lg:block">
      <div className="absolute left-4 right-0 top-6 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-lg shadow-slate-900/5">
        <div className="space-y-2">
          <Bar width="45%" dark />
          <Bar width="100%" />
          <Bar width="92%" />
          <Bar width="78%" />
        </div>
        <ul className="mt-4 space-y-2.5">
          {["88%", "80%", "84%"].map((width, i) => (
            <li key={i} className="flex items-center gap-2">
              <span className="grid h-4 w-4 shrink-0 place-items-center rounded bg-blue-600 text-white">
                <svg viewBox="0 0 12 12" className="h-2.5 w-2.5" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M2.5 6.2 4.8 8.5 9.5 3.8" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </span>
              <Bar width={width} />
            </li>
          ))}
        </ul>
      </div>

      <Chip icon={FileText} className="-left-2 top-0" />
      <Chip icon={Sparkles} className="-right-3 -top-3" />
      <Chip icon={Building2} className="-right-5 top-20" />
      <Chip icon={Users} className="-left-4 bottom-20" />
      <Chip icon={SquarePen} className="left-10 bottom-4" />

      <span className="absolute -right-2 bottom-0 grid h-20 w-20 place-items-center rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-700/30">
        <ShieldCheck className="h-9 w-9" />
      </span>
    </div>
  );
}
