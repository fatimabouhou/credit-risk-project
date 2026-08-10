import Badge from "../ui/Badge";
import type { DecisionValue } from "../../types/analysis";

interface ClientHeaderProps {
  clientId: string;
  secteur: string | null;
  taille: string | null;
  decision: DecisionValue;
  tailleEcart?: string | null;
}

const DECISION_LABEL: Record<string, string> = {
  accord: "Accord",
  a_surveiller: "À surveiller",
  refus: "Refus",
};

const DECISION_CLASSES: Record<string, string> = {
  accord: "text-chart-good bg-chart-good/10 border-chart-good/30",
  a_surveiller: "text-chart-warning bg-chart-warning/10 border-chart-warning/30",
  refus: "text-brand-light bg-brand/10 border-brand/35",
};

export default function ClientHeader({ clientId, secteur, taille, decision, tailleEcart }: ClientHeaderProps) {
  const decisionClass = decision ? DECISION_CLASSES[decision] : "text-text-muted bg-white/5 border-white/15";
  const decisionLabel = decision ? DECISION_LABEL[decision] : "Non déterminée";

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-bold tracking-wider text-text-faint uppercase">Client</p>
          <h1 className="mt-2 text-5xl font-extrabold tracking-tight text-text-primary xl:text-6xl">
            {clientId}
          </h1>
          <div className="mt-4 flex flex-wrap gap-2.5">
            {secteur && <Badge tone="neutral">Secteur {secteur}</Badge>}
            {taille && <Badge tone="neutral">Taille {taille}</Badge>}
          </div>
        </div>

        <span
          className={`inline-flex items-center gap-2.5 rounded-full border px-7 py-3.5 text-lg font-bold ${decisionClass}`}
        >
          <span className="h-2.5 w-2.5 rounded-full bg-current" />
          {decisionLabel}
        </span>
      </div>

      {tailleEcart && (
        <p className="rounded-lg border border-chart-warning/25 bg-chart-warning/8 px-5 py-4 text-sm text-chart-warning">
          ⚠ {tailleEcart}
        </p>
      )}
    </div>
  );
}
