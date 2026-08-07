// Vocabulaire d'affichage pour les ratios — miroir texte de ce que le
// back-end calcule (voir agentic-service/app/tools/ratio_table_parser.py,
// benchmark_tool.py), jamais une nouvelle logique de calcul : ce module ne
// fait que formater des valeurs déjà correctes.

export const CATEGORY_LABELS = {
  liquidite: "Liquidité",
  rentabilite: "Rentabilité",
  solvabilite: "Solvabilité",
  activite: "Activité",
  cash_flow: "Cash-flow",
};

export const RATIO_LABELS = {
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

const RATIO_FORMAT = {
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

// "liquidite.current_ratio" -> { category: "liquidite", key: "current_ratio" }
export function splitRatioName(ratioName) {
  const [category, ...rest] = ratioName.split(".");
  return { category, key: rest.join(".") };
}

export function categoryLabel(category) {
  return CATEGORY_LABELS[category] || category;
}

export function ratioLabel(key) {
  return RATIO_LABELS[key] || key;
}

export function formatRatioValue(key, value) {
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
// risque réel est "anomalies" (déjà filtrée côté back-end, voir
// benchmark_tool.py::_is_anomaly), pas ce badge sur chaque ligne de la
// table complète des ratios.
const VERDICT_TONE = {
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

export function verdictTone(verdict) {
  return VERDICT_TONE[verdict] || "neutral";
}

export function verdictLabel(verdict) {
  if (!verdict) return "—";
  return verdict.replaceAll("_", " ");
}
