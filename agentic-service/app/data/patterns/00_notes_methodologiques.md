# Note méthodologique — Refonte de la base de connaissances (v2)

Cette note documente les choix effectués lors de la refonte des 47 patterns d'origine vers la structure enrichie (identifiant, objectif, conditions required/optional, niveau de confiance, hypothèses multiples, actions d'investigation, références). Elle est destinée à l'équipe qui maintiendra la base, pas à l'agent de raisonnement lui-même.

## 1. Principes de reformulation appliqués systématiquement

- Tout diagnostic affirmant une causalité certaine ("traduit", "démontre que", "signifie que") a été reformulé au conditionnel ou avec des marqueurs d'hypothèse ("peut traduire", "est compatible avec", "mérite une analyse complémentaire").
- Chaque pattern propose désormais au minimum deux à quatre hypothèses explicatives distinctes, y compris pour les patterns à connotation positive (ex. LIQ.001), afin d'éviter que l'agent ne fige un diagnostic unique alors que plusieurs lectures restent possibles.
- Un niveau de confiance a été introduit indépendamment du niveau de risque : un pattern peut signaler un risque élevé avec une confiance seulement moyenne (ex. SOLV.002) si l'explication causale reste incertaine, ou à l'inverse un risque faible avec une confiance élevée (ex. LIQ.001) si le constat est peu ambigu.
- Les conditions ont été scindées entre `required` (strictement nécessaires au déclenchement) et `optional` (renforçant la confiance sans être bloquantes), ce qui permet à un moteur de règles de moduler le niveau de confiance affiché dynamiquement plutôt que de figer une confiance unique par pattern.

## 2. Patterns identifiés comme trop affirmatifs ou trop spéculatifs, et reformulés

| Pattern d'origine | Problème identifié | Traitement dans la v2 |
|---|---|---|
| PATTERN_CROSS_002 / PATTERN_CROSS_010 | Diagnostic concluant directement à une "stratégie" ou une "capacité sous-exploitée" sans réserve | Reformulé avec hypothèses concurrentes explicites (RENT.008, CROSS.RENT.001, CROSS.SOLV.002) et niveau de confiance abaissé à *faible* pour CROSS.SOLV.002 |
| PATTERN_CROSS_003 | Combinaison présentée comme un "risque de défaut" sans nuance | Reformulé en CROSS.SOLV.001, la formulation "accroît le risque de tension financière si la situation venait à se prolonger" remplace l'affirmation directe d'un risque de défaut |
| PATTERN_LIQ_007 | Fonds de roulement négatif qualifié de "déséquilibre" sans réserve suffisante | Reformulé en LIQ.007, avec renvoi systématique vers GLOB.006 pour éviter une lecture mécanique dans les secteurs à FR structurellement négatif |
| PATTERN_ACT_005 | Diagnostic hésitant déjà entre deux lectures mais sans structure d'hypothèses formalisée | Reformulé en ACT.005, niveau de confiance abaissé à *faible* car les deux hypothèses (négociation favorable / tension de trésorerie) sont d'égale plausibilité sans donnée complémentaire |

## 3. Redondances identifiées

Certains patterns univariés et croisés couvrent en partie le même signal. Ils n'ont pas été supprimés — un moteur de règles peut avoir intérêt à interroger indifféremment la table croisée ou la table de catégorie — mais la redondance est explicitement documentée dans le corps de chaque pattern concerné :

- **RENT.008 / CROSS.RENT.001** (rotation des actifs faible + marge opérationnelle élevée) : contenu identique, dupliqué pour permettre l'accès depuis les deux tables. Recommandation : à terme, ne conserver qu'une version et faire pointer l'autre identifiant vers elle par un simple alias, plutôt que dupliquer le texte.
- **RENT.003 / CROSS.RENT.003** (ROE élevé porté par le levier financier) : même logique de duplication assumée. Même recommandation d'alias à terme.
- **LIQ.003 / LIQ.004** : ne sont pas redondants au sens strict mais forment un couple gradué (tension → critique) sur les mêmes ratios. Conservés séparément car ils déclenchent des priorités différentes, mais leur proximité est signalée dans LIQ.003 pour orienter l'agent vers une escalade si les seuils se dégradent.
- **LIQ.004 / LIQ.007 / GLOB.006** : trois patterns différents peuvent se déclencher simultanément sur un même fonds de roulement négatif. GLOB.006 est explicitement positionné comme devant primer sur une lecture purement négative lorsque ses conditions (rentabilité et trésorerie satisfaisantes) sont réunies, afin d'éviter une contradiction dans le diagnostic final présenté à l'utilisateur.

## 4. Croisements classiques manquants, ajoutés dans la v2

L'analyse de la base d'origine a fait apparaître une couverture inégale des quatre croisements possibles entre catégories. Les ajouts suivants comblent les combinaisons absentes, en s'appuyant exclusivement sur des ratios déjà calculés par le système (aucun nouveau ratio introduit) :

- **CROSS.ACT.002** (activité × solvabilité) : dépendance combinée au crédit fournisseur (DPO élevé) et au crédit bancaire (Debt Ratio élevé). Ce croisement était absent alors qu'il constitue un signal classique de tension de financement du besoin en fonds de roulement en analyse crédit.
- **CROSS.GLOB.001** (liquidité × rentabilité × solvabilité) : convergence perte nette / fonds de roulement négatif / endettement élevé, correspondant au faisceau d'indices classiquement recherché pour documenter un risque de continuité d'exploitation. Ce pattern à trois dimensions n'existait pas dans la version d'origine, qui ne proposait que des croisements à deux dimensions.
- **CROSS.LIQ.003** existait déjà (ex-PATTERN_CROSS_008) mais a été renforcé avec une condition optionnelle sur le fonds de roulement pour améliorer la robustesse du diagnostic.

## 5. Patterns dépendant de données de tendance — à confirmer avant mise en production

Deux patterns reposent sur une donnée de tendance (évolution du chiffre d'affaires dans le temps) plutôt que sur un ratio ponctuel :

- **CROSS.RENT.002** (croissance du CA + dilution de marge)
- **GLOB.005** (croissance du CA + tension de fonds de roulement)

Conformément à la consigne de ne jamais construire un pattern sur un indicateur non calculé par le système, ces deux patterns ont été conservés avec un **niveau de confiance abaissé à *faible*** et une mention explicite dans leur objectif/diagnostic indiquant que la disponibilité de la donnée "évolution du chiffre d'affaires" doit être confirmée dans le pipeline de calcul avant activation. Si cette donnée n'est pas disponible, ces deux patterns doivent être désactivés plutôt qu'adaptés à un proxy imparfait.

## 6. Ce qui n'a volontairement pas été ajouté

Plusieurs croisements classiques en analyse financière (ex. Altman Z-Score, ratio de couverture du service de la dette (DSCR), flux de trésorerie disponible / dette nette) n'ont pas été intégrés, car ils reposent sur des ratios non mentionnés comme calculés par le système actuel. Conformément à la consigne, aucun pattern n'a été construit sur ces indicateurs. S'ils devenaient disponibles, ils constitueraient des candidats naturels pour une v3 de la base.

## 7. Récapitulatif quantitatif

| Fichier | Patterns v1 | Patterns v2 | Évolution |
|---|---|---|---|
| 01_liquidite_patterns.md | 8 | 8 | reformulation uniquement |
| 02_rentabilite_patterns.md | 8 | 8 | reformulation uniquement |
| 03_solvabilite_patterns.md | 7 | 7 | reformulation uniquement |
| 04_activite_patterns.md | 8 | 8 | reformulation uniquement |
| 05_patterns_croises.md | 10 | 12 | +2 (CROSS.ACT.002, CROSS.GLOB.001) |
| 06_patterns_globaux.md | 6 | 6 | reformulation uniquement |
| **Total** | **47** | **49** | **+2** |
