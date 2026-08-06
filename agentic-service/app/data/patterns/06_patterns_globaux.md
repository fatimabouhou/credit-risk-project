# Base de connaissances — Patterns globaux (synthèse multi-dimensions)

> Ces patterns de second ordre ne portent pas directement sur des ratios bruts mais sur le résultat de l'évaluation des patterns des fichiers 01 à 05 (comptage par niveau de risque et par catégorie). Ils doivent être exécutés après les patterns de catégorie et croisés, en dernière étape du pipeline de détection.

---

## GLOB.001 — Profil financier globalement sain

**Catégorie :** croisé (synthèse)

**Objectif :** Confirmer l'absence de signal de risque significatif à l'issue de l'analyse des quatre dimensions (liquidité, rentabilité, solvabilité, activité).

**Conditions obligatoires (required) :**
- Aucun pattern de niveau de risque élevé déclenché, toutes catégories confondues
- Majorité des patterns déclenchés de niveau de risque faible

**Conditions renforçant la confiance (optional) :**
- Aucun pattern croisé de niveau de risque élevé déclenché

**Niveau de confiance :** élevé

**Diagnostic :**
L'ensemble des dimensions analysées (liquidité, rentabilité, solvabilité, activité) converge vers un profil financier globalement sain à la date d'analyse. Aucun signal de risque significatif ne ressort de l'analyse croisée des indicateurs disponibles.

**Hypothèses possibles :**
- performance financière équilibrée sur l'ensemble des dimensions

**Actions d'investigation :**
- confirmer la stabilité de ce profil sur les exercices précédents avant de conclure définitivement

**Niveau de risque :** faible

**Priorité :** information

**Références :** 01_liquidite_patterns.md, 02_rentabilite_patterns.md, 03_solvabilite_patterns.md, 04_activite_patterns.md

---

## GLOB.002 — Profil de vigilance

**Catégorie :** croisé (synthèse)

**Objectif :** Signaler une accumulation de signaux modérés répartis sur plusieurs dimensions, ne justifiant pas individuellement une alerte mais appelant un suivi renforcé une fois cumulés.

**Conditions obligatoires (required) :**
- Au moins deux patterns de niveau de risque modéré déclenchés dans des catégories différentes
- Aucun pattern de niveau de risque élevé déclenché

**Conditions renforçant la confiance (optional) :**
- Les patterns modérés concernent des dimensions distinctes (ex. liquidité et activité, plutôt que deux patterns liquidité redondants)

**Niveau de confiance :** moyen

**Diagnostic :**
Plusieurs signaux modérés ont été identifiés dans des dimensions distinctes de l'analyse financière. Pris isolément, ces signaux ne sont pas alarmants, mais leur accumulation justifie un suivi attentif de la situation.

**Hypothèses possibles :**
- fragilités ponctuelles et indépendantes sur plusieurs dimensions
- début d'une dégradation coordonnée nécessitant une surveillance rapprochée

**Actions d'investigation :**
- établir la liste détaillée des patterns modérés déclenchés et leurs catégories
- suivre l'évolution de ces indicateurs sur le prochain exercice

**Niveau de risque :** modéré

**Priorité :** surveillance

**Références :** 01_liquidite_patterns.md, 02_rentabilite_patterns.md, 03_solvabilite_patterns.md, 04_activite_patterns.md

---

## GLOB.003 — Profil à risque élevé

**Catégorie :** croisé (synthèse)

**Objectif :** Signaler une convergence de signaux de risque élevé sur plusieurs dimensions distinctes, situation la plus critique du référentiel de synthèse.

**Conditions obligatoires (required) :**
- Au moins deux patterns de niveau de risque élevé déclenchés dans des catégories différentes

**Conditions renforçant la confiance (optional) :**
- Le pattern CROSS.GLOB.001 (risque de continuité d'exploitation) est également déclenché

**Niveau de confiance :** élevé

**Diagnostic :**
Plusieurs signaux de risque élevé convergent sur des dimensions distinctes de l'analyse financière. Cette accumulation de signaux négatifs est compatible avec une fragilité financière significative, nécessitant une analyse approfondie et, le cas échéant, l'examen de mesures correctives.

**Hypothèses possibles :**
- dégradation financière généralisée touchant plusieurs dimensions simultanément
- crise conjoncturelle sévère affectant transversalement l'entreprise
- accumulation de facteurs de risque indépendants coïncidant sur le même exercice

**Actions d'investigation :**
- établir la liste exhaustive des patterns élevés déclenchés et leurs catégories
- prioriser l'analyse sur les dimensions les plus critiques (solvabilité et liquidité en priorité)
- solliciter un avis d'analyste senior avant toute décision de crédit

**Niveau de risque :** élevé

**Priorité :** élevée

**Références :** 01_liquidite_patterns.md, 02_rentabilite_patterns.md, 03_solvabilite_patterns.md, 04_activite_patterns.md, 05_patterns_croises.md

---

## GLOB.004 — Fragilité concentrée sur une seule dimension

**Catégorie :** croisé (synthèse)

**Objectif :** Distinguer un risque isolé, concentré sur une seule dimension, d'une fragilité généralisée, afin d'orienter l'analyste vers l'investigation ciblée plutôt qu'une revue exhaustive.

**Conditions obligatoires (required) :**
- Exactement un pattern de niveau de risque élevé déclenché
- Tous les autres patterns déclenchés sont de niveau faible ou information

**Conditions renforçant la confiance (optional) :**
- aucune

**Niveau de confiance :** moyen

**Diagnostic :**
Le risque identifié semble concentré sur une seule dimension de l'analyse financière, les autres composantes restant globalement satisfaisantes. Il est recommandé de creuser spécifiquement cette dimension plutôt que de conclure à une fragilité généralisée de l'entreprise.

**Hypothèses possibles :**
- difficulté ponctuelle et circonscrite à un poste ou un processus spécifique
- signal précurseur d'une dégradation plus large, pas encore visible sur les autres dimensions

**Actions d'investigation :**
- concentrer l'analyse sur la dimension concernée par le pattern de niveau élevé
- vérifier l'absence de lien indirect avec les autres dimensions (par exemple via le tableau de flux de trésorerie)

**Niveau de risque :** modéré

**Priorité :** à investiguer

**Références :** 01_liquidite_patterns.md, 02_rentabilite_patterns.md, 03_solvabilite_patterns.md, 04_activite_patterns.md

---

## GLOB.005 — Croissance de l'activité sous tension de ressources

**Catégorie :** croisé (synthèse)

**Objectif :** Identifier un profil de croissance consommatrice de ressources financières, fréquent en phase de développement mais nécessitant un pilotage rigoureux.

**Conditions obligatoires (required) :**
- Chiffre d'affaires : en_croissance
- Working Capital : négatif ou proche_de_zero

**Conditions renforçant la confiance (optional) :**
- Debt Ratio : dans_la_norme ou au_dessus_norme

**Niveau de confiance :** faible

**Diagnostic :**
Une croissance de l'activité qui s'accompagne d'une tension sur le fonds de roulement peut traduire un besoin de financement accru lié au développement. Ce profil est fréquent en phase de croissance mais nécessite un pilotage rigoureux du besoin en fonds de roulement pour limiter le risque de rupture de trésorerie. Ce pattern dépend d'une donnée de tendance (évolution du chiffre d'affaires) dont la disponibilité dans le pipeline de calcul doit être confirmée.

**Hypothèses possibles :**
- croissance organique consommatrice de fonds de roulement, maîtrisée par la direction
- croissance mal anticipée sur le plan financier, sans financement suffisant du besoin en fonds de roulement additionnel

**Actions d'investigation :**
- établir un plan de financement prévisionnel intégrant la trajectoire de croissance
- vérifier l'existence de lignes de financement dédiées à la croissance (factor, crédit de campagne)
- rapprocher du pattern ACT.007 (besoin en fonds de roulement élevé)

**Niveau de risque :** modéré

**Priorité :** à investiguer

**Références :** 01_liquidite_patterns.md, 03_solvabilite_patterns.md, 04_activite_patterns.md

---

## GLOB.006 — Profil atypique nécessitant une contextualisation sectorielle

**Catégorie :** croisé (synthèse)

**Objectif :** Éviter une lecture mécanique d'un fonds de roulement négatif lorsque les indicateurs de rentabilité et de trésorerie restent par ailleurs satisfaisants, configuration typique de certains modèles économiques.

**Conditions obligatoires (required) :**
- Working Capital : négatif
- Marge nette : dans_la_norme ou au_dessus_norme
- Cash Ratio : dans_la_norme ou au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- Secteur d'activité connu pour un fonds de roulement structurellement négatif (distribution, restauration, e-commerce, services à paiement anticipé)

**Niveau de confiance :** moyen

**Diagnostic :**
Certains indicateurs présentent des valeurs qui s'écartent des références générales — notamment un fonds de roulement négatif — alors même que la rentabilité et la trésorerie disponible paraissent satisfaisantes. Ce profil est caractéristique de certains modèles économiques où la référence générale ne s'applique pas directement. Une contextualisation sectorielle est nécessaire avant de conclure à un risque, ce pattern devant primer sur une lecture isolée de LIQ.004 ou LIQ.007 lorsque ses conditions sont réunies.

**Hypothèses possibles :**
- modèle économique à encaissement client avant paiement fournisseur, structurel au secteur
- gestion financière optimisée du cycle d'exploitation, sans risque de continuité associé

**Actions d'investigation :**
- confirmer le secteur d'activité et comparer aux standards sectoriels plutôt qu'aux références générales
- vérifier la récurrence de cette configuration sur plusieurs exercices, qui renforcerait son caractère structurel plutôt qu'accidentel

**Niveau de risque :** faible

**Priorité :** à investiguer

**Références :** 01_liquidite_patterns.md, 02_rentabilite_patterns.md
