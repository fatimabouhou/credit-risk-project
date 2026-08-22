import type { IconName } from '../Icon'
import type { FinancialReport } from '../types'

type Unit = 'x' | 'pct' | 'days' | 'mad'

interface RatioDef {
  category: keyof FinancialReport['ratios_financiers_n']
  key: string
  label: string
  description: string
  icon: IconName
  unit: Unit
  /** true : ratio "vedette", toujours visible. false/absent : seulement dans "Tous les ratios" (App.tsx). */
  primary?: boolean
  /**
   * Seuil réel de bascule bon/mauvais et borne haute de la barre visuelle —
   * absents pour un ratio sans référentiel fiable (aucune fiche RAG ne le
   * couvre, ex. cash_flow, voir agentic-service/app/data/docs) : le ratio
   * s'affiche alors avec sa seule valeur brute, sans pastille ni barre
   * inventée. Seuils repris des mêmes fiches [SIMULÉ] que l'agent IA utilise
   * (data/docs/0X_*.md) — moyennés sur les 6 secteurs quand la fiche RAG est
   * sectorisée, cette page n'ayant pas le secteur du client comme contexte.
   */
  threshold?: number
  /** 'min' : bon si valeur >= seuil (ex. liquidité). 'max' : bon si valeur <= seuil (ex. délais/endettement). */
  direction?: 'min' | 'max'
  /** Borne haute de la barre visuelle (mêmes unités que la valeur brute) — purement d'affichage, jamais utilisée pour le verdict. */
  scaleMax?: number
  goodLabel?: string
  warnLabel?: string
  /** Sévérité affichée quand le seuil n'est pas respecté — 'warn' (ambre) par défaut, 'bad'
   * (rouge) pour un warnLabel qui se lit comme franchement négatif ("Faible")
   * plutôt qu'une simple vigilance ("À surveiller"). */
  warnTone?: 'warn' | 'bad'
}

const clamp = (v: number, max: number) => Math.max(0, Math.min(100, (v / max) * 100))

/**
 * Ratios repris du rapport financial-service (voir engine/ratios_*.py).
 *
 * Les 6 premiers (`primary: true`) sont toujours affichés. Les seuils/scaleMax
 * des 10 suivants viennent des fiches RAG que l'agent IA utilise déjà
 * (agentic-service/app/data/docs/0X_*.md, marquées [SIMULÉ] — repères de
 * plausibilité pour l'exercice, pas des données réelles) : moyenne des
 * bornes sectorielles quand la fiche est sectorisée, cette page n'ayant pas
 * le secteur du client comme contexte (contrairement à outil_benchmark_sectoriel
 * côté agent, qui lui compare secteur par secteur). Les 5 derniers (sans
 * threshold) n'ont aucune fiche RAG les couvrant (cash_flow n'a pas de fiche
 * du tout ; working_capital_frf est volontairement sans seuil, voir
 * 01_liquidite.md §6 — un montant absolu n'est pas comparable entre
 * entreprises de tailles différentes) : valeur brute seule, pas de verdict
 * inventé.
 */
export const RATIO_DEFS: RatioDef[] = [
  // --- Toujours visibles ---
  { category: 'liquidite', key: 'current_ratio', label: 'Liquidité générale', description: "Capacité à couvrir l'ensemble des dettes", icon: 'droplet', unit: 'x', primary: true, threshold: 1.5, direction: 'min', scaleMax: 3, goodLabel: 'Bon niveau', warnLabel: 'Sous le seuil recommandé' },
  { category: 'liquidite', key: 'quick_ratio', label: 'Quick ratio', description: 'Capacité à couvrir les dettes à court terme', icon: 'zap', unit: 'x', primary: true, threshold: 1, direction: 'min', scaleMax: 2, goodLabel: 'Solide', warnLabel: 'À surveiller' },
  { category: 'solvabilite', key: 'autonomie_financiere', label: 'Autonomie financière', description: 'Indépendance vis-à-vis des créanciers', icon: 'bank', unit: 'pct', primary: true, threshold: 0.3, direction: 'min', scaleMax: 0.5, goodLabel: 'Structure saine', warnLabel: 'À surveiller' },
  { category: 'rentabilite', key: 'ebitda_margin', label: 'Marge EBITDA', description: "Rentabilité opérationnelle de l'entreprise", icon: 'chart', unit: 'pct', primary: true, threshold: 0.1, direction: 'min', scaleMax: 0.2, goodLabel: 'Excellente', warnLabel: 'Faible', warnTone: 'bad' },
  { category: 'activite', key: 'dso_days', label: 'DSO', description: 'Délai moyen de recouvrement clients', icon: 'calendar', unit: 'days', primary: true, threshold: 60, direction: 'max', scaleMax: 120, goodLabel: 'Maîtrisé', warnLabel: 'À surveiller' },
  { category: 'activite', key: 'cycle_exploitation_days', label: "Cycle d'exploitation", description: "Durée totale du cycle d'exploitation", icon: 'calendar', unit: 'days', primary: true, threshold: 90, direction: 'max', scaleMax: 150, goodLabel: 'Stable', warnLabel: 'Élevé' },

  // --- "Tous les ratios" — seuil RAG disponible (voir data/docs) ---
  { category: 'liquidite', key: 'cash_ratio', label: 'Cash ratio', description: 'Couverture des dettes court terme par la seule trésorerie', icon: 'droplet', unit: 'x', threshold: 0.2, direction: 'min', scaleMax: 0.5, goodLabel: 'Confortable', warnLabel: 'À surveiller' },
  { category: 'rentabilite', key: 'roa_return_on_assets', label: 'ROA', description: "Rentabilité générée par l'ensemble des actifs", icon: 'chart', unit: 'pct', threshold: 0.02, direction: 'min', scaleMax: 0.09, goodLabel: 'Rentable', warnLabel: 'Faible', warnTone: 'bad' },
  { category: 'rentabilite', key: 'roe_return_on_equity', label: 'ROE', description: 'Rentabilité des capitaux apportés par les actionnaires', icon: 'chart', unit: 'pct', threshold: 0.05, direction: 'min', scaleMax: 0.22, goodLabel: 'Bon rendement', warnLabel: 'Faible', warnTone: 'bad' },
  { category: 'rentabilite', key: 'marge_nette', label: 'Marge nette', description: "Part du chiffre d'affaires transformée en résultat net", icon: 'chart', unit: 'pct', threshold: 0.025, direction: 'min', scaleMax: 0.125, goodLabel: 'Rentable', warnLabel: 'Faible', warnTone: 'bad' },
  { category: 'rentabilite', key: 'marge_operationnelle', label: 'Marge opérationnelle', description: "Rentabilité de l'activité avant charges financières", icon: 'chart', unit: 'pct', threshold: 0.045, direction: 'min', scaleMax: 0.19, goodLabel: 'Bon niveau', warnLabel: 'Faible', warnTone: 'bad' },
  { category: 'activite', key: 'asset_turnover', label: 'Rotation des actifs', description: "Chiffre d'affaires généré par unité d'actif", icon: 'calendar', unit: 'x', threshold: 0.65, direction: 'min', scaleMax: 1.7, goodLabel: 'Efficace', warnLabel: 'Sous-utilisation des actifs' },
  { category: 'solvabilite', key: 'liabilities_to_assets', label: 'Dettes / Total actif', description: "Part de l'actif financée par l'endettement", icon: 'bank', unit: 'pct', threshold: 0.64, direction: 'max', scaleMax: 0.7, goodLabel: 'Endettement maîtrisé', warnLabel: 'Élevé' },
  { category: 'solvabilite', key: 'net_current_liabilities_to_assets', label: 'Passif circulant net / Actif', description: 'Poids du besoin de financement court terme', icon: 'bank', unit: 'pct', threshold: 0.05, direction: 'max', scaleMax: 0.1, goodLabel: 'Situation favorable', warnLabel: 'Besoin significatif', warnTone: 'bad' },
  { category: 'solvabilite', key: 'debt_to_equity_leverage', label: 'Dettes / Capitaux propres', description: "Niveau de levier financier de l'entreprise", icon: 'bank', unit: 'x', threshold: 1.8, direction: 'max', scaleMax: 2.3, goodLabel: 'Levier maîtrisé', warnLabel: 'Élevé' },
  { category: 'solvabilite', key: 'retained_earnings_to_current_liabilities', label: 'Réserves / Passif circulant', description: 'Coussin de réserves face aux dettes court terme', icon: 'bank', unit: 'pct', threshold: 0.1, direction: 'min', scaleMax: 0.4, goodLabel: 'Niveau courant', warnLabel: 'Coussin faible' },

  // --- "Tous les ratios" — aucune fiche RAG ne couvre ces ratios : valeur brute seule ---
  { category: 'liquidite', key: 'working_capital_frf', label: 'Fonds de roulement', description: "Excédent de ressources stables sur l'actif immobilisé", icon: 'bank', unit: 'mad' },
  { category: 'activite', key: 'dpo_days', label: 'DPO', description: 'Délai moyen de paiement des fournisseurs', icon: 'calendar', unit: 'days' },
  { category: 'cash_flow', key: 'cfo_to_total_debt', label: 'CFO / Dettes totales', description: "Capacité du cash d'exploitation à couvrir la dette", icon: 'zap', unit: 'pct' },
  { category: 'cash_flow', key: 'cfo_to_total_assets', label: 'CFO / Total actif', description: "Rendement en cash de l'ensemble des actifs", icon: 'zap', unit: 'pct' },
  { category: 'cash_flow', key: 'free_cash_flow_to_total_debt', label: 'FCF / Dettes totales', description: 'Cash disponible après investissements vs endettement', icon: 'zap', unit: 'pct' },
]

export function formatRatioValue(value: number, unit: Unit): string {
  if (unit === 'x') return `${value.toFixed(2)}×`
  if (unit === 'pct') return `${(value * 100).toFixed(2)}%`
  if (unit === 'mad') { const m = formatMad(value); return `${m.display} ${m.unit}` }
  return `${Math.round(value)} jours`
}

/** Version compacte pour la graduation sous la barre (pas d'unité "jours"
 * répétée 3 fois par ligne, voir thresholdText pour l'unité complète). */
function formatScaleLabel(value: number, unit: Unit): string {
  if (unit === 'x') return `${value.toFixed(1)}×`
  if (unit === 'pct') return `${Math.round(value * 100)}%`
  return `${Math.round(value)}`
}

export interface RatioRow {
  key: string
  icon: IconName
  label: string
  description: string
  value: string
  /** Champs absents (undefined) quand def.threshold n'est pas défini — App.tsx
   * affiche alors des tirets plutôt qu'une pastille/barre/tendance inventées. */
  verdict?: string
  tone?: 'good' | 'warn' | 'bad'
  trackPct?: number
  /** Graduation sous la barre : ["0", seuil formaté, borne haute formatée]. */
  scaleLabels?: [string, string, string]
  /** "valeur / seuil", ex. "1.70× / 1.50×" ou "543 jours / < 60 jours". */
  thresholdText?: string
  trendIcon?: 'trendUp' | 'trendFlat' | 'trendDown'
}

function buildRow(def: RatioDef, raw: number): RatioRow {
  const base = { key: def.key, icon: def.icon, label: def.label, description: def.description, value: formatRatioValue(raw, def.unit) }
  if (def.threshold === undefined || def.direction === undefined || def.scaleMax === undefined || !def.goodLabel || !def.warnLabel) {
    return base
  }
  const good = def.direction === 'min' ? raw >= def.threshold : raw <= def.threshold
  const tone = good ? 'good' : (def.warnTone ?? 'warn')
  return {
    ...base,
    verdict: good ? def.goodLabel : def.warnLabel,
    tone,
    trackPct: clamp(raw, def.scaleMax),
    scaleLabels: ['0', formatScaleLabel(def.threshold, def.unit), formatScaleLabel(def.scaleMax, def.unit)],
    thresholdText: `${formatRatioValue(raw, def.unit)} / ${def.direction === 'max' ? '< ' : ''}${formatRatioValue(def.threshold, def.unit)}`,
    trendIcon: tone === 'good' ? 'trendUp' : tone === 'bad' ? 'trendDown' : 'trendFlat',
  }
}

/** Les 6 ratios "vedette", toujours affichés. */
export function buildRatioRows(report: FinancialReport): RatioRow[] {
  const rows: RatioRow[] = []
  for (const def of RATIO_DEFS) {
    if (!def.primary) continue
    const raw = report.ratios_financiers_n?.[def.category]?.[def.key]
    if (typeof raw !== 'number') continue
    rows.push(buildRow(def, raw))
  }
  return rows
}

/** Le reste des ratios calculés par financial-service, derrière "Tous les ratios" (App.tsx). */
export function buildExtraRatioRows(report: FinancialReport): RatioRow[] {
  const rows: RatioRow[] = []
  for (const def of RATIO_DEFS) {
    if (def.primary) continue
    const raw = report.ratios_financiers_n?.[def.category]?.[def.key]
    if (typeof raw !== 'number') continue
    rows.push(buildRow(def, raw))
  }
  return rows
}

/**
 * Score de santé 0-100 dérivé du score Altman Z (financial-service ne renvoie pas
 * de score global unique) : position du score dans sa zone, mappée sur l'intervalle
 * de la zone (distress -> 0-40, grey -> 40-70, safe -> 70-100).
 */
export function computeHealthScore(altman: FinancialReport['altman_score']): number | null {
  if (!altman || altman.score === null || !altman.zone) return null
  const bounds: Record<string, { min: number; max: number; scoreMin: number; scoreMax: number }> = {
    distress: { min: 0, max: 40, scoreMin: -5, scoreMax: 1.1 },
    grey: { min: 40, max: 70, scoreMin: 1.1, scoreMax: 2.6 },
    safe: { min: 70, max: 100, scoreMin: 2.6, scoreMax: 6 },
  }
  const b = bounds[altman.zone]
  if (!b) return null
  const ratio = clamp(((altman.score - b.scoreMin) / (b.scoreMax - b.scoreMin)) * 100, 100) / 100
  return Math.round(b.min + ratio * (b.max - b.min))
}

export function healthScoreLabel(zone: FinancialReport['altman_score']['zone']): { title: string; subtitle: string } {
  if (zone === 'safe') return { title: 'Risque maîtrisé', subtitle: 'Profil financier favorable' }
  if (zone === 'grey') return { title: 'Risque à surveiller', subtitle: 'Zone grise Altman' }
  if (zone === 'distress') return { title: 'Risque élevé', subtitle: "Zone de détresse financière" }
  return { title: 'Non évalué', subtitle: 'Données insuffisantes' }
}

/**
 * LineChart (App.tsx) attend des valeurs 0-100 (position Y calculée comme
 * `98 - value * .78` dans un viewBox de 100x100) — les montants réels en MAD
 * (dizaines de millions) doivent être ramenés à cette échelle avant affichage,
 * sinon les points sortent du cadre visible et la courbe disparaît.
 */
export function normalizeSeries(values: number[]): number[] {
  const max = Math.max(...values, 0)
  if (max <= 0) return values.map(() => 0)
  return values.map((v) => Math.max(0, (v / max) * 100))
}

export function formatMad(value: number): { display: string; unit: string } {
  const abs = Math.abs(value)
  if (abs >= 1_000_000) return { display: (value / 1_000_000).toFixed(2), unit: 'M MAD' }
  if (abs >= 1_000) return { display: (value / 1_000).toFixed(1), unit: 'K MAD' }
  return { display: value.toFixed(0), unit: 'MAD' }
}

/**
 * Un seul exercice dans le dossier (voir evaluator.py::_annees_disponibles) :
 * pas d'historique exploitable pour un graphique de tendance (courbe à deux
 * points nuls sur trois, voir capture utilisateur) — la cascade de
 * l'exercice disponible (buildPerformanceCascade) reste, elle, lisible avec
 * une seule année.
 */
export function hasSingleYearOnly(report: FinancialReport | null): boolean {
  const years = Object.keys(report?.donnees_brutes_applaties ?? {})
  return years.length <= 1
}

export interface CascadePoint {
  label: string
  value: number
}

/**
 * Remplace la série temporelle (3 années) par une cascade de rentabilité de
 * l'exercice de référence : Chiffre d'affaires -> EBITDA -> Résultat net —
 * même composant LineChart (App.tsx) que l'ancien graphique de tendance,
 * seuls les 3 points affichés changent. Les 3 indicateurs viennent de
 * analyse_tendances_3ans (déjà présent même à 1 seul exercice, voir
 * TrendsEngine.analyze_trends) plutôt que donnees_brutes_applaties.
 */
export function buildPerformanceCascade(report: FinancialReport | null): CascadePoint[] | null {
  if (!report) return null
  const ca = report.analyse_tendances_3ans?.chiffre_affaires?.valeurs?.N
  const ebitda = report.analyse_tendances_3ans?.ebitda?.valeurs?.N
  const net = report.analyse_tendances_3ans?.resultat_net?.valeurs?.N
  if (ca === undefined || ebitda === undefined || net === undefined) return null

  return [
    { label: "Chiffre d'affaires", value: ca },
    { label: 'EBITDA', value: ebitda },
    { label: 'Résultat net', value: net },
  ]
}
