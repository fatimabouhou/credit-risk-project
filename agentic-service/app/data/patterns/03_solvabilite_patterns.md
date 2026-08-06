# Base de connaissances — Patterns de solvabilité

> Ratios mobilisés dans ce fichier : Debt Ratio, Debt-to-Equity, Interest Coverage, Equity Ratio.

---

## SOLV.001 — Structure financière équilibrée

**Catégorie :** solvabilité

**Objectif :** Identifier une structure de financement présentant un équilibre raisonnable entre dettes et capitaux propres, avec une capacité de couverture des charges financières satisfaisante.

**Conditions obligatoires (required) :**
- Debt Ratio : dans_la_norme
- Interest Coverage : dans_la_norme ou au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- Debt-to-Equity : dans_la_norme

**Niveau de confiance :** élevé

**Diagnostic :**
La structure de financement repose sur un équilibre raisonnable entre dettes et capitaux propres, avec une capacité de couverture des charges financières qui apparaît satisfaisante à la date d'analyse.

**Hypothèses possibles :**
- politique financière prudente et constante
- structure de financement adaptée au profil de risque de l'activité

**Actions d'investigation :**
- vérifier la stabilité de la structure financière sur plusieurs exercices
- comparer aux références du secteur d'activité

**Niveau de risque :** faible

**Priorité :** information

**Références :** 03_solvabilite_patterns.md

---

## SOLV.002 — Endettement supérieur aux références

**Catégorie :** solvabilité

**Objectif :** Signaler un niveau d'endettement significativement supérieur aux références, accroissant la dépendance vis-à-vis des créanciers.

**Conditions obligatoires (required) :**
- Debt-to-Equity : au_dessus_norme
- Debt Ratio : au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- Interest Coverage : en_dessous_norme

**Niveau de confiance :** élevé

**Diagnostic :**
Un niveau d'endettement nettement supérieur aux références est susceptible d'accroître la dépendance de l'entreprise vis-à-vis de ses créanciers et sa sensibilité à une hausse des taux ou à un ralentissement de l'activité. Ce constat doit être apprécié au regard de la capacité de l'entreprise à couvrir le coût de cette dette (cf. Interest Coverage).

**Hypothèses possibles :**
- financement d'un projet de croissance ou d'investissement structurant
- recours à l'endettement pour optimiser le coût moyen pondéré du capital
- dégradation progressive de la structure financière sur plusieurs exercices

**Actions d'investigation :**
- analyser la nature et l'échéance de la dette (court terme vs long terme)
- vérifier l'affectation des fonds empruntés (investissement, exploitation, refinancement)
- rapprocher du pattern SOLV.003 (couverture des intérêts)

**Niveau de risque :** élevé

**Priorité :** élevée

**Références :** 03_solvabilite_patterns.md

---

## SOLV.003 — Couverture des intérêts fragile

**Catégorie :** solvabilité

**Objectif :** Identifier une capacité insuffisante du résultat d'exploitation à couvrir les charges d'intérêts, signal précurseur de risque de défaut sur la dette.

**Conditions obligatoires (required) :**
- Interest Coverage : en_dessous_norme

**Conditions renforçant la confiance (optional) :**
- Marge opérationnelle : en_dessous_norme (voir 02_rentabilite_patterns.md)

**Niveau de confiance :** élevé

**Diagnostic :**
Un résultat d'exploitation qui couvre difficilement les charges d'intérêts peut indiquer qu'une nouvelle baisse de la rentabilité opérationnelle compromettrait la capacité de l'entreprise à honorer ses engagements financiers. Ce signal est parmi les plus déterminants du risque de crédit et mérite une attention particulière.

**Hypothèses possibles :**
- dégradation récente de la rentabilité opérationnelle
- niveau d'endettement élevé au regard de la capacité bénéficiaire
- taux d'intérêt en hausse sur une dette à taux variable

**Actions d'investigation :**
- vérifier la structure des taux (fixe/variable) de la dette
- analyser l'évolution du ratio sur plusieurs exercices
- rapprocher du pattern RENT.002 (marge opérationnelle sous pression)

**Niveau de risque :** élevé

**Priorité :** élevée

**Références :** 03_solvabilite_patterns.md, 02_rentabilite_patterns.md

---

## SOLV.004 — Recours limité à l'endettement

**Catégorie :** solvabilité

**Objectif :** Identifier une structure financière très prudente, pouvant traduire soit une gestion conservatrice, soit une capacité d'endettement inexploitée.

**Conditions obligatoires (required) :**
- Debt Ratio : en_dessous_norme
- Equity Ratio : au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- aucune

**Niveau de confiance :** moyen

**Diagnostic :**
Un recours limité à l'endettement associé à une part élevée de capitaux propres dans le financement total est compatible avec une gestion financière prudente. Cette configuration peut aussi correspondre à une capacité d'endettement inexploitée pour financer la croissance ; les deux lectures ne sont pas mutuellement exclusives.

**Hypothèses possibles :**
- politique financière délibérément conservatrice
- capacité d'endettement disponible mais non mobilisée
- structure d'actionnariat privilégiant l'autofinancement

**Actions d'investigation :**
- évaluer la capacité d'endettement théorique au regard de la rentabilité
- vérifier l'existence de projets de croissance nécessitant un financement externe

**Niveau de risque :** faible

**Priorité :** surveillance

**Références :** 03_solvabilite_patterns.md

---

## SOLV.005 — Effet de ciseau entre endettement et capacité de remboursement

**Catégorie :** solvabilité

**Objectif :** Identifier la combinaison la plus critique en matière de solvabilité : un endettement élevé associé à une couverture des intérêts insuffisante.

**Conditions obligatoires (required) :**
- Debt-to-Equity : au_dessus_norme
- Interest Coverage : en_dessous_norme

**Conditions renforçant la confiance (optional) :**
- Marge nette : en_dessous_norme ou négatif

**Niveau de confiance :** élevé

**Diagnostic :**
La combinaison d'un endettement élevé et d'une couverture des intérêts insuffisante forme un effet de ciseau qui mérite une attention prioritaire : le poids de la dette dans la structure financière s'accompagne d'une capacité limitée à en assumer le coût. Ce constat ne préjuge pas d'un défaut mais concentre plusieurs facteurs de risque simultanément.

**Hypothèses possibles :**
- dégradation conjointe et récente de la rentabilité et du niveau d'endettement
- financement par la dette d'un projet dont les retours attendus ne se sont pas encore matérialisés
- choc externe affectant à la fois l'activité et le coût de la dette

**Actions d'investigation :**
- établir un plan de trésorerie prévisionnel intégrant le service de la dette
- vérifier l'existence de covenants bancaires et leur respect
- analyser les possibilités de restructuration ou de renégociation de la dette

**Niveau de risque :** élevé

**Priorité :** élevée

**Références :** 03_solvabilite_patterns.md

---

## SOLV.006 — Part des capitaux propres très réduite

**Catégorie :** solvabilité

**Objectif :** Signaler une dépendance forte au financement externe, au-delà du seul niveau d'endettement.

**Conditions obligatoires (required) :**
- Equity Ratio : en_dessous_norme

**Conditions renforçant la confiance (optional) :**
- Debt Ratio : zone_a_interroger_haut

**Niveau de confiance :** moyen

**Diagnostic :**
Une part des capitaux propres très réduite dans le financement total est compatible avec une dépendance forte de l'entreprise aux financements externes, la rendant potentiellement plus sensible aux conditions d'accès au crédit. Ce constat gagne à être mis en perspective avec l'historique de rentabilité, qui détermine la capacité de reconstitution des capitaux propres.

**Hypothèses possibles :**
- pertes cumulées ayant érodé les capitaux propres
- distribution de dividendes importante récente
- structure de financement récente encore peu capitalisée (jeune entreprise, LBO)

**Actions d'investigation :**
- analyser l'évolution des capitaux propres sur plusieurs exercices
- vérifier l'origine de la faiblesse des capitaux propres (pertes, distribution, structure)
- rapprocher du pattern RENT.006 (rentabilité négative) si pertinent

**Niveau de risque :** élevé

**Priorité :** à investiguer

**Références :** 03_solvabilite_patterns.md, 02_rentabilite_patterns.md

---

## SOLV.007 — Capacité de remboursement solide

**Catégorie :** solvabilité

**Objectif :** Confirmer une capacité de remboursement robuste, combinant couverture des intérêts élevée et endettement maîtrisé.

**Conditions obligatoires (required) :**
- Interest Coverage : au_dessus_norme
- Debt-to-Equity : dans_la_norme ou en_dessous_norme

**Conditions renforçant la confiance (optional) :**
- aucune

**Niveau de confiance :** élevé

**Diagnostic :**
L'entreprise génère un résultat d'exploitation qui semble largement suffisant pour couvrir ses charges financières, dans un contexte d'endettement maîtrisé. Sa capacité de remboursement apparaît robuste à la date d'analyse.

**Hypothèses possibles :**
- performance opérationnelle solide et récurrente
- politique financière prudente en matière d'endettement

**Actions d'investigation :**
- vérifier la stabilité de cette capacité sur plusieurs exercices

**Niveau de risque :** faible

**Priorité :** information

**Références :** 03_solvabilite_patterns.md
