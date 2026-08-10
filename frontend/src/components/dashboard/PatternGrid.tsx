import Card from "../ui/Card";
import SectionHeader from "../ui/SectionHeader";
import PatternCard from "./PatternCard";
import type { Pattern } from "../../types/analysis";

interface PatternGridProps {
  patterns: Pattern[];
}

const RISK_ORDER: Record<string, number> = { "élevé": 0, "modéré": 1, "faible": 2 };

export default function PatternGrid({ patterns }: PatternGridProps) {
  const sorted = [...patterns].sort(
    (a, b) => (RISK_ORDER[a.niveau_risque] ?? 1) - (RISK_ORDER[b.niveau_risque] ?? 1)
  );

  return (
    <Card>
      <SectionHeader
        title="Combinaisons de ratios (patterns)"
        subtitle={`${patterns.length} pattern(s) déclenché(s)`}
      />

      {sorted.length === 0 ? (
        <p className="text-sm text-text-faint">Aucune combinaison significative détectée.</p>
      ) : (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          {sorted.map((p) => (
            <PatternCard key={p.id} pattern={p} />
          ))}
        </div>
      )}
    </Card>
  );
}
