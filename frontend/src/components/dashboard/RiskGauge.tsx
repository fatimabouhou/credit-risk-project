import Card from "../ui/Card";
import SectionHeader from "../ui/SectionHeader";
import type { DecisionValue } from "../../types/analysis";

interface RiskGaugeProps {
  score: number;
  decision: DecisionValue;
}

// Seuils exacts de compute_risk_score (agentic-service/app/graph/decision.py)
// — jamais recalculés ici, uniquement affichés.
const ACCORD_MAX = 3;
const SURVEILLANCE_MAX = 7;

const DECISION_LABEL: Record<string, string> = {
  accord: "Accord",
  a_surveiller: "À surveiller",
  refus: "Refus",
};

const DECISION_HEX: Record<string, string> = {
  accord: "#34d399",
  a_surveiller: "#fbbf24",
  refus: "#eb3349",
};

// Cadran façon "speedometer" (jauge à 300°, trou de 60° en bas) — même
// géométrie que la référence fournie, couleurs inversées : chez nous un
// score BAS est bon (vert), un score HAUT est mauvais (rouge), l'inverse
// d'un "credit score" classique où un score haut est excellent.
const START_ANGLE = 120; // degrés, bas-gauche
const SWEEP = 300;
const R = 130;
const CX = 160;
const CY = 150;

function polarPoint(angleDeg: number, radius = R) {
  const rad = (angleDeg * Math.PI) / 180;
  return { x: CX + radius * Math.cos(rad), y: CY + radius * Math.sin(rad) };
}

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

function lerpColor(c1: string, c2: string, t: number) {
  const p1 = c1.match(/\w\w/g)!.map((h) => parseInt(h, 16));
  const p2 = c2.match(/\w\w/g)!.map((h) => parseInt(h, 16));
  const rgb = p1.map((v, i) => Math.round(lerp(v, p2[i], t)));
  return `rgb(${rgb.join(",")})`;
}

// Vert -> ambre -> rouge, interpolé point par point le long de l'arc (SVG
// n'a pas de dégradé "le long d'un chemin" natif) : approximé par de
// nombreux petits segments de couleur interpolée.
function gaugeColorAt(t: number) {
  if (t < 0.5) return lerpColor("#34d399", "#fbbf24", t / 0.5);
  return lerpColor("#fbbf24", "#eb3349", (t - 0.5) / 0.5);
}

const SEGMENTS = 60;

export default function RiskGauge({ score, decision }: RiskGaugeProps) {
  const displayMax = Math.max(14, score + 2);
  const clampedScore = Math.max(0, Math.min(score, displayMax));
  const needleAngle = START_ANGLE + (clampedScore / displayMax) * SWEEP;
  const needleTip = polarPoint(needleAngle, R - 22);
  const decisionColor = (decision && DECISION_HEX[decision]) || "#94a3b8";
  const decisionLabel = decision ? DECISION_LABEL[decision] : "Non déterminée";

  const ticks = [0, ACCORD_MAX, SURVEILLANCE_MAX, displayMax];

  return (
    <Card className="flex flex-col items-center">
      <SectionHeader title="Score de risque" subtitle="Contributions déterministes, seuils fixes" />

      <svg viewBox="0 0 320 250" width="100%" height="230" className="overflow-visible">
        {/* Arc de fond, en segments colorés (vert -> ambre -> rouge) */}
        {Array.from({ length: SEGMENTS }).map((_, i) => {
          const a1 = START_ANGLE + (i / SEGMENTS) * SWEEP;
          const a2 = START_ANGLE + ((i + 1) / SEGMENTS) * SWEEP + 0.6;
          const p1 = polarPoint(a1);
          const p2 = polarPoint(a2);
          const largeArc = a2 - a1 > 180 ? 1 : 0;
          return (
            <path
              key={i}
              d={`M ${p1.x} ${p1.y} A ${R} ${R} 0 ${largeArc} 1 ${p2.x} ${p2.y}`}
              stroke={gaugeColorAt(i / (SEGMENTS - 1))}
              strokeWidth={16}
              strokeLinecap="round"
              fill="none"
              opacity={0.9}
            />
          );
        })}

        {/* Graduations */}
        {ticks.map((t) => {
          const angle = START_ANGLE + (t / displayMax) * SWEEP;
          const p = polarPoint(angle, R + 24);
          return (
            <text
              key={t}
              x={p.x}
              y={p.y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-text-faint text-[15px] font-semibold"
            >
              {t}
            </text>
          );
        })}

        {/* Aiguille */}
        <line
          x1={CX}
          y1={CY}
          x2={needleTip.x}
          y2={needleTip.y}
          stroke="#f5f7fa"
          strokeWidth={3}
          strokeLinecap="round"
        />
        <circle cx={CX} cy={CY} r={7} fill="#f5f7fa" />

        {/* Centre : score + décision */}
        <text x={CX} y={CY + 48} textAnchor="middle" className="fill-text-primary text-[54px] font-extrabold">
          {score}
        </text>
        <text
          x={CX}
          y={CY + 80}
          textAnchor="middle"
          fill={decisionColor}
          className="text-[19px] font-bold"
        >
          {decisionLabel}
        </text>
      </svg>
    </Card>
  );
}
