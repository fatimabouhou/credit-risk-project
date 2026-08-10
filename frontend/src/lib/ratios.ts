// Vocabulaire d'affichage pour les ratios — miroir texte de ce que le
// back-end calcule (voir agentic-service/app/tools/ratio_table_parser.py,
// benchmark_tool.py), jamais une nouvelle logique de calcul.

export type Tone = "success" | "warning" | "danger" | "neutral";

export const CATEGORY_LABELS: Record<string, string> = {
  liquidite: "Liquidité",
  rentabilite: "Rentabilité",
  solvabilite: "Solvabilité",
  activite: "Activité",
  cash_flow: "Cash-flow",
};

export const CATEGORY_ORDER = ["liquidite", "rentabilite", "activite", "solvabilite"];

export const RATIO_LABELS: Record<string, string> = {
  current_ratio: "Current Ratio",
  quick_ratio: "Quick Ratio",
  cash_ratio: "Cash Ratio",
  working_capital_frf: "Fonds de roulement",
  roa_return_on_assets: "ROA",
  roe_return_on_equity: "ROE",
  marge_nette: "Marge nette",
  marge_operationnelle: "Marge opérationnelle",
  ebitda_margin: "Marge EBITDA",
  asset_turnover: "Rotation des actifs",
  dso_days: "DSO",
  dio_days: "DIO",
  dpo_days: "DPO",
  cycle_exploitation_days: "Cycle d'exploitation",
  liabilities_to_assets: "Endettement global",
  net_current_liabilities_to_assets: "Passifs courants nets / Actifs",
  debt_to_equity_leverage: "Debt-to-Equity",
  retained_earnings_to_current_liabilities: "Réserves / Passifs courants",
  autonomie_financiere: "Autonomie financière",
  cfo_to_total_debt: "CFO / Dettes totales",
  cfo_to_total_assets: "CFO / Actif total",
  free_cash_flow_to_total_debt: "FCF / Dettes totales",
};

type ValueFormat = "percent" | "days" | "currency" | "decimal";

const RATIO_FORMAT: Record<string, ValueFormat> = {
  current_ratio: "decimal",
  quick_ratio: "decimal",
  cash_ratio: "decimal",
  working_capital_frf: "currency",
  roa_return_on_assets: "percent",
  roe_return_on_equity: "percent",
  marge_nette: "percent",
  marge_operationnelle: "percent",
  ebitda_margin: "percent",
  asset_turnover: "decimal",
  dso_days: "days",
  dio_days: "days",
  dpo_days: "days",
  cycle_exploitation_days: "days",
  liabilities_to_assets: "percent",
  net_current_liabilities_to_assets: "percent",
  debt_to_equity_leverage: "decimal",
  retained_earnings_to_current_liabilities: "percent",
  autonomie_financiere: "percent",
  cfo_to_total_debt: "percent",
  cfo_to_total_assets: "percent",
  free_cash_flow_to_total_debt: "percent",
};

export function splitRatioName(ratioName: string): { category: string; key: string } {
  const [category, ...rest] = ratioName.split(".");
  return { category, key: rest.join(".") };
}

export function categoryLabel(category: string): string {
  return CATEGORY_LABELS[category] || category;
}

export function ratioLabel(key: string): string {
  return RATIO_LABELS[key] || key;
}

export function formatRatioValue(key: string, value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const format = RATIO_FORMAT[key] || "decimal";
  switch (format) {
    case "percent":
      return `${(value * 100).toFixed(2)}%`;
    case "days":
      return `${value.toFixed(1)} j`;
    case "currency":
      return `${Math.round(value).toLocaleString("fr-FR")} MAD`;
    default:
      return value.toFixed(2);
  }
}

// Teinte d'affichage indicative seulement — la liste faisant foi pour le
// risque réel est "anomalies" (déjà filtrée côté back-end), pas ce badge
// sur chaque ligne de ratio.
const VERDICT_TONE: Record<string, Tone> = {
  dans_la_norme: "success",
  favorable: "success",
  en_dessous_norme: "warning",
  zone_a_interroger_haut: "warning",
  zone_a_interroger_bas: "warning",
  coussin_faible: "warning",
  au_dela_seuil_alerte: "danger",
  en_dessous_seuil_alerte: "danger",
  besoin_significatif: "danger",
};

export function verdictTone(verdict: string | undefined): Tone {
  if (!verdict) return "neutral";
  return VERDICT_TONE[verdict] || "neutral";
}

export function verdictLabel(verdict: string | undefined): string {
  if (!verdict) return "—";
  return verdict.replaceAll("_", " ");
}

// Position visuelle (0-100) de la valeur dans sa fourchette de référence —
// affichage seulement, jamais une donnée qui existe côté back-end. Retourne
// null quand la fourchette ne permet pas une lecture honnête (ex. ni min ni
// max, comme working_capital_frf : montant absolu, pas de norme chiffrée).
export function computeRatioProgress(
  value: number,
  verdict: { min?: number; max?: number } | undefined
): number | null {
  if (!verdict) return null;
  const { min, max } = verdict;
  if (min !== undefined && max !== undefined && max > min) {
    return Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
  }
  if (max !== undefined && max !== 0) {
    return Math.max(0, Math.min(100, (value / (max * 1.5)) * 100));
  }
  if (min !== undefined && min !== 0) {
    return Math.max(0, Math.min(100, (value / (min * 2)) * 100));
  }
  return null;
}

export const NIVEAU_RISQUE_TONE: Record<string, Tone> = {
  "élevé": "danger",
  "modéré": "warning",
  "faible": "success",
};

export const SEVERITE_TONE: Record<string, Tone> = {
  elevee: "danger",
  a_surveiller: "warning",
};

export const ALTMAN_ZONE_TONE: Record<string, Tone> = {
  distress: "danger",
  grey: "warning",
  safe: "success",
};

export const ALTMAN_ZONE_LABELS: Record<string, string> = {
  safe: "Zone sûre",
  grey: "Zone grise",
  distress: "Zone de détresse",
};
