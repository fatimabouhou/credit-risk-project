# Fiche méthodologique — Référentiel de segmentation

> **Nature de ce document.** Fiche de normes sectorielles [SIMULÉ] destinée au RAG 1. Toutes les valeurs de ce document sont fictives, construites à des fins de démonstration, et ne doivent jamais être présentées comme une donnée réelle marocaine. Ce fichier est la clé de lecture commune à `01_liquidite.md`, `02_rentabilite.md`, `03_solvabilite.md` et à la fiche activité/cash flow/DSCR.

---

## 1. Pourquoi ce fichier

Toutes les fiches de ratios donnent des seuils **par secteur** et/ou **par taille**. Sans une règle de classement univoque, l'agent d'analyse ne peut pas choisir la bonne ligne de seuils. Ce fichier fixe :
1. la liste fermée des codes secteur et taille utilisés dans tout le référentiel,
2. les critères de classement,
3. la règle à appliquer en cas d'ambiguïté ou de donnée manquante.

---

## 2. Segmentation sectorielle

| Code | Secteur | Activités typiques incluses |
|---|---|---|
| `BTP` | Bâtiment & Travaux Publics | Construction, promotion immobilière, gros œuvre, second œuvre, travaux publics |
| `IND` | Industrie | Fabrication, transformation, agroalimentaire industriel, textile, mécanique, chimie |
| `COM` | Commerce | Négoce, distribution, import-export, grande distribution, e-commerce marchand |
| `SRV` | Services | Conseil, ingénierie, IT, professions libérales, services aux entreprises, éducation privée |
| `HOT` | Hébergement / Restauration | Hôtellerie, restauration, tourisme réceptif |
| `TRA` | Transport | Transport de marchandises, transport de personnes, logistique, messagerie |

**Règle en cas d'activité mixte** : classer selon l'activité qui génère la majorité du chiffre d'affaires (>50%). Si aucune activité ne dépasse 50% du CA, utiliser le secteur de l'immobilisation la plus significative au bilan.

**Secteur non couvert par cette liste** (ex. agriculture, finance, extraction minière) : ne pas forcer un rattachement à l'un des 6 codes ci-dessus. Signaler l'absence de norme sectorielle plutôt que d'appliquer un seuil non pertinent.

---

## 3. Segmentation par taille [SIMULÉ]

RATIO_BENCHMARK_TAG: segmentation.taille

| Code | Taille | Chiffre d'affaires annuel | Total actif | Effectif |
|---|---|---|---|---|
| `TPE` | Très Petite Entreprise | < 10 000 000 MAD | < 8 000 000 MAD | < 10 salariés |
| `PME` | Petite et Moyenne Entreprise | 10 000 000 à 175 000 000 MAD | 8 000 000 à 150 000 000 MAD | 10 à 200 salariés |
| `GE` | Grande Entreprise | > 175 000 000 MAD | > 150 000 000 MAD | > 200 salariés |

**Règle de classement** : le chiffre d'affaires est le critère prioritaire. Si le CA et le total actif pointent vers deux tailles différentes (cas d'une entreprise capitalistique à faible rotation), retenir la taille correspondant au CA et signaler l'écart en commentaire — il peut lui-même être un signal utile (ex. actif très supérieur au CA dans une foncière ou un holding).

**Cas limite** : une entreprise à cheval sur deux bornes (ex. CA = 175 100 000 MAD) est classée dans la catégorie supérieure.

---

## 4. Application au dossier en cours

Avant d'invoquer les seuils de `01_liquidite.md`, `02_rentabilite.md`, `03_solvabilite.md` ou de la fiche activité, l'agent doit déterminer et tracer explicitement, pour l'exercice N :
- le `secteur_code` (un des 6 codes ci-dessus, ou "non couvert"),
- le `taille_code` (`TPE`, `PME` ou `GE`),
- la base du classement (CA, total actif, ou les deux si écart).

Si l'un des deux champs ne peut pas être déterminé à partir des données disponibles (ex. absence de code d'activité, absence de CA fiable), l'agent doit le signaler explicitement dans le rapport plutôt que de choisir un secteur ou une taille par défaut.

---

## 5. Limites de cette fiche

- Les seuils de taille sont un repère de plausibilité pour l'exercice, non calibrés sur la réglementation marocaine réelle (loi PME, définitions BAM, etc.).
- La liste sectorielle à 6 codes est volontairement simplifiée ; une entreprise réelle peut nécessiter une segmentation plus fine (sous-secteurs) non couverte ici.
