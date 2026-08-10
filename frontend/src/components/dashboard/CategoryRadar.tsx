import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer } from "recharts";
import Card from "../ui/Card";
import SectionHeader from "../ui/SectionHeader";
import { verdictTone } from "../../lib/ratios";
import type { Ratio } from "../../types/analysis";

interface CategoryRadarProps {
  categories: { category: string; label: string; ratios: { ratio: Ratio; key: string }[] }[];
}

// Vue d'ensemble "structure" du dossier — % dans la norme par catégorie,
// les 4 sur un seul graphique pour voir la forme globale d'un coup d'œil
// (une catégorie qui tire vers le centre = point faible du dossier).
// Complète les 4 stat cards, ne les remplace pas.
export default function CategoryRadar({ categories }: CategoryRadarProps) {
  const data = categories.map(({ label, ratios }) => {
    const tones = ratios.map(({ ratio }) => (ratio.verdict ? verdictTone(ratio.verdict.verdict) : "neutral"));
    const total = tones.length;
    const success = tones.filter((t) => t === "success").length;
    return { label, pct: total > 0 ? Math.round((success / total) * 100) : 0 };
  });

  return (
    <Card>
      <SectionHeader title="Structure du dossier" subtitle="% dans la norme, par catégorie" />
      <ResponsiveContainer width="100%" height={220}>
        <RadarChart data={data} outerRadius="75%">
          <PolarGrid stroke="rgba(255,255,255,0.1)" />
          <PolarAngleAxis dataKey="label" tick={{ fill: "#94a3b8", fontSize: 15 }} />
          <Radar dataKey="pct" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.35} strokeWidth={2} />
        </RadarChart>
      </ResponsiveContainer>
    </Card>
  );
}
