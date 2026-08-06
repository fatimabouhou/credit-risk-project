# Base de connaissances — Patterns de rentabilité

> Ratios mobilisés dans ce fichier : Marge brute, Marge opérationnelle, Marge nette, ROA, ROE, Asset Turnover.
> Les patterns de rentabilité isolée doivent être lus avec prudence : un même niveau de marge ou de ROE peut correspondre à des réalités économiques très différentes selon le secteur et la structure de financement.

---

## RENT.001 — Rentabilité solide et équilibrée

**Catégorie :** rentabilité

**Objectif :** Identifier une cohérence d'ensemble entre les différents niveaux de rentabilité (commerciale, économique, financière).

**Conditions obligatoires (required) :**
- Marge nette : dans_la_norme ou au_dessus_norme
- ROA : dans_la_norme ou au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- ROE : dans_la_norme ou au_dessus_norme

**Niveau de confiance :** élevé

**Diagnostic :**
La cohérence entre marge nette et ROA est compatible avec une performance de rentabilité satisfaisante, sans déséquilibre apparent entre la rentabilité commerciale et la rentabilité économique. Ce constat statique ne préjuge pas de la soutenabilité de cette performance dans le temps.

**Hypothèses possibles :**
- modèle économique performant et maîtrisé
- positionnement de marché favorable
- structure de coûts optimisée

**Actions d'investigation :**
- vérifier la stabilité de la performance sur plusieurs exercices
- comparer aux moyennes du secteur d'activité

**Niveau de risque :** faible

**Priorité :** information

**Références :** 02_rentabilite_patterns.md

---

## RENT.002 — Rentabilité opérationnelle sous pression malgré une marge brute correcte

**Catégorie :** rentabilité

**Objectif :** Isoler un écart entre performance commerciale (marge brute) et performance opérationnelle (marge d'exploitation), révélateur d'un poids important des charges de structure.

**Conditions obligatoires (required) :**
- Marge opérationnelle : en_dessous_norme
- Marge brute : dans_la_norme ou au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- Asset Turnover : dans_la_norme

**Niveau de confiance :** moyen

**Diagnostic :**
L'écart entre une marge brute correcte et une marge opérationnelle en retrait peut résulter d'un poids significatif des charges d'exploitation hors coût des ventes (charges de structure, frais commerciaux, frais administratifs). Cette lecture reste une hypothèse à confirmer par une analyse détaillée du compte de résultat.

**Hypothèses possibles :**
- charges de structure disproportionnées par rapport à l'activité
- investissements commerciaux ou marketing significatifs sur la période
- phase de montée en charge (charges fixes non encore absorbées par le volume d'activité)

**Actions d'investigation :**
- décomposer les charges d'exploitation par nature
- comparer le ratio de charges de structure sur chiffre d'affaires au secteur
- vérifier si la période correspond à une phase d'investissement ou de restructuration

**Niveau de risque :** modéré

**Priorité :** à investiguer

**Références :** 02_rentabilite_patterns.md

---

## RENT.003 — ROE porté par l'effet de levier financier

**Catégorie :** rentabilité

**Objectif :** Distinguer la part de la rentabilité des capitaux propres attribuable à la performance opérationnelle de celle attribuable au levier financier.

**Conditions obligatoires (required) :**
- ROE : au_dessus_norme
- ROA : dans_la_norme

**Conditions renforçant la confiance (optional) :**
- Debt-to-Equity : au_dessus_norme (voir 03_solvabilite_patterns.md)

**Niveau de confiance :** moyen

**Diagnostic :**
Un ROE supérieur aux références alors que le ROA reste dans la norme est compatible avec un effet de levier financier significatif : la rentabilité des capitaux propres serait alors en partie portée par le recours à l'endettement plutôt que par la seule performance opérationnelle. Cette lecture amplifie tant la rentabilité que le risque en cas de retournement d'activité, et gagne à être confirmée par le niveau d'endettement réel.

**Hypothèses possibles :**
- structure de financement à fort effet de levier, assumée et maîtrisée
- base de capitaux propres réduite (distribution de dividendes, rachats d'actions)
- endettement récent finançant un projet de croissance

**Actions d'investigation :**
- rapprocher du pattern SOLV correspondant (Debt-to-Equity, Interest Coverage)
- décomposer le ROE selon une approche DuPont (marge nette × rotation des actifs × levier financier)
- vérifier l'évolution des capitaux propres sur les derniers exercices

**Niveau de risque :** modéré

**Priorité :** à investiguer

**Références :** 02_rentabilite_patterns.md, 03_solvabilite_patterns.md

---

## RENT.004 — Écart marge brute / marge nette à documenter

**Catégorie :** rentabilité

**Objectif :** Repérer un écart important entre marge brute et marge nette non expliqué par le seul niveau opérationnel, orientant vers les charges financières, exceptionnelles ou fiscales.

**Conditions obligatoires (required) :**
- Marge brute : dans_la_norme
- Marge nette : en_dessous_norme

**Conditions renforçant la confiance (optional) :**
- Marge opérationnelle : dans_la_norme (écart concentré sous la ligne d'exploitation)

**Niveau de confiance :** moyen

**Diagnostic :**
Un écart marqué entre une marge brute conforme aux références et une marge nette en retrait peut résulter d'éléments situés sous le résultat opérationnel : charges financières, éléments exceptionnels ou charge fiscale. L'origine précise de cet écart ne peut être déterminée sans analyse du compte de résultat détaillé.

**Hypothèses possibles :**
- poids important des charges financières lié à l'endettement
- éléments exceptionnels non récurrents (dépréciations, litiges, restructuration)
- taux d'imposition effectif élevé sur la période

**Actions d'investigation :**
- isoler la contribution du résultat financier et du résultat exceptionnel
- vérifier la récurrence de ces éléments sur plusieurs exercices
- rapprocher du niveau d'endettement (Interest Coverage, Debt-to-Equity)

**Niveau de risque :** modéré

**Priorité :** à investiguer

**Références :** 02_rentabilite_patterns.md, 03_solvabilite_patterns.md

---

## RENT.005 — Marge brute structurellement faible

**Catégorie :** rentabilité

**Objectif :** Identifier une faiblesse de la marge commerciale, déterminante pour la rentabilité en aval.

**Conditions obligatoires (required) :**
- Marge brute : en_dessous_norme

**Conditions renforçant la confiance (optional) :**
- Constat stable sur plusieurs exercices

**Niveau de confiance :** moyen

**Diagnostic :**
Une marge brute inférieure aux références du secteur peut résulter d'une pression concurrentielle sur les prix, d'un coût des ventes élevé, ou d'un positionnement de marché spécifique. Ce constat conditionne fortement la rentabilité en aval et mérite d'être resitué dans le contexte concurrentiel de l'entreprise.

**Hypothèses possibles :**
- pression concurrentielle sur les prix de vente
- hausse du coût des matières premières ou des approvisionnements non répercutée
- positionnement stratégique volontaire sur des volumes plutôt que sur la marge

**Actions d'investigation :**
- comparer la marge brute aux acteurs comparables du secteur
- analyser l'évolution du coût des ventes et des prix de vente sur la période
- vérifier l'existence d'une stratégie de volume assumée

**Niveau de risque :** modéré

**Priorité :** surveillance

**Références :** 02_rentabilite_patterns.md

---

## RENT.006 — Rentabilité négative sur la période

**Catégorie :** rentabilité

**Objectif :** Signaler une perte nette sur l'exercice analysé, situation nécessitant systématiquement une revue approfondie.

**Conditions obligatoires (required) :**
- Marge nette : négatif
- ROA : négatif

**Conditions renforçant la confiance (optional) :**
- Marge opérationnelle : négatif

**Niveau de confiance :** élevé

**Diagnostic :**
L'entreprise enregistre une perte nette sur la période analysée. Ce constat impose une revue approfondie des causes, qui peuvent être conjoncturelles, structurelles, ou liées à des éléments exceptionnels ; il ne permet pas, en l'état, de conclure seul à un risque de pérennité.

**Hypothèses possibles :**
- choc conjoncturel ponctuel (baisse d'activité, événement exceptionnel)
- dégradation structurelle du modèle économique
- phase d'investissement ou de restructuration pesant temporairement sur le résultat
- dépréciation d'actifs comptabilisée sur l'exercice

**Actions d'investigation :**
- distinguer la part opérationnelle et la part exceptionnelle de la perte
- comparer avec les résultats des exercices précédents
- évaluer l'impact sur les capitaux propres et la solvabilité (rapprocher de 03_solvabilite_patterns.md)

**Niveau de risque :** élevé

**Priorité :** élevée

**Références :** 02_rentabilite_patterns.md, 03_solvabilite_patterns.md

---

## RENT.007 — ROE atteignant un niveau inhabituel

**Catégorie :** rentabilité

**Objectif :** Signaler un ROE isolément très élevé, dont l'origine (performance réelle ou effet mécanique) doit être vérifiée.

**Conditions obligatoires (required) :**
- ROE : zone_a_interroger_haut

**Conditions renforçant la confiance (optional) :**
- Marge nette : dans_la_norme (écarte une explication par une rentabilité commerciale exceptionnelle)

**Niveau de confiance :** faible

**Diagnostic :**
Un ROE atteignant un niveau inhabituellement élevé peut refléter une performance opérationnelle exceptionnelle, mais également un effet mécanique lié à une base de capitaux propres réduite. La seule lecture du ROE ne permet pas de trancher entre ces hypothèses.

**Hypothèses possibles :**
- performance opérationnelle réellement exceptionnelle sur la période
- base de capitaux propres très réduite (endettement élevé, rachats d'actions, distribution importante)
- effet de base lié à un exercice atypique (capitaux propres négatifs redevenus positifs, par exemple)

**Actions d'investigation :**
- décomposer le ROE selon une approche DuPont
- vérifier le niveau et l'évolution récente des capitaux propres
- rapprocher du pattern CROSS correspondant (ROE élevé + endettement élevé)

**Niveau de risque :** modéré

**Priorité :** à investiguer

**Références :** 02_rentabilite_patterns.md, 05_patterns_croises.md

---

## RENT.008 — Rentabilité opérationnelle soutenue malgré une rotation des actifs faible

**Catégorie :** rentabilité

**Objectif :** Caractériser un modèle économique à forte marge plutôt qu'à fort volume, en croisant marge opérationnelle et rotation des actifs.

**Conditions obligatoires (required) :**
- Asset Turnover : en_dessous_norme
- Marge opérationnelle : au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- Marge brute : au_dessus_norme

**Niveau de confiance :** moyen

**Diagnostic :**
La combinaison d'une rotation des actifs faible et d'une marge opérationnelle élevée est compatible avec un modèle économique privilégiant la marge plutôt que le volume d'activité. Cette configuration n'est pas en soi un signal de risque mais caractérise un profil économique spécifique, à confirmer au regard du secteur.

**Hypothèses possibles :**
- stratégie de différenciation ou de positionnement haut de gamme
- activité intensive en capital avec cycle de rotation long (immobilier, infrastructures)
- phase d'investissement récent gonflant temporairement la base d'actifs

**Actions d'investigation :**
- comparer le couple marge/rotation aux références du secteur d'activité
- vérifier si la base d'actifs inclut des investissements récents non encore pleinement productifs

**Niveau de risque :** faible

**Priorité :** information

**Références :** 02_rentabilite_patterns.md, 04_activite_patterns.md
