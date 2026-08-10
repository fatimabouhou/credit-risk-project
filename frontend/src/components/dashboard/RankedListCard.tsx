import Card from "../ui/Card";
import SectionHeader from "../ui/SectionHeader";
import type { Tone } from "../../lib/ratios";

export interface RankedListRow {
  label: string;
  value: string;
  percent: number; // 0-100, position de la mini-barre
  tone?: Tone;
}

interface RankedListCardProps {
  title: string;
  subtitle?: string;
  rows: RankedListRow[];
}

const TONE_BAR: Record<Tone, string> = {
  success: "bg-chart-good",
  warning: "bg-chart-warning",
  danger: "bg-brand",
  neutral: "bg-accent-purple",
};

// Même esprit que le bloc "Real-time Data" / "Pages" de la référence :
// une liste de métriques, chacune avec sa valeur et une mini-barre —
// mais construite uniquement à partir de données réellement disponibles
// dans le diagnostic (pas d'inventer un "max" arbitraire par ligne).
export default function RankedListCard({ title, subtitle, rows }: RankedListCardProps) {
  return (
    <Card className="flex h-full flex-col">
      <SectionHeader title={title} subtitle={subtitle} />
      <ul className="flex flex-1 flex-col justify-center gap-5">
        {rows.map((row) => (
          <li key={row.label}>
            <div className="mb-2 flex items-center justify-between gap-2 text-sm">
              <span className="text-text-muted">{row.label}</span>
              <span className="font-mono font-bold text-text-primary">{row.value}</span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/8">
              <div
                className={`h-full rounded-full ${TONE_BAR[row.tone || "neutral"]}`}
                style={{ width: `${Math.max(0, Math.min(100, row.percent))}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
