export type RatioValue = number | null

export interface FinancialReport {
  client_id: string
  annee_reference: number
  ratios_financiers_n: Record<string, Record<string, RatioValue | boolean | string>>
  analyse_tendances_3ans: Record<string, Trend>
  couverture_dette_dscr: { dscr: number | null; is_dscr_acceptable: boolean | null }
  altman_score: { model: string | null; score: number | null; zone: 'safe' | 'grey' | 'distress' | null; formula_used: string | null }
}

export interface Trend {
  valeurs?: { N?: number; 'N-1'?: number; 'N-2'?: number }
  variations?: { 'N_vs_N-1_pct'?: number | null }
  tendance_recente?: string
}

export interface BenchmarkRatio {
  ratio_name?: string
  name?: string
  value?: number | null
  valeur?: number | null
  verdict?: string
  norme?: string
  reference?: string
}

export interface Finding {
  id?: string
  titre?: string
  categorie?: string
  niveau_risque?: string
  priorite?: string
  diagnostic?: string
  hypotheses?: string[]
  actions?: string[]
  ratio_name?: string
  severite?: string
  message?: string
}

export interface AgentAnalysis {
  client_id: string
  secteur: string | null
  taille: string | null
  taille_source: string | null
  ratios: BenchmarkRatio[]
  anomalies: Finding[]
  patterns: Finding[]
  altman_score: FinancialReport['altman_score'] | null
  dscr: FinancialReport['couverture_dette_dscr'] | null
  tendances: Record<string, Trend> | null
  conformite_reglementaire: { attestations_legales?: Array<{ source?: string; is_compliant?: boolean }> } | null
  alertes_coherence: string[]
  ratios_non_comparables: BenchmarkRatio[]
  champs_manquants: string[]
  conclusion: string
  decision: { decision?: 'accord' | 'refus' | 'a_surveiller' | null; score?: number; contributions?: Array<{ label: string; points: number }>; justification?: string; erreur?: string } | null
}

export type DocumentAudit = Record<string, unknown>
