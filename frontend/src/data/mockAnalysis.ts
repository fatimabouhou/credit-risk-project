import type { AnalysisResult } from "../types/analysis";

// Jeu de données réaliste — valeurs réelles observées pour le client "data"
// pendant cette session (voir agentic-service, tests manuels), pas des
// nombres inventés. Sert à prévisualiser le design sans dépendre du quota
// Groq. Pas de dimension temporelle (tendances: null) — voir décision du
// 2026-08-07 : RatioBenchmarkChart compare valeur actuelle vs seuil, pas
// une série dans le temps.
export const mockAnalysis: AnalysisResult = {
  client_id: "data",
  thread_id: "data:8efbdcd2",
  tool_error_count: 0,
  secteur: "COM",
  taille: "PME",
  taille_source: "calculée automatiquement (chiffre d'affaires / total actif)",
  taille_ecart:
    "le total actif (255,438,857 MAD) pointerait vers GE alors que le chiffre d'affaires (55,555,048 MAD) pointe vers PME - taille retenue selon le CA (critere prioritaire), ecart a noter",
  ratios: [
    { ratio_name: "liquidite.current_ratio", ratio_value: 1.93, reference_id: "01_liquidite.md::4", verdict: { min: 1.1, max: 2.1, verdict: "dans_la_norme" } },
    { ratio_name: "liquidite.quick_ratio", ratio_value: 1.92, reference_id: "01_liquidite.md::3", verdict: { min: 0.6, max: 1.4, verdict: "au_dessus_norme" } },
    { ratio_name: "liquidite.cash_ratio", ratio_value: 1.05, reference_id: "01_liquidite.md::5", verdict: { min: 0.8, verdict: "zone_a_interroger_haut" } },
    { ratio_name: "liquidite.working_capital_frf", ratio_value: 89623127.55, reference_id: "01_liquidite.md::6" },
    { ratio_name: "rentabilite.roa_return_on_assets", ratio_value: 0.0354, reference_id: "02_rentabilite.md::4", verdict: { min: 0.02, max: 0.09, verdict: "dans_la_norme" } },
    { ratio_name: "rentabilite.roe_return_on_equity", ratio_value: 0.1028, reference_id: "02_rentabilite.md::5", verdict: { min: 0.06, max: 0.25, verdict: "dans_la_norme" } },
    { ratio_name: "rentabilite.marge_nette", ratio_value: 0.1629, reference_id: "02_rentabilite.md::6", verdict: { min: 0.01, max: 0.08, verdict: "au_dessus_norme" } },
    { ratio_name: "rentabilite.marge_operationnelle", ratio_value: 0.3204, reference_id: "02_rentabilite.md::3", verdict: { min: 0.02, max: 0.12, verdict: "au_dessus_norme" } },
    { ratio_name: "rentabilite.ebitda_margin", ratio_value: 0.3204, reference_id: "02_rentabilite.md::7", verdict: { min: 0.03, max: 0.15, verdict: "au_dessus_norme" } },
    { ratio_name: "activite.asset_turnover", ratio_value: 0.22, reference_id: "04_activite.md::4", verdict: { min: 1.2, max: 3.0, verdict: "en_dessous_norme" } },
    { ratio_name: "activite.dso_days", ratio_value: 542.7, reference_id: "04_activite.md::3", verdict: { min: 15.0, max: 45.0, verdict: "au_dessus_norme" } },
    { ratio_name: "solvabilite.liabilities_to_assets", ratio_value: 0.3762, reference_id: "03_solvabilite.md::5", verdict: { min: 0.29, max: 0.6, seuil_alerte: 0.67, verdict: "dans_la_norme" } },
    { ratio_name: "solvabilite.net_current_liabilities_to_assets", ratio_value: -0.0194, reference_id: "03_solvabilite.md::6", verdict: { max: 0.0, verdict: "favorable" } },
    { ratio_name: "solvabilite.debt_to_equity_leverage", ratio_value: 1.09, reference_id: "03_solvabilite.md::3", verdict: { min: 0.4, max: 1.5, seuil_alerte: 2.0, verdict: "dans_la_norme" } },
    { ratio_name: "solvabilite.retained_earnings_to_current_liabilities", ratio_value: 0.0, reference_id: "03_solvabilite.md::6", verdict: { max: 0.1, verdict: "coussin_faible" } },
    { ratio_name: "solvabilite.autonomie_financiere", ratio_value: 0.3445, reference_id: "03_solvabilite.md::4", verdict: { min: 0.2, seuil_alerte: 0.15, zone_confortable: 0.4, verdict: "dans_la_norme" } },
  ],
  anomalies: [
    { ratio_name: "liquidite.quick_ratio", ratio_value: 1.92, verdict: "au_dessus_norme", severite: "a_surveiller" },
    { ratio_name: "liquidite.cash_ratio", ratio_value: 1.05, verdict: "zone_a_interroger_haut", severite: "a_surveiller" },
    { ratio_name: "activite.asset_turnover", ratio_value: 0.22, verdict: "en_dessous_norme", severite: "a_surveiller" },
    { ratio_name: "activite.dso_days", ratio_value: 542.7, verdict: "au_dessus_norme", severite: "elevee" },
    { ratio_name: "solvabilite.retained_earnings_to_current_liabilities", ratio_value: 0.0, verdict: "coussin_faible", severite: "a_surveiller" },
  ],
  patterns: [
    {
      id: "ACT.001",
      titre: "Difficulté de recouvrement des créances",
      niveau_risque: "élevé",
      priorite: "élevée",
      confiance: "moyen",
      diagnostic:
        "Un délai moyen de recouvrement des créances supérieur aux références peut accroître les besoins en fonds de roulement et exercer une pression sur la trésorerie. Ce constat mérite d'être documenté avant toute conclusion, plusieurs facteurs pouvant l'expliquer.",
      hypotheses: ["délais de paiement contractuels longs, propres au secteur ou à la clientèle"],
    },
    {
      id: "ACT.004",
      titre: "Rotation des actifs faible",
      niveau_risque: "modéré",
      priorite: "surveillance",
      confiance: "moyen",
      diagnostic:
        "Un chiffre d'affaires relativement faible au regard de la taille du bilan peut indiquer une sous-utilisation des actifs ou correspondre à un modèle économique intensif en capital.",
      hypotheses: ["modèle économique intensif en capital (industrie lourde, immobilier, infrastructures)"],
    },
    {
      id: "CROSS.LIQ.001",
      titre: "Liquidité disponible élevée et recouvrement dégradé",
      niveau_risque: "modéré",
      priorite: "à investiguer",
      confiance: "moyen",
      diagnostic:
        "La coexistence d'une trésorerie importante et de délais de recouvrement très élevés est une combinaison qui mérite une analyse complémentaire : elle peut traduire des réalités très différentes selon l'origine de la liquidité disponible et la qualité effective des créances clients.",
      hypotheses: ["trésorerie issue d'une opération de financement récente, sans lien avec le poste clients"],
    },
    {
      id: "GLOB.004",
      titre: "Fragilité concentrée sur une seule dimension",
      niveau_risque: "modéré",
      priorite: "à investiguer",
      confiance: "moyen",
      diagnostic:
        "Le risque identifié semble concentré sur une seule dimension de l'analyse financière, les autres composantes restant globalement satisfaisantes. Il est recommandé de creuser spécifiquement cette dimension plutôt que de conclure à une fragilité généralisée de l'entreprise.",
      hypotheses: ["difficulté ponctuelle et circonscrite à un poste ou un processus spécifique"],
    },
    {
      id: "LIQ.001",
      titre: "Liquidité confortable",
      niveau_risque: "faible",
      priorite: "information",
      confiance: "élevé",
      diagnostic:
        "La combinaison d'un ratio de liquidité générale dans les références et d'un fonds de roulement positif est compatible avec une capacité satisfaisante à couvrir les engagements à court terme.",
      hypotheses: ["gestion équilibrée du cycle d'exploitation"],
    },
    {
      id: "RENT.001",
      titre: "Rentabilité solide et équilibrée",
      niveau_risque: "faible",
      priorite: "information",
      confiance: "élevé",
      diagnostic:
        "La cohérence entre marge nette et ROA est compatible avec une performance de rentabilité satisfaisante, sans déséquilibre apparent entre la rentabilité commerciale et la rentabilité économique.",
      hypotheses: ["modèle économique performant et maîtrisé"],
    },
  ],
  altman_score: { model: "Z''", score: 3.73, zone: "safe", formula_used: "Altman Z'' (1995)" },
  coherence_altman: null,
  dscr: { dscr: 1.17, is_dscr_acceptable: false },
  tendances: null,
  conformite_reglementaire: {
    attestations_legales: [
      { source: "CNSS", ice: "001717835000072", is_compliant: true, statut_texte: "En règle" },
      { source: "DGI", ice: "001717835000072", is_compliant: true, statut_texte: "En règle" },
    ],
  },
  alertes_coherence: [],
  ratios_non_comparables: [],
  champs_manquants: ["activite.dpo_days", "activite.cycle_exploitation_days"],
  conclusion:
    "Le score de défaillance Altman (Z'', Altman Z'' (1995)) s'établit à 3.73, ce qui place l'entreprise en zone 'safe' et suggère un risque de défaillance faible selon ce modèle. La liquidité du client est confortable, avec un ratio de liquidité générale dans les références et un fonds de roulement positif. La rentabilité est également solide et équilibrée, avec une cohérence entre la marge nette et le ROA.\n\nToutefois, il existe des signaux de risque, notamment une rotation des actifs faible et des délais de recouvrement des créances élevés. La coexistence d'une trésorerie importante et de délais de recouvrement très élevés mérite une analyse complémentaire.\n\nLa priorité d'analyse devrait porter sur l'investigation de la qualité des créances clients et l'origine de la liquidité disponible, afin de déterminer si le délai de recouvrement élevé constitue un risque réel pour la trésorerie.",
  decision: {
    decision: "refus",
    score: 9,
    contributions: [
      { label: "Pattern ACT.001 (risque élevé)", points: 3 },
      { label: "DSCR insuffisant", points: 3 },
      { label: "Pattern ACT.004 (risque modéré)", points: 1 },
      { label: "Pattern CROSS.LIQ.001 (risque modéré)", points: 1 },
      { label: "Pattern GLOB.004 (risque modéré)", points: 1 },
    ],
    justification:
      "La décision de refus est motivée par un score DSCR de 1,17, en dessous de la limite acceptable, et par le pattern ACT.001 signalant une difficulté de recouvrement des créances, avec un délai moyen de recouvrement élevé. Bien que le score Altman Z'' soit dans la zone «safe» et que la liquidité générale soit confortable, les risques de recouvrement et de couverture de dette insuffisante justifient le refus.",
  },
};
