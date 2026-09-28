"use client";

import { cn } from "@/lib/utils";

export type RoleOption<T extends string> = {
  value: T;
  label: string;
  hint?: string;
};

/**
 * Segmented role switch used by the login and register forms in place of a
 * dropdown, so the available roles are visible without opening a menu.
 */
export function RoleToggle<T extends string>({
  id,
  value,
  options,
  onChange,
  disabled,
}: {
  id?: string;
  value: T;
  options: RoleOption<T>[];
  onChange: (value: T) => void;
  disabled?: boolean;
}) {
  const active = options.find((o) => o.value === value);

  return (
    <div className="space-y-1.5">
      <div
        id={id}
        role="radiogroup"
        aria-label="Role"
        className="grid gap-1 rounded-lg border border-slate-200 bg-slate-100 p-1"
        style={{ gridTemplateColumns: `repeat(${options.length}, minmax(0, 1fr))` }}
      >
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={selected}
              disabled={disabled}
              onClick={() => onChange(option.value)}
              className={cn(
                "rounded-md px-2 py-2 text-xs font-semibold transition sm:text-sm",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1",
                "disabled:cursor-not-allowed disabled:opacity-60",
                selected
                  ? "bg-white text-blue-800 shadow-sm"
                  : "text-slate-600 hover:text-slate-900",
              )}
            >
              {option.label}
            </button>
          );
        })}
      </div>
      {active?.hint && <p className="text-xs text-slate-500">{active.hint}</p>}
    </div>
  );
}
