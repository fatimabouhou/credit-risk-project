# Base de connaissances — Patterns d'activité (rotation)

> Ratios mobilisés dans ce fichier : DSO, DIO, DPO, Asset Turnover.

---

## ACT.001 — Difficulté de recouvrement des créances

**Catégorie :** activité

**Objectif :** Identifier un allongement du délai de recouvrement des créances clients, susceptible de peser sur le besoin en fonds de roulement.

**Conditions obligatoires (required) :**
- DSO : au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- Cash Ratio : en_dessous_norme (voir 01_liquidite_patterns.md)

**Niveau de confiance :** moyen

**Diagnostic :**
Un délai moyen de recouvrement des créances supérieur aux références peut accroître les besoins en fonds de roulement et exercer une pression sur la trésorerie. Ce constat mérite d'être documenté avant toute conclusion, plusieurs facteurs pouvant l'expliquer.

**Hypothèses possibles :**
- délais de paiement contractuels longs, propres au secteur ou à la clientèle
- dégradation de la qualité du poste clients (retards, impayés)
- concentration du portefeuille clients sur quelques comptes à fort pouvoir de négociation
- politique commerciale volontaire d'allongement des délais pour fidéliser la clientèle

**Actions d'investigation :**
- analyser l'ancienneté des créances (balance âgée)
- identifier les principaux clients et leur poids relatif
- comparer avec les délais de paiement contractuels
- comparer avec N-1 pour évaluer une éventuelle tendance

**Niveau de risque :** élevé

**Priorité :** élevée

**Références :** 04_activite_patterns.md

---

## ACT.002 — Cycle d'exploitation maîtrisé

**Catégorie :** activité

**Objectif :** Confirmer une cohérence d'ensemble entre les délais de recouvrement, de rotation des stocks et de paiement fournisseurs.

**Conditions obligatoires (required) :**
- DSO : dans_la_norme
- DIO : dans_la_norme

**Conditions renforçant la confiance (optional) :**
- DPO : dans_la_norme

**Niveau de confiance :** élevé

**Diagnostic :**
Les délais de recouvrement, de rotation des stocks et de paiement fournisseurs sont cohérents avec les références habituelles. Le cycle d'exploitation ne présente pas de déséquilibre notable à la date d'analyse.

**Hypothèses possibles :**
- gestion opérationnelle maîtrisée du cycle d'exploitation

**Actions d'investigation :**
- vérifier la stabilité de ces délais sur plusieurs exercices

**Niveau de risque :** faible

**Priorité :** information

**Références :** 04_activite_patterns.md

---

## ACT.003 — Rotation des stocks ralentie

**Catégorie :** activité

**Objectif :** Identifier un ralentissement de l'écoulement des stocks, susceptible d'immobiliser des ressources financières.

**Conditions obligatoires (required) :**
- DIO : au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- Marge brute : en_dessous_norme ou en_baisse

**Niveau de confiance :** moyen

**Diagnostic :**
Des stocks qui s'écoulent plus lentement que la référence attendue peuvent immobiliser des ressources financières et accroître le risque de dépréciation. Ce constat gagne à être resitué dans le contexte du secteur, certaines activités impliquant des cycles de stockage naturellement longs.

**Hypothèses possibles :**
- ralentissement de la demande sur les produits concernés
- constitution volontaire de stocks de sécurité ou anticipation d'une hausse de prix
- allongement structurel des délais de production ou d'approvisionnement

**Actions d'investigation :**
- analyser la composition des stocks par nature et par ancienneté
- vérifier l'existence de provisions pour dépréciation de stocks
- comparer avec les standards du secteur d'activité

**Niveau de risque :** modéré

**Priorité :** surveillance

**Références :** 04_activite_patterns.md

---

## ACT.004 — Rotation des actifs faible

**Catégorie :** activité

**Objectif :** Identifier un chiffre d'affaires faible au regard de la taille du bilan, pouvant traduire une sous-utilisation des actifs ou un modèle intensif en capital.

**Conditions obligatoires (required) :**
- Asset Turnover : en_dessous_norme

**Conditions renforçant la confiance (optional) :**
- Marge opérationnelle : au_dessus_norme (voir RENT.008)

**Niveau de confiance :** moyen

**Diagnostic :**
Un chiffre d'affaires relativement faible au regard de la taille du bilan peut indiquer une sous-utilisation des actifs ou correspondre à un modèle économique intensif en capital. La distinction entre ces deux lectures nécessite une analyse complémentaire de la rentabilité et du secteur d'activité.

**Hypothèses possibles :**
- modèle économique intensif en capital (industrie lourde, immobilier, infrastructures)
- sous-utilisation ou obsolescence d'une partie des actifs
- investissements récents pas encore pleinement productifs

**Actions d'investigation :**
- comparer le taux de rotation des actifs aux standards du secteur
- vérifier l'ancienneté et le taux d'utilisation des actifs immobilisés
- rapprocher du pattern RENT.008 pour évaluer si la marge compense la rotation faible

**Niveau de risque :** modéré

**Priorité :** surveillance

**Références :** 04_activite_patterns.md, 02_rentabilite_patterns.md

---

## ACT.005 — Délai de paiement fournisseurs élevé

**Catégorie :** activité

**Objectif :** Identifier un allongement du délai de paiement fournisseurs, dont l'origine peut être une politique de négociation ou une tension de trésorerie.

**Conditions obligatoires (required) :**
- DPO : zone_a_interroger_haut

**Conditions renforçant la confiance (optional) :**
- Cash Ratio : en_dessous_norme (voir 01_liquidite_patterns.md)

**Niveau de confiance :** faible

**Diagnostic :**
Un délai de règlement des fournisseurs particulièrement élevé peut résulter d'une politique de négociation favorable à l'entreprise, mais peut également signaler des tensions de trésorerie conduisant à différer les paiements. Ces deux hypothèses ne peuvent être départagées sans analyse complémentaire.

**Hypothèses possibles :**
- pouvoir de négociation élevé vis-à-vis des fournisseurs
- tension de trésorerie conduisant à différer les règlements
- pratique sectorielle standard sur des délais longs

**Actions d'investigation :**
- comparer le DPO aux délais contractuels habituels du secteur
- vérifier l'existence de retards de paiement ou de relances fournisseurs
- croiser avec les indicateurs de liquidité (Cash Ratio, Current Ratio)

**Niveau de risque :** modéré

**Priorité :** à investiguer

**Références :** 04_activite_patterns.md, 01_liquidite_patterns.md

---

## ACT.006 — Cycle de conversion de trésorerie favorable

**Catégorie :** activité

**Objectif :** Identifier une combinaison de délais favorable au besoin en fonds de roulement (recouvrement et stocks rapides, délai fournisseurs confortable).

**Conditions obligatoires (required) :**
- DSO : dans_la_norme ou en_dessous_norme
- DIO : dans_la_norme ou en_dessous_norme

**Conditions renforçant la confiance (optional) :**
- DPO : dans_la_norme ou au_dessus_norme

**Niveau de confiance :** moyen

**Diagnostic :**
Le recouvrement rapide des créances et l'écoulement rapide des stocks, combinés à des délais fournisseurs confortables, sont compatibles avec un cycle de conversion de trésorerie favorable, limitant le besoin en fonds de roulement. Cette configuration constitue *a priori* un atout pour la gestion de trésorerie.

**Hypothèses possibles :**
- gestion opérationnelle efficace du cycle d'exploitation
- rapport de force commercial favorable vis-à-vis de clients et fournisseurs
- modèle économique structurellement favorable (paiement comptant clients)

**Actions d'investigation :**
- vérifier la pérennité de cette configuration sur plusieurs exercices

**Niveau de risque :** faible

**Priorité :** information

**Références :** 04_activite_patterns.md

---

## ACT.007 — Besoin en fonds de roulement élevé lié au cycle d'exploitation

**Catégorie :** activité

**Objectif :** Identifier une accumulation de délais défavorables (recouvrement et stocks) génératrice d'un besoin en fonds de roulement important.

**Conditions obligatoires (required) :**
- DSO : au_dessus_norme
- DIO : au_dessus_norme

**Conditions renforçant la confiance (optional) :**
- Working Capital : négatif ou proche_de_zero (voir 01_liquidite_patterns.md)

**Niveau de confiance :** moyen

**Diagnostic :**
Des délais de recouvrement et de rotation des stocks tous deux supérieurs aux références sont compatibles avec un besoin en fonds de roulement élevé, susceptible d'accroître la dépendance de l'entreprise au financement externe du cycle d'exploitation.

**Hypothèses possibles :**
- cumul de délais de paiement clients longs et de stocks importants, propres au secteur
- dégradation conjointe de la gestion du poste clients et des stocks
- phase de croissance nécessitant un financement accru du cycle d'exploitation

**Actions d'investigation :**
- calculer le besoin en fonds de roulement en nombre de jours de chiffre d'affaires
- identifier le mode de financement de ce besoin (dette court terme, capitaux propres)
- rapprocher des patterns ACT.001 et ACT.003

**Niveau de risque :** élevé

**Priorité :** élevée

**Références :** 04_activite_patterns.md, 01_liquidite_patterns.md

---

## ACT.008 — Rotation des stocks très rapide

**Catégorie :** activité

**Objectif :** Identifier une rotation des stocks anormalement rapide, pouvant traduire une gestion tendue avec un risque de rupture.

**Conditions obligatoires (required) :**
- DIO : zone_a_interroger_bas

**Conditions renforçant la confiance (optional) :**
- Marge brute : au_dessus_norme

**Niveau de confiance :** faible

**Diagnostic :**
Une rotation des stocks particulièrement rapide peut refléter une gestion efficace de la chaîne d'approvisionnement, mais également un niveau de stocks tendu exposant à un risque de rupture en cas de demande imprévue.

**Hypothèses possibles :**
- gestion en flux tendu (juste-à-temps) maîtrisée
- niveaux de stocks insuffisants exposant à un risque de rupture
- activité de service ou de négoce à faible intensité de stocks

**Actions d'investigation :**
- vérifier l'existence d'incidents de rupture de stock récents
- analyser la nature de l'activité (industrielle, négoce, service)

**Niveau de risque :** faible

**Priorité :** surveillance

**Références :** 04_activite_patterns.md
