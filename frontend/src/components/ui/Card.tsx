import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  accent?: "danger" | "warning" | "success" | "neutral" | null;
}

const ACCENT_BORDER: Record<string, string> = {
  danger: "border-l-brand",
  warning: "border-l-chart-warning",
  success: "border-l-chart-good",
  neutral: "border-l-white/20",
};

// Card de base du dashboard : fond légèrement plus clair que la page,
// bordure subtile, coin arrondi, légère élévation au survol. `accent`
// ajoute une bordure gauche colorée (ex. sévérité d'un pattern) sans
// dupliquer le composant.
export default function Card({ children, className = "", accent = null }: CardProps) {
  const accentClass = accent ? `border-l-4 ${ACCENT_BORDER[accent]}` : "";
  return (
    <div
      className={`rounded-2xl border border-white/8 bg-bg-raised p-8 shadow-[0_1px_0_rgba(255,255,255,0.04)_inset,0_8px_24px_-12px_rgba(0,0,0,0.5)] transition-all hover:border-white/20 hover:shadow-[0_1px_0_rgba(255,255,255,0.04)_inset,0_12px_32px_-12px_rgba(0,0,0,0.6)] ${accentClass} ${className}`}
    >
      {children}
    </div>
  );
}
