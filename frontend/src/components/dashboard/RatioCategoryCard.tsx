import Card from "../ui/Card";
import Badge from "../ui/Badge";
import ProgressBar from "../ui/ProgressBar";
import { categoryLabel, computeRatioProgress, formatRatioValue, ratioLabel, verdictLabel, verdictTone } from "../../lib/ratios";
import type { Ratio } from "../../types/analysis";

interface RatioCategoryCardProps {
  category: string;
  ratios: { ratio: Ratio; key: string }[];
}

export default function RatioCategoryCard({ category, ratios }: RatioCategoryCardProps) {
  return (
    <Card>
      <h3 className="mb-5 text-sm font-bold tracking-widest text-brand-light uppercase">
        {categoryLabel(category)}
      </h3>

      <ul className="flex flex-col gap-5">
        {ratios.map(({ ratio, key }) => {
          const tone = ratio.verdict ? verdictTone(ratio.verdict.verdict) : "neutral";
          const progress = computeRatioProgress(ratio.ratio_value, ratio.verdict);

          return (
            <li key={ratio.ratio_name}>
              <div className="mb-2 flex items-center justify-between gap-2">
                <span className="text-[15px] font-semibold text-text-primary">{ratioLabel(key)}</span>
                <span className="font-mono text-[15px] font-bold text-text-primary">
                  {formatRatioValue(key, ratio.ratio_value)}
                </span>
              </div>
              {progress !== null ? (
                <ProgressBar percent={progress} tone={tone} />
              ) : (
                <div className="h-1.5 w-full rounded-full bg-white/5" />
              )}
              {ratio.verdict && (
                <div className="mt-2">
                  <Badge tone={tone} size="sm">
                    {verdictLabel(ratio.verdict.verdict)}
                  </Badge>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
