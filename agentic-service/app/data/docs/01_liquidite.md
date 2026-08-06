# Fiche méthodologique — Ratios de liquidité

> **Nature de ce document.** Fiche de normes sectorielles [SIMULÉ] destinée au RAG 1. Toutes les valeurs chiffrées de ce document sont fictives, construites à des fins de démonstration, et ne doivent jamais être présentées comme une donnée réelle marocaine. Segmentation utilisée : voir `00_segmentation_reference.md`.

---

## 1. Périmètre

| Champ | Formule usuelle | Ce qu'il mesure |
|---|---|---|
| `liquidite.current_ratio` | Actif circulant / Passif circulant | Capacité globale à couvrir le court terme |
| `liquidite.quick_ratio` | (Actif circulant − Stocks) / Passif circulant | Capacité à couvrir le court terme sans liquider les stocks |
| `liquidite.cash_ratio` | Trésorerie active / Passif circulant | Capacité à couvrir le court terme avec la seule trésorerie disponible |
| `liquidite.working_capital_frf` | Actif circulant − Passif circulant | Fonds de roulement en valeur absolue (montant, pas un ratio comparable directement entre entreprises) |

---

## 2. Ce que ces ratios mesurent réellement

La liquidité ne dit rien sur la rentabilité : une entreprise peut être rentable et illiquide (immobilisée dans ses stocks ou ses créances), ou peu rentable mais très liquide (activité de négoce à faible marge mais rotation rapide). C'est un ratio de **survie à court terme**, pas de performance.

Le `current_ratio` surestime la liquidité réelle dans les secteurs à stocks lents ou obsolescents (le stock inclus au numérateur n'est pas toujours convertible rapidement en cash) — d'où l'intérêt du `quick_ratio`, plus strict.

Le `working_capital_frf`, rapporté au total actif, correspond à l'opposé du `net_current_liabilities_to_assets` de la fiche solvabilité (`03_solvabilite.md`) — les deux mesurent le même déséquilibre court terme, vu sous deux angles (montant absolu vs. part du bilan).

---

## 3. Valeurs de référence par secteur [SIMULÉ] — Quick Ratio

RATIO_BENCHMARK_TAG: `liquidite.quick_ratio`

| Secteur | Min acceptable | Moyenne | Max habituel |
|---|---|---|---|
| BTP | 0,75 | 1,05 | 1,60 |
| Industrie (IND) | 0,80 | 1,10 | 1,70 |
| Commerce (COM) | 0,60 | 0,90 | 1,40 |
| Services (SRV) | 0,90 | 1,20 | 1,90 |
| Hébergement/restauration (HOT) | 0,50 | 0,80 | 1,30 |
| Transport (TRA) | 0,70 | 1,00 | 1,50 |

**Lecture** : le commerce et l'hôtellerie tolèrent structurellement un quick ratio plus bas (rotation rapide, encaissement comptant ou quasi-comptant). Le BTP et l'industrie nécessitent un coussin plus large, car leur cycle d'exploitation est plus long (cf. `04_activite.md`).

---

## 4. Valeurs de référence par taille [SIMULÉ] — Current Ratio

RATIO_BENCHMARK_TAG: `liquidite.current_ratio`

| Taille | Min acceptable | Moyenne | Max habituel |
|---|---|---|---|
| TPE | 1,00 | 1,30 | 1,90 |
| PME | 1,10 | 1,45 | 2,10 |
| GE | 1,20 | 1,60 | 2,40 |

**Lecture** : les grandes entreprises affichent en moyenne des ratios de liquidité plus confortables, en partie parce qu'elles ont un meilleur accès au financement de marché et peuvent piloter plus finement leur fonds de roulement.

---

## 5. Cash Ratio — repère unique [SIMULÉ]

RATIO_BENCHMARK_TAG: `liquidite.cash_ratio`

| Repère | Valeur |
|---|---|
| Seuil d'alerte (trésorerie très tendue) | < 0,10 |
| Zone confortable | 0,20 à 0,50 |
| Zone à interroger (trésorerie dormante excessive) | > 0,80 |

**Lecture** : un cash ratio très élevé n'est pas toujours positif — il peut signaler une mauvaise allocation du capital (trésorerie qui ne finance ni investissement ni distribution), à interroger au même titre qu'un ratio trop bas.

---

## 6. Limites de cette fiche

RATIO_BENCHMARK_TAG: `liquidite.working_capital_frf`

- Ces intervalles sont des repères de plausibilité construits pour l'exercice, non calibrés sur des données réelles.
- Le `working_capital_frf` n'a volontairement pas de valeur de référence chiffrée : c'est un montant absolu, non comparable entre entreprises de tailles différentes sans le rapporter au chiffre d'affaires ou au total actif.
