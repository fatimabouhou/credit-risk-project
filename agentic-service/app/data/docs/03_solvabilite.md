# Fiche méthodologique — Ratios de solvabilité

> **Nature de ce document.** Fiche de normes sectorielles [SIMULÉ] destinée au RAG 1. Toutes les valeurs chiffrées de ce document sont fictives, construites à des fins de démonstration, et ne doivent jamais être présentées comme une donnée réelle marocaine. Segmentation utilisée : voir `00_segmentation_reference.md`.

---

## 1. Périmètre

| Champ | Formule usuelle | Ce qu'il mesure |
|---|---|---|
| `solvabilite.liabilities_to_assets` | Total dettes / Total actif | Part de l'actif financée par des tiers (dette) plutôt que par les actionnaires |
| `solvabilite.autonomie_financiere` | Capitaux propres / Total actif | Part de l'actif financée par les fonds propres — miroir du ratio précédent |
| `solvabilite.debt_to_equity_leverage` | Total dettes / Capitaux propres | Niveau d'endettement rapporté aux fonds propres — mesure directe du levier financier |
| `solvabilite.net_current_liabilities_to_assets` | (Passif circulant − Actif circulant) / Total actif | Poids du besoin de financement à court terme non couvert dans le bilan total (signe négatif = actif circulant > passif circulant, situation favorable) |
| `solvabilite.retained_earnings_to_current_liabilities` | Report à nouveau + Réserves / Passif circulant | Capacité des résultats accumulés (non distribués) à absorber le passif court terme — indicateur de solidité historique, proche de l'esprit du ratio RE/TA du Z-score d'Altman |

**Relation entre les deux premiers ratios** : `liabilities_to_assets` + `autonomie_financiere` = 1 par construction (tout l'actif est financé soit par la dette, soit par les fonds propres). Si la somme observée s'écarte sensiblement de 1, cela signale une incohérence de calcul ou de périmètre (ex. dette totale mal définie) à vérifier avant toute interprétation.

---

## 2. Ce que ces ratios mesurent réellement

La solvabilité répond à une question différente de la liquidité : la liquidité mesure la capacité à honorer le court terme, la solvabilité mesure la capacité à absorber un choc en liquidant l'ensemble du bilan — c'est un ratio de **résistance structurelle**, pertinent notamment en cas de retournement prolongé ou de scénario de défaut.

Le `debt_to_equity_leverage` doit toujours être lu avec le ROE (fiche 02) : un levier élevé qui s'accompagne d'un ROE élevé peut être une stratégie de financement assumée et maîtrisée ; un levier élevé avec un ROE faible ou en baisse est un signal de fragilité qui mérite d'être investigué en priorité.

Le `net_current_liabilities_to_assets` recoupe le `working_capital_frf` de la fiche liquidité, mais rapporté au total actif — il permet de comparer ce besoin de financement entre entreprises de tailles différentes, ce que le FRF en valeur absolue ne permet pas.

---

## 3. Valeurs de référence par secteur [SIMULÉ] — Debt to Equity (Levier)

| Secteur | Min (faible levier) | Moyenne | Max acceptable | Seuil d'alerte |
|---|---|---|---|---|
| BTP | 0,60 | 1,30 | 2,00 | > 2,50 |
| Industrie (IND) | 0,50 | 1,10 | 1,80 | > 2,20 |
| Commerce (COM) | 0,40 | 0,90 | 1,50 | > 2,00 |
| Services (SRV) | 0,20 | 0,60 | 1,10 | > 1,50 |
| Hébergement/restauration (HOT) | 0,80 | 1,60 | 2,40 | > 3,00 |
| Transport (TRA) | 0,70 | 1,40 | 2,10 | > 2,60 |

**Lecture** : le BTP, l'hôtellerie et le transport tolèrent structurellement un levier plus élevé (actifs immobilisés importants, financement bancaire adossé à des actifs physiques). Les services, peu capitalistiques, doivent rester plus prudents sur l'endettement — un `debt_to_equity` de 1,5 y est déjà un signal fort, alors qu'il serait dans la norme haute en hôtellerie.

---

## 4. Valeurs de référence par taille [SIMULÉ] — Autonomie financière

| Taille | Seuil d'alerte (sous-capitalisation) | Min acceptable | Moyenne | Zone confortable |
|---|---|---|---|---|
| TPE | < 15% | 20% | 28% | > 35% |
| PME | < 15% | 20% | 30% | > 40% |
| GE | < 10% | 15% | 25% | > 35% |

**Lecture** : les grandes entreprises, ayant un accès plus large au financement de marché, peuvent fonctionner durablement avec une autonomie financière plus faible sans que cela signale une fragilité équivalente à celle d'une TPE ou PME dans la même situation.

---

## 5. Repères uniques [SIMULÉ] — Structure court terme

| Ratio | Repère | Interprétation |
|---|---|---|
| `net_current_liabilities_to_assets` | < 0 | Actif circulant supérieur au passif circulant — situation structurellement favorable |
| `net_current_liabilities_to_assets` | 0 à 5% | Zone neutre, à surveiller si la tendance se dégrade sur 3 exercices |
| `net_current_liabilities_to_assets` | > 5% | Besoin de financement court terme significatif au regard du bilan total — à recouper avec le `working_capital_frf` et le `current_ratio` (fiche 01) |
| `retained_earnings_to_current_liabilities` | < 0,10 | Faible coussin de résultats accumulés face au passif court terme — vigilance surtout si l'entreprise est jeune ou a distribué fortement ses résultats |
| `retained_earnings_to_current_liabilities` | 0,10 à 0,40 | Niveau courant, sans signal particulier |
| `retained_earnings_to_current_liabilities` | > 0,40 | Coussin de solidité confortable, historique de rétention de résultats significatif |

---

## 6. Limites de cette fiche

- Ces intervalles sont des repères de plausibilité construits pour l'exercice, non calibrés sur des données réelles ni sur les covenants effectivement pratiqués par les banques marocaines.
- Aucune distinction par taille n'est donnée pour le `debt_to_equity_leverage` et par secteur pour l'`autonomie_financiere` : dans cette simulation, un seul facteur (secteur ou taille) est jugé structurant par ratio, à l'image du choix fait dans `02_rentabilite.md`.
- Le `retained_earnings_to_current_liabilities` n'a pas de déclinaison sectorielle : sa lecture dépend surtout de l'âge de l'entreprise et de sa politique de distribution, deux facteurs non capturés par la segmentation secteur/taille de ce référentiel.
