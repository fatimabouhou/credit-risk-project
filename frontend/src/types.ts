export type RatioValue = number | null

export interface FinancialReport {
  client_id: string
  annee_reference: number
  ratios_financiers_n: Record<string, Record<string, RatioValue | boolean | string>>
  analyse_tendances_3ans: Record<string, Trend>
  couverture_dette_dscr: {
    dscr: number | null
    dscr_existant?: number | null
    dscr_apres_nouveau_credit?: number | null
    annuite_nouveau_credit?: number | null
    montant_nouveau_credit?: number | null
    duree_nouveau_credit_mois?: number | null
    taux_annuel_nouveau_credit?: number | null
    nouveau_credit_evaluable?: boolean
    is_dscr_acceptable: boolean | null
    is_dscr_apres_nouveau_credit_acceptable?: boolean | null
  }
  altman_score: { model: string | null; score: number | null; zone: 'safe' | 'grey' | 'distress' | null; formula_used: string | null }
  /** Clé = année ("2023"...), voir evaluator.py::donnees_brutes_applaties — postes bruts aplatis (immobilisations, stocks, tresorerie_actif...), une entrée par exercice réellement présent dans le dossier (1 à 3). */
  donnees_brutes_applaties?: Record<string, Record<string, number>>
}

export interface Trend {
  valeurs?: { N?: number; 'N-1'?: number; 'N-2'?: number }
  variations?: { 'N_vs_N-1_pct'?: number | null }
  tendance_recente?: string
}

/** Forme réelle de "comparisons" (voir agentic-service/app/tools/benchmark_tool.py, check_client_ratios). */
export interface BenchmarkRatio {
  ratio_name: string
  ratio_value: number | null
  reference_id?: string | null
  taille?: string | null
  verdict?: { verdict?: string; [key: string]: unknown } | null
}

/**
 * Sert à la fois pour les patterns croisés (titre/diagnostic présents) et les
 * anomalies de benchmark (ratio_name/verdict/severite présents, jamais de
 * titre/diagnostic/message — voir benchmark_tool.py, anomalies_detectees).
 * Ne pas supposer que titre/diagnostic/message existent sans vérifier lequel
 * des deux jeux de champs est réellement rempli.
 */
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
  ratio_value?: number | null
  verdict?: string
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

/** Champ tracé par les extracteurs : {value, source, page}. */
export interface TracedField<T = number> {
  value: T | null
  source: string
  page: number
}

export interface DocumentAudit {
  client_id: string
  profil_administratif: {
    demande_credit?: { montant_demande: string | null; duree: string | null; objet: string | null; apport: string | null }
    fiche_renseignements?: { raison_sociale: string | null; capital_social: string | null; secteur: string | null; creation: string | null }
  }
  conformite_reglementaire: {
    attestations_legales?: Array<{ source: 'DGI' | 'CNSS'; ice: string | null; is_compliant: boolean; statut_texte: string }>
  }
  historique_financier: {
    historique_financier?: Array<Record<string, unknown> & { annee: number | string }>
  }
  comportement_bancaire: {
    comptes_bancaires?: Array<{
      banque: string
      solde_fin_periode: TracedField
      total_crediteur: TracedField
      total_debiteur: TracedField
      comportement: { nombre_rejets: TracedField<number>; decouvert_max_detecte: TracedField }
    }>
    dette_existante?: {
      credits_detailles?: Array<{ intitule: string; mensualite: TracedField; capital_restant: TracedField }>
      mensualite_totale?: TracedField
      capital_restant_total?: TracedField
    }
    centrale_risques?: {
      ice: TracedField<string>
      total_autorisation: TracedField
      total_encours_utilise: TracedField
      taux_utilisation: TracedField
      incidents: { incidents_definis: TracedField<boolean>; statut_incidents: TracedField<string>; nombre_incidents: TracedField<number> }
    }
  }
  alertes_coherence: string[]
}
