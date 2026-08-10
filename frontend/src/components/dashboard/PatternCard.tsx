import Card from "../ui/Card";
import Badge from "../ui/Badge";
import { NIVEAU_RISQUE_TONE } from "../../lib/ratios";
import type { Pattern } from "../../types/analysis";

interface PatternCardProps {
  pattern: Pattern;
}

export default function PatternCard({ pattern }: PatternCardProps) {
  const tone = NIVEAU_RISQUE_TONE[pattern.niveau_risque] || "neutral";

  return (
    <Card accent={tone} className="flex h-full flex-col">
      <div className="mb-3 flex items-center justify-between gap-2">
        <span className="font-mono text-xs font-bold text-text-faint">{pattern.id}</span>
        <Badge tone={tone} size="sm">
          {pattern.niveau_risque}
        </Badge>
      </div>

      <h4 className="mb-3 text-lg font-bold text-text-primary">{pattern.titre}</h4>

      <p className="line-clamp-3 flex-1 text-[15px] leading-relaxed text-text-muted">{pattern.diagnostic}</p>

      {pattern.hypotheses?.length > 0 && (
        <p className="mt-4 line-clamp-2 text-sm leading-relaxed text-text-faint italic">
          <span className="font-semibold not-italic">Hypothèse possible :</span> {pattern.hypotheses[0]}
        </p>
      )}
    </Card>
  );
}
