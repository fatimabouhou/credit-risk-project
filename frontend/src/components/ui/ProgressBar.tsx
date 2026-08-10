import type { Tone } from "../../lib/ratios";

interface ProgressBarProps {
  percent: number; // 0-100, déjà calculé par l'appelant (dépend du domaine du ratio)
  tone: Tone;
}

const TONE_FILL: Record<Tone, string> = {
  success: "bg-chart-good",
  warning: "bg-chart-warning",
  danger: "bg-brand",
  neutral: "bg-text-muted",
};

export default function ProgressBar({ percent, tone }: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, percent));
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/8">
      <div
        className={`h-full rounded-full transition-[width] duration-300 ${TONE_FILL[tone]}`}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
