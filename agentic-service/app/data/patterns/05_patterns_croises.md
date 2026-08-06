# Base de connaissances — Patterns croisés (multi-dimensions)

> Ces patterns combinent des indicateurs issus de plusieurs catégories. Ils ont généralement un pouvoir diagnostique supérieur aux patterns univariés, car la convergence de plusieurs signaux réduit (sans l'éliminer) le risque de fausse alerte. Chaque pattern reste toutefois une hypothèse de lecture, non une conclusion.

---

## CROSS.LIQ.001 — Liquidité disponible élevée et recouvrement dégradé

**Catégorie :** croisé (liquidité × activité)

**Objectif :** Identifier une situation où une trésorerie abondante coexiste avec un poste clients dégradé, combinaison qui interroge sur l'origine de la liquidité et la qualité des créances.

**Conditions obligatoires (required) :**
- Cash Ratio : zone_a_interroger_haut
- DSO : au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- Current Ratio : au_dessus_norme

**Niveau de confiance :** moyen

**Diagnostic :**
La coexistence d'une trésorerie importante et de délais de recouvrement très élevés est une combinaison qui mérite une analyse complémentaire : elle peut traduire des réalités très différentes selon l'origine de la liquidité disponible et la qualité effective des créances clients.

**Hypothèses possibles :**
- trésorerie issue d'une opération de financement récente, sans lien avec le poste clients
- créances clients anciennes mais jugées recouvrables, sans tension de trésorerie associée
- gestion différenciée entre une activité rentable en cash et une activité à crédit clients longs

**Actions d'investigation :**
- analyser l'origine de la trésorerie disponible (flux d'exploitation, de financement ou d'investissement)
- examiner la balance âgée des créances clients
- vérifier l'existence de provisions pour créances douteuses

**Niveau de risque :** modéré

**Priorité :** à investiguer

**Références :** 01_liquidite_patterns.md, 04_activite_patterns.md

---

## CROSS.RENT.001 — Rentabilité soutenue malgré une rotation des actifs faible

**Catégorie :** croisé (rentabilité × activité)

**Objectif :** Caractériser un modèle économique à forte marge compensant une rotation des actifs modeste.

**Conditions obligatoires (required) :**
- Asset Turnover : en_dessous_norme
- Marge opérationnelle : au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- Marge brute : au_dessus_norme

**Niveau de confiance :** moyen

**Diagnostic :**
La faible rotation des actifs semble compensée par une marge opérationnelle élevée, ce qui est compatible avec une stratégie privilégiant la marge plutôt que le volume d'activité. Ce constat n'est pas en soi un signal de risque.

**Hypothèses possibles :**
- positionnement stratégique haut de gamme ou de niche
- activité intensive en capital à cycle de rotation long
- effet temporaire d'investissements récents non encore pleinement productifs

**Actions d'investigation :**
- comparer le couple marge/rotation aux références du secteur
- vérifier la nature et l'ancienneté des actifs immobilisés

**Niveau de risque :** faible

**Priorité :** information

**Références :** 02_rentabilite_patterns.md, 04_activite_patterns.md

*(Doublon de RENT.008, conservé ici comme point d'entrée croisé pour un moteur de règles interrogeant d'abord la table des patterns croisés — voir note de redondance en fin de document.)*

---

## CROSS.SOLV.001 — Endettement élevé associé à une rentabilité insuffisante

**Catégorie :** croisé (solvabilité × rentabilité)

**Objectif :** Identifier une situation où le niveau d'endettement paraît difficilement soutenable au regard de la rentabilité générée.

**Conditions obligatoires (required) :**
- Debt-to-Equity : au_dessus_norme
- Marge nette : en_dessous_norme ou négatif

**Conditions renforçant la confiance (optional) :**
- Interest Coverage : en_dessous_norme

**Niveau de confiance :** élevé

**Diagnostic :**
Un endettement élevé associé à une rentabilité insuffisante pour en absorber le coût dans la durée est une combinaison qui accroît le risque de tension financière si la situation venait à se prolonger. Ce constat ne permet pas de conclure à un risque de défaut immédiat, mais justifie une vigilance renforcée.

**Hypothèses possibles :**
- phase d'investissement financée par dette dont les retours ne se sont pas encore matérialisés
- dégradation conjoncturelle récente de la rentabilité
- dégradation structurelle simultanée de la rentabilité et de la structure financière

**Actions d'investigation :**
- vérifier si la baisse de rentabilité est ponctuelle ou récurrente
- analyser le plan d'affaires et les perspectives de redressement de la rentabilité
- rapprocher des patterns SOLV.002, SOLV.005 et RENT.006

**Niveau de risque :** élevé

**Priorité :** élevée

**Références :** 03_solvabilite_patterns.md, 02_rentabilite_patterns.md

---

## CROSS.RENT.002 — Croissance du chiffre d'affaires avec dilution de la marge

**Catégorie :** croisé (activité × rentabilité)

**Objectif :** Identifier une croissance de l'activité qui ne se traduit pas par une amélioration, voire s'accompagne d'une dégradation, de la rentabilité opérationnelle.

**Conditions obligatoires (required) :**
- Chiffre d'affaires : en_croissance
- Marge opérationnelle : en_dessous_norme ou en_baisse

**Conditions renforçant la confiance (optional) :**
- Marge brute : stable ou en_baisse

**Niveau de confiance :** faible

**Diagnostic :**
Une progression du chiffre d'affaires non accompagnée d'une amélioration de la rentabilité opérationnelle peut traduire une dilution de la marge, dont l'origine reste à documenter. Ce pattern nécessite une donnée de tendance (évolution du chiffre d'affaires) en complément des ratios ponctuels habituels ; sa disponibilité doit être confirmée auprès du pipeline de calcul avant activation en production.

**Hypothèses possibles :**
- stratégie de conquête de parts de marché via des prix plus agressifs
- pression concurrentielle sur les prix de vente
- structure de coûts qui s'ajuste avec retard à la croissance de l'activité

**Actions d'investigation :**
- décomposer l'évolution de la marge par facteur (prix, volume, coûts)
- comparer le rythme de croissance du chiffre d'affaires et des charges d'exploitation
- vérifier si la dilution de marge est assumée dans le plan stratégique de l'entreprise

**Niveau de risque :** modéré

**Priorité :** à investiguer

**Références :** 02_rentabilite_patterns.md

---

## CROSS.LIQ.002 — Risque combiné de liquidité et d'endettement

**Catégorie :** croisé (liquidité × solvabilité)

**Objectif :** Identifier une double contrainte financière, à court terme (liquidité) et à moyen-long terme (endettement), réduisant fortement les marges de manœuvre.

**Conditions obligatoires (required) :**
- Current Ratio : en_dessous_norme
- Debt-to-Equity : au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- Interest Coverage : en_dessous_norme

**Niveau de confiance :** élevé

**Diagnostic :**
La fragilité de la liquidité à court terme combinée à un endettement élevé à moyen et long terme est une configuration qui réduit fortement les marges de manœuvre financières de l'entreprise, sur les deux horizons temporels simultanément.

**Hypothèses possibles :**
- dégradation financière généralisée touchant plusieurs horizons
- financement récent d'un investissement pesant temporairement sur la liquidité et l'endettement
- gestion de trésorerie tendue mais volontairement maintenue (financement par découvert)

**Actions d'investigation :**
- établir un plan de trésorerie prévisionnel à 12 mois intégrant le service de la dette
- vérifier l'existence de covenants bancaires liés à la liquidité ou à l'endettement
- prioriser une analyse de la soutenabilité de la dette à moyen terme

**Niveau de risque :** élevé

**Priorité :** élevée

**Références :** 01_liquidite_patterns.md, 03_solvabilite_patterns.md

---

## CROSS.RENT.003 — ROE élevé à mettre en perspective avec l'endettement

**Catégorie :** croisé (rentabilité × solvabilité)

**Objectif :** Nuancer la lecture d'un ROE élevé lorsqu'il coïncide avec un endettement supérieur aux références.

**Conditions obligatoires (required) :**
- ROE : au_dessus_norme
- Debt-to-Equity : au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- ROA : dans_la_norme (écarte une explication par la seule performance opérationnelle)

**Niveau de confiance :** moyen

**Diagnostic :**
Un ROE élevé coïncidant avec un endettement supérieur aux références suggère que la rentabilité des capitaux propres pourrait être en partie portée par l'effet de levier financier plutôt que par la seule performance opérationnelle. La lecture de cet indicateur gagne à être nuancée par le niveau de risque financier associé.

**Hypothèses possibles :**
- effet de levier financier assumé et maîtrisé par la direction
- base de capitaux propres réduite du fait de l'endettement
- performance opérationnelle réelle également en cause, à vérifier via le ROA

**Actions d'investigation :**
- décomposer le ROE selon une approche DuPont
- comparer le ROA et le ROE pour isoler la contribution du levier
- rapprocher des patterns RENT.003 et RENT.007

**Niveau de risque :** modéré

**Priorité :** à investiguer

**Références :** 02_rentabilite_patterns.md, 03_solvabilite_patterns.md

*(Recoupe largement RENT.003 ; conservé comme point d'entrée croisé — voir note de redondance en fin de document.)*

---

## CROSS.ACT.001 — Ralentissement des stocks et pression sur la marge brute

**Catégorie :** croisé (activité × rentabilité)

**Objectif :** Identifier un risque de dépréciation des stocks lorsqu'un ralentissement de leur rotation coïncide avec une marge brute dégradée.

**Conditions obligatoires (required) :**
- DIO : au_dessus_norme
- Marge brute : en_dessous_norme ou en_baisse

**Conditions renforçant la confiance (optional) :**
- aucune

**Niveau de confiance :** moyen

**Diagnostic :**
Le ralentissement de la rotation des stocks associé à une marge brute en retrait peut signaler un risque de dépréciation des stocks ou une difficulté à écouler la production aux conditions de prix habituelles. D'autres explications sectorielles restent possibles.

**Hypothèses possibles :**
- stocks difficilement écoulables nécessitant des baisses de prix ou des dépréciations
- ralentissement de la demande sur les produits concernés
- accumulation de stocks liée à une stratégie d'approvisionnement anticipée, sans lien avec la marge

**Actions d'investigation :**
- vérifier l'existence et le niveau des provisions pour dépréciation de stocks
- analyser la composition des stocks par ancienneté et par catégorie de produits
- comparer l'évolution de la marge brute et du DIO sur plusieurs exercices

**Niveau de risque :** modéré

**Priorité :** à investiguer

**Références :** 04_activite_patterns.md, 02_rentabilite_patterns.md

---

## CROSS.LIQ.003 — Tension de trésorerie associée au poste clients

**Catégorie :** croisé (liquidité × activité)

**Objectif :** Identifier une situation où le retard de recouvrement des créances clients semble peser directement sur le niveau de trésorerie disponible.

**Conditions obligatoires (required) :**
- DSO : au_dessus_norme
- Cash Ratio : zone_a_interroger_bas

**Conditions renforçant la confiance (optional) :**
- Working Capital : négatif ou proche_de_zero

**Niveau de confiance :** élevé

**Diagnostic :**
Le retard de recouvrement des créances clients associé à un niveau de trésorerie disponible très faible est compatible avec un lien direct entre les deux phénomènes. Une action ciblée sur le poste clients pourrait, sous cette hypothèse, avoir un effet relativement rapide sur la liquidité de l'entreprise ; ce lien de causalité reste néanmoins à confirmer.

**Hypothèses possibles :**
- dégradation du recouvrement expliquant directement la tension de trésorerie
- deux phénomènes concomitants mais d'origines distinctes (par exemple investissement récent et retard clients indépendant)
- gestion de trésorerie tendue par nature, indépendamment du poste clients

**Actions d'investigation :**
- établir un plan de trésorerie prévisionnel intégrant les encaissements attendus
- prioriser les actions de relance sur les créances les plus anciennes
- vérifier si d'autres facteurs (investissement, remboursement de dette) expliquent la tension de trésorerie

**Niveau de risque :** élevé

**Priorité :** élevée

**Références :** 01_liquidite_patterns.md, 04_activite_patterns.md

---

## CROSS.RENT.004 — Rentabilité affichée non reflétée dans la trésorerie disponible

**Catégorie :** croisé (rentabilité × liquidité)

**Objectif :** Identifier un écart entre la rentabilité comptable et la trésorerie effectivement disponible, invitant à examiner la conversion du résultat en cash.

**Conditions obligatoires (required) :**
- Marge nette : dans_la_norme ou au_dessus_norme
- Cash Ratio : en_dessous_norme ou zone_a_interroger_bas

**Conditions renforçant la confiance (optional) :**
- DSO ou DIO : au_dessus_norme

**Niveau de confiance :** moyen

**Diagnostic :**
Une rentabilité comptable satisfaisante qui ne se traduit pas par un niveau de trésorerie disponible équivalent peut provenir d'un besoin en fonds de roulement croissant, d'investissements significatifs, ou d'éléments non monétaires dans le résultat. L'écart entre résultat comptable et trésorerie mérite d'être documenté plutôt que présumé anormal.

**Hypothèses possibles :**
- besoin en fonds de roulement en augmentation (créances, stocks)
- programme d'investissement significatif sur la période
- éléments non monétaires dans le résultat (réévaluations, écritures de reprise)

**Actions d'investigation :**
- analyser le tableau de flux de trésorerie (exploitation, investissement, financement)
- rapprocher le résultat net de la variation de trésorerie
- croiser avec les patterns d'activité (DSO, DIO) pour évaluer l'impact du cycle d'exploitation

**Niveau de risque :** modéré

**Priorité :** à investiguer

**Références :** 02_rentabilite_patterns.md, 01_liquidite_patterns.md

---

## CROSS.SOLV.002 — Capacité financière disponible mais rentabilité modeste

**Catégorie :** croisé (solvabilité × rentabilité)

**Objectif :** Identifier une situation où une structure financière solide coexiste avec une rentabilité en retrait, pouvant indiquer une capacité d'investissement sous-exploitée.

**Conditions obligatoires (required) :**
- Interest Coverage : au_dessus_norme
- Debt Ratio : en_dessous_norme
- Marge nette : en_dessous_norme

**Conditions renforçant la confiance (optional) :**
- aucune

**Niveau de confiance :** faible

**Diagnostic :**
La combinaison d'une structure financière solide et d'une capacité de remboursement confortable avec une rentabilité modeste peut traduire une capacité d'investissement ou de levier sous-exploitée pour soutenir la croissance. Cette lecture reste une hypothèse parmi d'autres, la rentabilité modeste pouvant aussi refléter des difficultés opérationnelles indépendantes de la structure financière.

**Hypothèses possibles :**
- capacité de financement disponible mais non mobilisée par choix stratégique
- difficultés opérationnelles limitant la rentabilité indépendamment de la structure financière
- phase de transition entre deux modèles économiques

**Actions d'investigation :**
- analyser les causes de la rentabilité modeste indépendamment de la structure financière
- évaluer les opportunités d'investissement identifiées par la direction

**Niveau de risque :** faible

**Priorité :** surveillance

**Références :** 03_solvabilite_patterns.md, 02_rentabilite_patterns.md

*(Reformulation prudente de l'ancien PATTERN_CROSS_010, dont la conclusion — « capacité sous-exploitée » — était affirmée de façon trop catégorique ; le niveau de confiance a été abaissé en conséquence.)*

---

## CROSS.ACT.002 — Dépendance combinée au crédit fournisseur et au crédit bancaire

**Catégorie :** croisé (activité × solvabilité)

**Objectif :** Identifier une situation où l'entreprise mobilise simultanément un crédit fournisseur étendu et un endettement bancaire élevé pour financer son cycle d'exploitation — configuration classique de tension de financement du besoin en fonds de roulement.

**Conditions obligatoires (required) :**
- DPO : zone_a_interroger_haut
- Debt Ratio : au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- Working Capital : négatif ou proche_de_zero

**Niveau de confiance :** moyen

**Diagnostic :**
Le recours conjoint à un allongement du crédit fournisseur et à un endettement bancaire élevé peut indiquer que l'entreprise mobilise l'ensemble des leviers de financement disponibles pour couvrir son cycle d'exploitation. Cette configuration mérite une analyse de la soutenabilité de ces deux sources de financement, en particulier si l'une venait à se réduire (durcissement des conditions fournisseurs, refus de renouvellement de crédit).

**Hypothèses possibles :**
- financement structurel du besoin en fonds de roulement par l'ensemble des ressources court et moyen terme disponibles
- tension de trésorerie sous-jacente conduisant à mobiliser tous les leviers disponibles
- pratique sectorielle standard combinant délais fournisseurs longs et endettement modéré à élevé

**Actions d'investigation :**
- vérifier l'évolution du DPO et du Debt Ratio sur plusieurs exercices
- évaluer la marge de manœuvre residuelle en cas de durcissement des conditions fournisseurs
- rapprocher des patterns ACT.005 et SOLV.002

**Niveau de risque :** modéré

**Priorité :** à investiguer

**Références :** 04_activite_patterns.md, 03_solvabilite_patterns.md

---

## CROSS.GLOB.001 — Signaux convergents de risque de continuité d'exploitation

**Catégorie :** croisé (liquidité × rentabilité × solvabilité)

**Objectif :** Identifier la convergence des trois signaux considérés en analyse crédit comme les plus déterminants pour apprécier un risque de continuité d'exploitation : perte nette, fonds de roulement négatif et endettement élevé.

**Conditions obligatoires (required) :**
- Marge nette : négatif
- Working Capital : négatif
- Debt-to-Equity : au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- Interest Coverage : en_dessous_norme

**Niveau de confiance :** élevé

**Diagnostic :**
La convergence d'une perte nette, d'un fonds de roulement négatif et d'un endettement élevé constitue l'une des combinaisons les plus significatives en analyse crédit. Elle est compatible avec un risque de continuité d'exploitation qui doit être documenté sans délai ; elle ne constitue toutefois pas, à elle seule, une preuve de défaillance imminente, certaines entreprises redressant durablement une telle situation.

**Hypothèses possibles :**
- crise conjoncturelle sévère mais potentiellement réversible
- dégradation structurelle profonde du modèle économique
- restructuration ou plan de redressement déjà engagé mais non encore visible dans les résultats

**Actions d'investigation :**
- vérifier l'existence d'un plan de restructuration ou de redressement en cours
- analyser la trésorerie prévisionnelle à court terme et les échéances de dette
- évaluer le soutien potentiel des actionnaires ou des créanciers
- rapprocher des patterns LIQ.004, RENT.006 et SOLV.005

**Niveau de risque :** élevé

**Priorité :** élevée

**Références :** 01_liquidite_patterns.md, 02_rentabilite_patterns.md, 03_solvabilite_patterns.md
