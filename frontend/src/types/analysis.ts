// Types calqués exactement sur la réponse réelle de
// `POST /api/v1/agentic/analyze/{client_id}` (agentic-service/app/api/routes.py)
// — mêmes noms de clés, mêmes valeurs possibles, aucune couche de mapping.

export type RatioVerdictLabel =
  | "dans_la_norme"
  | "favorable"
  | "au_dessus_norme"
  | "en_dessous_norme"
  | "zone_a_interroger_haut"
  | "zone_a_interroger_bas"
  | "coussin_faible"
  | "au_dela_seuil_alerte"
  | "en_dessous_seuil_alerte"
  | "besoin_significatif"
  | string;

export interface RatioVerdict {
  min?: number;
  max?: number;
  seuil_alerte?: number;
  zone_confortable?: number;
  verdict: RatioVerdictLabel;
}

export interface Ratio {
  ratio_name: string; // "liquidite.current_ratio"
  ratio_value: number;
  reference_id?: string | null;
  taille?: string;
  // absent pour les ratios sans norme (ex. working_capital_frf) — jamais
  // un objet vide, vérifier la présence avant de lire `.verdict.verdict`.
  verdict?: RatioVerdict;
}

export type Severite = "elevee" | "a_surveiller";

export interface Anomalie {
  ratio_name: string;
  ratio_value: number;
  verdict: string;
  severite: Severite;
}

export type NiveauRisque = "élevé" | "modéré" | "faible";

export interface Pattern {
  id: string;
  titre: string;
  niveau_risque: NiveauRisque;
  priorite: string;
  confiance: string;
  diagnostic: string;
  hypotheses: string[];
}

export type AltmanZone = "safe" | "grey" | "distress";

export interface AltmanScore {
  model: string; // "Z" | "Z'" | "Z''"
  score: number;
  zone: AltmanZone;
  formula_used: string;
}

export interface CoherenceAltman {
  altman_zone: AltmanZone;
  divergence: string;
}

export interface Dscr {
  dscr: number;
  is_dscr_acceptable: boolean;
}

export interface TendanceIndicateur {
  valeurs: { N: number; "N-1": number; "N-2": number };
  variations: { "N_vs_N-1_pct": number; "N-1_vs_N-2_pct": number };
  tendance_recente: "Hausse" | "Baisse";
}

export interface AttestationLegale {
  source: string;
  ice?: string;
  is_compliant: boolean;
  statut_texte?: string;
}

export interface ConformiteReglementaire {
  attestations_legales: AttestationLegale[];
}

export type DecisionValue = "accord" | "a_surveiller" | "refus" | null;

export interface Contribution {
  label: string;
  points: number;
}

export interface Decision {
  decision: DecisionValue;
  score?: number;
  contributions?: Contribution[];
  justification: string | null;
  erreur?: string;
}

export interface AnalysisResult {
  client_id: string;
  thread_id: string;
  tool_error_count: number;
  secteur: string | null;
  taille: string | null;
  taille_source: string | null;
  taille_ecart: string | null;
  ratios: Ratio[];
  anomalies: Anomalie[];
  patterns: Pattern[];
  altman_score: AltmanScore | null;
  coherence_altman: CoherenceAltman | null;
  dscr: Dscr | null;
  tendances: Record<string, TendanceIndicateur> | null;
  conformite_reglementaire: ConformiteReglementaire;
  alertes_coherence: string[];
  ratios_non_comparables: unknown[];
  champs_manquants: string[];
  conclusion: string;
  decision: Decision;
}
