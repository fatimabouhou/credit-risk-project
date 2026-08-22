import type { BenchmarkRatio, Finding } from '../types'

/**
 * Les 4 catégories réellement benchmarkées côté backend (voir
 * agentic-service/app/tools/benchmark_tool.py, BENCHMARKED_CATEGORIES) —
 * "ratio_name" est toujours préfixé par l'une d'elles (ex.
 * "liquidite.current_ratio"). Il n'existe PAS de 5e catégorie "trésorerie" :
 * l'ancien radar à 5 axes en incluait une qui n'avait jamais de données
 * réelles derrière.
 */
export const RADAR_AXES: Array<{ key: string; label: string }> = [
  { key: 'liquidite', label: 'Liquidité' },
  { key: 'rentabilite', label: 'Rentabilité' },
  { key: 'activite', label: 'Activité' },
  { key: 'solvabilite', label: 'Solvabilité' },
]

export interface RadarScore {
  label: string
  /** % de ratios de cette catégorie non signalés en anomalie ; null si aucun ratio comparé (pas de donnée à afficher). */
  pct: number | null
}

/** Position polaire sur le radar : angle 0° = axe du haut, sens horaire. */
export function radarPoint(center: [number, number], maxRadius: number, angleDeg: number, pct: number): [number, number] {
  const angleRad = ((angleDeg - 90) * Math.PI) / 180
  const r = maxRadius * (pct / 100)
  return [center[0] + r * Math.cos(angleRad), center[1] + r * Math.sin(angleRad)]
}

/**
 * Score par axe = part des ratios de la catégorie qui ne sont PAS dans
 * "anomalies" (déjà filtrées côté backend, voir _extract_benchmark) — pas de
 * dépendance à la liste exacte des libellés de verdict, juste au comptage
 * anomalie/non-anomalie déjà fait en amont.
 */
export function buildRadarScores(ratios: BenchmarkRatio[], anomalies: Finding[]): RadarScore[] {
  return RADAR_AXES.map(({ key, label }) => {
    const compared = ratios.filter((r) => r.ratio_name?.startsWith(`${key}.`))
    if (compared.length === 0) return { label, pct: null }
    const flagged = anomalies.filter((a) => a.ratio_name?.startsWith(`${key}.`)).length
    return { label, pct: Math.round(100 * (1 - flagged / compared.length)) }
  })
}
