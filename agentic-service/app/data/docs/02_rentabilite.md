# Fiche méthodologique — Ratios de rentabilité

> **Nature de ce document.** Fiche de normes sectorielles [SIMULÉ] destinée au RAG 1. Toutes les valeurs chiffrées de ce document sont fictives, construites à des fins de démonstration. Segmentation utilisée : voir `00_segmentation_reference.md`.

---

## 1. Périmètre

| Champ | Formule usuelle | Ce qu'il mesure |
|---|---|---|
| `rentabilite.roa_return_on_assets` | Résultat net / Total actif | Capacité à générer du profit à partir des actifs employés |
| `rentabilite.roe_return_on_equity` | Résultat net / Capitaux propres | Rentabilité pour les actionnaires |
| `rentabilite.marge_nette` | Résultat net / Chiffre d'affaires | Part du CA convertie en profit final |
| `rentabilite.marge_operationnelle` | Résultat d'exploitation / CA | Rentabilité du cœur de métier, hors éléments financiers et exceptionnels |
| `rentabilite.ebitda_margin` | EBITDA / CA | Rentabilité opérationnelle avant amortissements — utile pour comparer des entreprises à intensité capitalistique différente |

---

## 2. Ce que ces ratios mesurent réellement

Le ROA et le ROE ne se lisent jamais isolément l'un de l'autre : un ROE élevé avec un ROA faible signale un effet de levier fort (l'entreprise est très endettée, ce qui amplifie mécaniquement la rentabilité pour les actionnaires — et amplifie aussi le risque en cas de retournement).

La marge opérationnelle isole la performance du métier, indépendamment de la structure de financement — c'est le ratio le plus comparable entre une entreprise très endettée et une entreprise peu endettée.

---

## 3. Valeurs de référence par secteur [SIMULÉ] — Marge opérationnelle

| Secteur | Min acceptable | Moyenne | Max habituel |
|---|---|---|---|
| BTP | 4% | 9% | 16% |
| Industrie (IND) | 5% | 11% | 20% |
| Commerce (COM) | 2% | 6% | 12% |
| Services (SRV) | 8% | 16% | 28% |
| Hébergement/restauration (HOT) | 3% | 10% | 22% |
| Transport (TRA) | 4% | 8% | 15% |

**Lecture** : le commerce a structurellement les marges les plus faibles (modèle de volume, cf. fiche 04) — une marge de 6% y est normale, alors qu'elle serait faible dans les services.

---

## 4. Valeurs de référence par secteur [SIMULÉ] — ROA

| Secteur | Min acceptable | Moyenne | Max habituel |
|---|---|---|---|
| BTP | 1,5% | 4% | 8% |
| Industrie (IND) | 2% | 5% | 10% |
| Commerce (COM) | 2% | 5% | 9% |
| Services (SRV) | 3% | 7% | 14% |
| Hébergement/restauration (HOT) | 1% | 3,5% | 7% |
| Transport (TRA) | 1,5% | 4% | 8% |

---

## 5. Valeurs de référence par taille [SIMULÉ] — ROE

| Taille | Min acceptable | Moyenne | Max habituel |
|---|---|---|---|
| TPE | 5% | 12% | 22% |
| PME | 6% | 14% | 25% |
| GE | 5% | 11% | 20% |

**Lecture** : les PME affichent souvent le ROE moyen le plus élevé de la segmentation, porté par un effet de levier plus marqué que les TPE et un capital plus concentré que les GE — un ROE élevé chez une PME doit donc être vérifié contre son niveau d'endettement (fiche 03) avant d'être interprété comme une performance pure.

---

## 6. Écart marge nette / marge opérationnelle — repère de lecture

| Situation | Interprétation |
|---|---|
| Marge nette proche de la marge opérationnelle | Résultat financier et exceptionnel neutres — performance lisible directement |
| Marge nette nettement inférieure à la marge opérationnelle | Poids financier (charges d'intérêt) ou éléments exceptionnels négatifs à investiguer |
| Marge nette supérieure à la marge opérationnelle | Produit financier ou exceptionnel positif — à ne pas considérer comme récurrent dans la projection |

---

## 7. Limites de cette fiche

- Ces intervalles sont des repères de plausibilité pour l'exercice, non calibrés sur des données réelles.
- Aucune distinction par taille n'est donnée pour la marge opérationnelle et le ROA : dans cette simulation, seul le facteur sectoriel est jugé structurant pour ces deux ratios.
