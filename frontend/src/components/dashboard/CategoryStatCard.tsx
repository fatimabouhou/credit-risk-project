import type { ReactNode } from "react";
import Card from "../ui/Card";
import { verdictTone, type Tone } from "../../lib/ratios";
import type { Ratio } from "../../types/analysis";

interface CategoryStatCardProps {
  label: string;
  ratios: { ratio: Ratio; key: string }[];
  extra?: ReactNode;
}

const DELTA_TONE_CLASSES: Record<Tone, string> = {
  success: "text-chart-good",
  warning: "text-chart-warning",
  danger: "text-brand-light",
  neutral: "text-text-faint",
};

// Épuré à l'extrême, façon stat cards "Active Conversations" : label +
// petit indicateur coloré (pas de pastille pleine, pas d'icône, pas de
// barre) + gros chiffre. Le "delta" n'est pas une variation dans le
// temps (pas de donnée pour ça) mais le compte de ratios qui s'écartent
// de la norme dans cette catégorie — même position/style, sémantique
// honnête.
export default function CategoryStatCard({ label, ratios, extra }: CategoryStatCardProps) {
  const tones = ratios.map(({ ratio }) => (ratio.verdict ? verdictTone(ratio.verdict.verdict) : "neutral"));
  const total = tones.length;
  const successCount = tones.filter((t) => t === "success").length;
  const dangerCount = tones.filter((t) => t === "danger").length;
  const warningCount = tones.filter((t) => t === "warning").length;
  const pct = total > 0 ? Math.round((successCount / total) * 100) : 0;

  const overallTone: Tone = dangerCount > 0 ? "danger" : warningCount > 0 ? "warning" : "success";
  const offCount = dangerCount + warningCount;
  const deltaLabel = offCount === 0 ? "Sain" : `${offCount} à surveiller`;
  const arrow = offCount === 0 ? "✓" : "▲";

  return (
    <Card>
      <div className="flex items-center justify-between gap-2">
        <span className="text-base font-bold tracking-wide text-text-muted uppercase">{label}</span>
        <span className={`flex shrink-0 items-center gap-1 text-sm font-semibold whitespace-nowrap ${DELTA_TONE_CLASSES[overallTone]}`}>
          <span>{arrow}</span>
          {deltaLabel}
        </span>
      </div>

      <div className="mt-6">
        <span className="text-6xl font-extrabold text-text-primary">{pct}%</span>
      </div>
      <p className="mt-2 text-base text-text-faint">
        {successCount}/{total} ratios dans la norme
      </p>

      {extra && <div className="mt-4 flex flex-wrap gap-2">{extra}</div>}
    </Card>
  );
}
