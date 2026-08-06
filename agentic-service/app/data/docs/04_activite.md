# Fiche méthodologique — Ratios d'activité

> **Nature de ce document.** Fiche de normes sectorielles [SIMULÉ] destinée au RAG 1. Toutes les valeurs chiffrées de ce document sont fictives, construites à des fins de démonstration, et ne doivent jamais être présentées comme une donnée réelle marocaine. Segmentation utilisée : voir `00_segmentation_reference.md`.

---

## 1. Périmètre

| Champ | Formule usuelle | Ce qu'il mesure |
|---|---|---|
| `activite.asset_turnover` | Chiffre d'affaires / Total actif | Efficacité avec laquelle les actifs sont utilisés pour générer des ventes |
| `activite.dso_days` | (Créances clients / Chiffre d'affaires TTC) × 365 | Délai moyen de recouvrement des créances clients (Days Sales Outstanding) |
| `activite.dpo_days` | (Dettes fournisseurs / Achats TTC) × 365 | Délai moyen de règlement des fournisseurs (Days Payable Outstanding) |
| `activite.dio_days` | (Stocks / Coût des ventes) × 365 | Délai moyen d'écoulement des stocks (Days Inventory Outstanding) |
| `activite.cycle_exploitation_days` | DIO + DSO − DPO | Besoin de financement du cycle d'exploitation en jours (Cash Conversion Cycle) |

**Note de champ manquant** : `activite.dio_days` fait partie du périmètre théorique de cette fiche mais n'apparaît pas dans le JSON de sortie actuel (`ratios_financiers_n.activite`) ; de même, `cycle_exploitation_days` ne peut pas être calculé si `dpo_days` est `null`. Ces trous doivent être signalés par l'agent plutôt que masqués par une valeur par défaut.

---

## 2. Ce que ces ratios mesurent réellement

Le cycle d'exploitation (DSO + DIO − DPO) est le pendant, en jours, du `working_capital_frf` de `01_liquidite.md` et du `net_current_liabilities_to_assets` de `03_solvabilite.md` : les trois mesurent le même besoin de financement court terme sous des unités différentes (montant, part du bilan, durée). Une lecture croisée cohérente entre ces trois ratios renforce la confiance dans le diagnostic ; une divergence forte entre eux doit être investiguée avant conclusion.

Le `asset_turnover`, rapproché du ROA (`02_rentabilite.md`), permet de décomposer la rentabilité des actifs : ROA = marge nette × asset_turnover. Un ROA faible avec un `asset_turnover` normal pointe vers un problème de marge ; un ROA faible avec un `asset_turnover` très bas pointe vers une sous-utilisation des actifs (surinvestissement, actifs improductifs).

---

## 3. Valeurs de référence par secteur [SIMULÉ] — DSO, DPO et DIO

RATIO_BENCHMARK_TAG: `activite.dso_days`
RATIO_BENCHMARK_TAG: `activite.dpo_days`
RATIO_BENCHMARK_TAG: `activite.dio_days`

| Secteur | DSO (Clients) moyen | DPO (Fournisseurs) moyen | DIO (Stocks) moyen |
|---|---|---|---|
| BTP | 80 à 120 jours | 60 à 90 jours | 30 à 60 jours |
| Industrie (IND) | 60 à 90 jours | 45 à 60 jours | 45 à 90 jours |
| Commerce (COM) | 15 à 45 jours | 45 à 60 jours | 30 à 60 jours |
| Services (SRV) | 30 à 60 jours | 30 à 45 jours | < 5 jours |
| Hébergement/restauration (HOT) | < 15 jours | 30 à 45 jours | < 15 jours |
| Transport (TRA) | 45 à 60 jours | 45 à 60 jours | < 15 jours |

---

## 4. Valeurs de référence par secteur [SIMULÉ] — Asset Turnover

RATIO_BENCHMARK_TAG: `activite.asset_turnover`

| Secteur | Min acceptable | Moyenne | Max habituel |
|---|---|---|---|
| BTP | 0,50 | 0,90 | 1,40 |
| Industrie (IND) | 0,60 | 1,00 | 1,60 |
| Commerce (COM) | 1,20 | 2,00 | 3,00 |
| Services (SRV) | 0,70 | 1,20 | 1,90 |
| Hébergement/restauration (HOT) | 0,40 | 0,70 | 1,10 |
| Transport (TRA) | 0,50 | 0,85 | 1,30 |

**Lecture** : le commerce affiche l'`asset_turnover` le plus élevé (modèle de volume à faible marge, cf. `02_rentabilite.md`), l'hôtellerie le plus bas (actifs immobilisés lourds — bâti, équipements — pour un CA plus modeste).

---

## 5. Règles d'interprétation — Cycle d'exploitation

| Situation | Interprétation |
|---|---|
| `cycle_exploitation_days` < 0 | L'entreprise génère une ressource en fonds de roulement (typique du commerce de détail ou de l'hébergement, qui encaissent comptant mais paient à délai) |
| `dso_days` > `dpo_days` | L'entreprise paie ses fournisseurs avant d'être payée par ses clients — besoin de financement structurel à couvrir par un fonds de roulement suffisant ou des crédits de trésorerie |
| `dso_days` très supérieur à la fourchette sectorielle haute | Signal fort à investiguer en priorité : recouvrement dégradé, litige client, ou erreur de calcul (créances clients mal renseignées, CA TTC incohérent) |

---

## 6. Limites de cette fiche

- Ces intervalles sont des repères de plausibilité construits pour l'exercice, non calibrés sur des données réelles.
- Aucune distinction par taille n'est donnée dans cette fiche : dans cette simulation, seul le facteur sectoriel est jugé structurant pour les ratios d'activité.
