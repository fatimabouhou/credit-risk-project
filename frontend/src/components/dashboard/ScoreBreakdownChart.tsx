import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Card from "../ui/Card";
import SectionHeader from "../ui/SectionHeader";
import type { Contribution } from "../../types/analysis";

interface ScoreBreakdownChartProps {
  contributions: Contribution[] | undefined;
}

function truncate(label: string, max = 16): string {
  return label.length > max ? `${label.slice(0, max - 1)}…` : label;
}

export default function ScoreBreakdownChart({ contributions }: ScoreBreakdownChartProps) {
  const sorted = [...(contributions || [])].sort((a, b) => b.points - a.points);
  const maxPoints = Math.max(...sorted.map((c) => c.points), 1);

  return (
    <Card className="flex h-full flex-col">
      <SectionHeader
        title="Répartition du score"
        subtitle="Points de risque attribués à chaque signal — pas la valeur du ratio"
      />

      {sorted.length === 0 ? (
        <p className="flex min-h-[240px] flex-1 items-center text-sm text-text-faint">
          Aucun signal de risque détecté.
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={Math.max(240, sorted.length * 48)}>
          <BarChart data={sorted} layout="vertical" margin={{ left: 8, right: 40, top: 4, bottom: 4 }}>
            <CartesianGrid horizontal={false} stroke="rgba(255,255,255,0.08)" />
            <XAxis
              type="number"
              domain={[0, maxPoints]}
              allowDecimals={false}
              tick={{ fill: "#4b5768", fontSize: 14 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="label"
              width={160}
              interval={0}
              tickFormatter={(label: string) => truncate(label)}
              tick={{ fill: "#94a3b8", fontSize: 14 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              formatter={(value: number) => [`+${value} pts`, ""]}
              labelFormatter={(label: string) => label}
              contentStyle={{
                background: "#0d1220",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 8,
                fontSize: 14,
              }}
              itemStyle={{ color: "#f5f7fa" }}
              labelStyle={{ color: "#94a3b8", marginBottom: 4 }}
            />
            <Bar dataKey="points" radius={[0, 4, 4, 0]} maxBarSize={28}>
              {sorted.map((entry) => (
                <Cell key={entry.label} fill="#8b5cf6" />
              ))}
              <LabelList
                dataKey="points"
                position="right"
                formatter={(value: number) => `+${value} pts`}
                fill="#f5f7fa"
                fontSize={13}
                fontWeight={700}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
