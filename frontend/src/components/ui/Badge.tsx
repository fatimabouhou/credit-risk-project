import type { ReactNode } from "react";
import type { Tone } from "../../lib/ratios";

interface BadgeProps {
  tone?: Tone;
  children: ReactNode;
  size?: "sm" | "md";
}

const TONE_CLASSES: Record<Tone, string> = {
  success: "text-chart-good bg-chart-good/10 border-chart-good/30",
  warning: "text-chart-warning bg-chart-warning/10 border-chart-warning/30",
  danger: "text-brand-light bg-brand/10 border-brand/35",
  neutral: "text-text-muted bg-white/5 border-white/15",
};

export default function Badge({ tone = "neutral", children, size = "md" }: BadgeProps) {
  const sizeClass = size === "sm" ? "text-sm px-3 py-1.5" : "text-base px-4 py-2";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-semibold capitalize whitespace-nowrap ${TONE_CLASSES[tone]} ${sizeClass}`}
    >
      {children}
    </span>
  );
}
