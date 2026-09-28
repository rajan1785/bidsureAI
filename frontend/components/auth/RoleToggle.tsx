"use client";

import { Check, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export type RoleOption<T extends string> = {
  value: T;
  label: string;
  hint?: string;
  icon?: LucideIcon;
};

/**
 * Role switch used by the login and register forms in place of a dropdown,
 * so every available role is visible without opening a menu.
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
  return (
    <div
      id={id}
      role="radiogroup"
      aria-label="Role"
      className="grid gap-2"
      style={{ gridTemplateColumns: `repeat(${options.length}, minmax(0, 1fr))` }}
    >
      {options.map((option) => {
        const selected = option.value === value;
        const Icon = option.icon;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            disabled={disabled}
            onClick={() => onChange(option.value)}
            className={cn(
              "relative rounded-xl border px-2 py-3 text-center transition",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1",
              "disabled:cursor-not-allowed disabled:opacity-60",
              selected
                ? "border-blue-600 bg-blue-50/70 shadow-sm"
                : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50",
            )}
          >
            {selected && (
              <span className="absolute -right-1.5 -top-1.5 grid h-5 w-5 place-items-center rounded-full bg-blue-600 text-white">
                <Check className="h-3 w-3" aria-hidden />
              </span>
            )}
            {Icon && (
              <Icon
                className={cn("mx-auto mb-1 h-4 w-4", selected ? "text-blue-700" : "text-slate-500")}
                aria-hidden
              />
            )}
            <span
              className={cn(
                "block text-xs font-semibold leading-tight",
                selected ? "text-blue-900" : "text-slate-800",
              )}
            >
              {option.label}
            </span>
            {option.hint && (
              <span
                className={cn(
                  "mt-0.5 block text-[11px] leading-tight",
                  selected ? "text-blue-700/80" : "text-slate-500",
                )}
              >
                {option.hint}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
