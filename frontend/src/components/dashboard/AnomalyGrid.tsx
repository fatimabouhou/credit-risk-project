import Card from "../ui/Card";
import Badge from "../ui/Badge";
import SectionHeader from "../ui/SectionHeader";
import { ratioLabel, splitRatioName, verdictLabel, SEVERITE_TONE } from "../../lib/ratios";
import type { Anomalie } from "../../types/analysis";

interface AnomalyGridProps {
  anomalies: Anomalie[];
}

function SeverityIcon({ severite }: { severite: string }) {
  const isElevee = severite === "elevee";
  return (
    <span
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-base ${
        isElevee ? "bg-brand/12 text-brand-light" : "bg-chart-warning/12 text-chart-warning"
      }`}
      aria-hidden
    >
      {isElevee ? "▲" : "!"}
    </span>
  );
}

export default function AnomalyGrid({ anomalies }: AnomalyGridProps) {
  return (
    <Card>
      <SectionHeader title="Anomalies détectées" subtitle={`${anomalies.length} ratio(s) hors norme`} />

      {anomalies.length === 0 ? (
        <p className="text-sm text-text-faint">Aucune anomalie détectée.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {anomalies.map((a, i) => {
            const { key } = splitRatioName(a.ratio_name);
            return (
              <div
                key={i}
                className="flex items-center gap-4 rounded-xl border border-white/8 bg-bg-base p-5"
              >
                <SeverityIcon severite={a.severite} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-base font-semibold text-text-primary">{ratioLabel(key)}</p>
                  <p className="text-sm text-text-faint capitalize">{verdictLabel(a.verdict)}</p>
                </div>
                <Badge tone={SEVERITE_TONE[a.severite] || "neutral"} size="sm">
                  {a.severite === "elevee" ? "élevée" : "à surveiller"}
                </Badge>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
