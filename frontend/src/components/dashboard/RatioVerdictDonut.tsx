import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import Card from "../ui/Card";
import SectionHeader from "../ui/SectionHeader";
import { verdictTone } from "../../lib/ratios";
import type { Ratio } from "../../types/analysis";

interface RatioVerdictDonutProps {
  ratios: Ratio[];
  nonComparablesCount?: number;
}

const GROUPS: { tone: string; label: string; color: string }[] = [
  { tone: "success", label: "Dans la norme", color: "#34d399" },
  { tone: "warning", label: "À surveiller", color: "#fbbf24" },
  { tone: "danger", label: "Alerte", color: "#eb3349" },
  { tone: "neutral", label: "Non normé", color: "#94a3b8" },
];

export default function RatioVerdictDonut({ ratios, nonComparablesCount = 0 }: RatioVerdictDonutProps) {
  const counts: Record<string, number> = { success: 0, warning: 0, danger: 0, neutral: nonComparablesCount };
  for (const r of ratios) {
    const tone = r.verdict ? verdictTone(r.verdict.verdict) : "neutral";
    counts[tone] = (counts[tone] || 0) + 1;
  }

  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const present = GROUPS.filter((g) => counts[g.tone] > 0).map((g) => ({ ...g, count: counts[g.tone] }));
  const pctSain = total > 0 ? Math.round((counts.success / total) * 100) : 0;

  return (
    <Card className="@container flex h-full flex-col">
      <SectionHeader title="Composition des ratios" subtitle={`${total} ratios calculés`} />

      {total === 0 ? (
        <p className="text-sm text-text-faint">Aucun ratio à représenter.</p>
      ) : (
        <div className="flex flex-1 flex-col items-center justify-center gap-6 @sm:flex-col @lg:flex-row @lg:gap-8">
          <div className="relative shrink-0">
            <ResponsiveContainer width={224} height={224}>
              <PieChart>
                <Pie
                  data={present}
                  dataKey="count"
                  nameKey="label"
                  innerRadius={72}
                  outerRadius={104}
                  paddingAngle={3}
                  cornerRadius={5}
                  stroke="none"
                >
                  {present.map((entry) => (
                    <Cell key={entry.tone} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number, _name, item) => [`${value} ratio(s)`, item.payload.label]}
                  contentStyle={{
                    background: "#0d1220",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 8,
                    fontSize: 14,
                  }}
                  itemStyle={{ color: "#f5f7fa" }}
                  labelStyle={{ color: "#94a3b8" }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-extrabold text-text-primary">{pctSain}%</span>
              <span className="mt-1.5 max-w-[110px] text-center text-xs font-semibold text-text-faint">
                dans la norme
              </span>
            </div>
          </div>

          <ul className="flex w-full flex-col gap-4">
            {present.map((g) => (
              <li key={g.tone} className="flex items-center gap-3 text-base">
                <span className="h-3 w-3 shrink-0 rounded-full" style={{ background: g.color }} />
                <span className="flex-1 text-text-muted">{g.label}</span>
                <span className="font-mono text-lg font-bold text-text-primary">{g.count}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}
