# Base de connaissances — Patterns de liquidité

> Ratios mobilisés dans ce fichier : Current Ratio, Quick Ratio, Cash Ratio, Working Capital.
> Tous les diagnostics sont formulés au conditionnel et n'engagent qu'une lecture probable des indicateurs ; ils doivent être confirmés par l'analyste.

---

## LIQ.001 — Liquidité confortable

**Catégorie :** liquidité

**Objectif :** Identifier une situation de liquidité générale satisfaisante, où l'entreprise dispose *a priori* de ressources suffisantes pour couvrir ses engagements à court terme.

**Conditions obligatoires (required) :**
- Current Ratio : dans_la_norme
- Working Capital : positif

**Conditions renforçant la confiance (optional) :**
- Quick Ratio : dans_la_norme ou au_dessus_norme

**Niveau de confiance :** élevé

**Diagnostic :**
La combinaison d'un ratio de liquidité générale dans les références et d'un fonds de roulement positif est compatible avec une capacité satisfaisante à couvrir les engagements à court terme. Ce constat reste toutefois statique et ne présume pas de l'évolution future de la liquidité.

**Hypothèses possibles :**
- gestion équilibrée du cycle d'exploitation
- politique prudente de constitution de réserves de trésorerie
- structure d'actifs circulants conforme aux standards du secteur

**Actions d'investigation :**
- confirmer la tendance sur les 2-3 derniers exercices
- comparer aux moyennes sectorielles plutôt qu'à une norme générique
- vérifier l'absence de saisonnalité forte qui fausserait la lecture à date

**Niveau de risque :** faible

**Priorité :** information

**Références :** 01_liquidite_patterns.md

---

## LIQ.002 — Excès de liquidité apparent

**Catégorie :** liquidité

**Objectif :** Repérer un niveau de trésorerie disponible sensiblement supérieur aux références, pouvant traduire une allocation sous-optimale des ressources.

**Conditions obligatoires (required) :**
- Cash Ratio : zone_a_interroger_haut

**Conditions renforçant la confiance (optional) :**
- Current Ratio : au_dessus_norme

**Niveau de confiance :** moyen

**Diagnostic :**
Un niveau de trésorerie disponible nettement supérieur aux références est susceptible d'indiquer une accumulation de liquidités non réinvesties. Cette lecture reste une hypothèse parmi d'autres : elle peut tout aussi bien correspondre à une opération ponctuelle (levée de fonds, cession d'actif) récemment intervenue.

**Hypothèses possibles :**
- sous-utilisation temporaire des ressources financières
- constitution volontaire d'un matelas de sécurité avant une échéance connue
- produit exceptionnel récent (cession, levée de fonds, subvention)
- politique de distribution de dividendes différée

**Actions d'investigation :**
- examiner le tableau de flux de trésorerie pour identifier l'origine de l'excédent
- vérifier l'existence d'un projet d'investissement ou d'acquisition en cours
- comparer avec le niveau de trésorerie des exercices précédents

**Niveau de risque :** faible

**Priorité :** surveillance

**Références :** 01_liquidite_patterns.md

---

## LIQ.003 — Tension de liquidité générale

**Catégorie :** liquidité

**Objectif :** Détecter un premier niveau de dégradation de la liquidité générale, avant que la situation ne devienne critique.

**Conditions obligatoires (required) :**
- Current Ratio : en_dessous_norme

**Conditions renforçant la confiance (optional) :**
- Working Capital : positif ou proche_de_zero

**Niveau de confiance :** moyen

**Diagnostic :**
Un ratio de liquidité générale inférieur aux références peut traduire une marge de manœuvre réduite pour honorer les engagements à court terme. Ce pattern constitue un signal d'alerte précoce ; il ne permet pas à lui seul de conclure à un risque de défaillance.

**Hypothèses possibles :**
- financement du cycle d'exploitation davantage assuré par le passif court terme
- décalage temporaire entre encaissements et décaissements
- phase de croissance consommatrice de fonds de roulement
- point bas conjoncturel dans un cycle d'activité saisonnier

**Actions d'investigation :**
- analyser la composition des actifs et passifs circulants
- vérifier l'évolution du ratio sur plusieurs trimestres
- rapprocher du pattern LIQ.007 (fonds de roulement négatif structurel) pour distinguer un phénomène ponctuel d'une tendance de fond

**Niveau de risque :** modéré

**Priorité :** surveillance

**Références :** 01_liquidite_patterns.md

---

## LIQ.004 — Liquidité critique

**Catégorie :** liquidité

**Objectif :** Identifier une convergence de signaux de liquidité dégradée justifiant une escalade vers une analyse approfondie.

**Conditions obligatoires (required) :**
- Current Ratio : en_dessous_norme
- Quick Ratio : en_dessous_norme
- Working Capital : négatif

**Conditions renforçant la confiance (optional) :**
- Cash Ratio : en_dessous_norme

**Niveau de confiance :** élevé

**Diagnostic :**
La convergence d'un fonds de roulement négatif et de ratios de liquidité générale et immédiate tous deux inférieurs aux références est compatible avec une tension significative sur la capacité de l'entreprise à honorer ses engagements à court terme. Ce constat justifie une analyse complémentaire avant toute conclusion sur le risque de défaut, certains modèles économiques fonctionnant durablement avec un fonds de roulement négatif (cf. LIQ.007 et GLOB.006).

**Hypothèses possibles :**
- dégradation réelle de la solvabilité à court terme
- modèle économique à cycle de encaissement rapide (grande distribution, restauration)
- restructuration récente du passif circulant
- soutien financier externe non reflété dans les ratios (ligne de crédit non tirée)

**Actions d'investigation :**
- vérifier l'existence de lignes de financement court terme non utilisées
- analyser le secteur d'activité pour évaluer si un fonds de roulement négatif y est structurel
- examiner l'échéancier des dettes à court terme
- comparer avec les exercices antérieurs pour distinguer un choc ponctuel d'une tendance

**Niveau de risque :** élevé

**Priorité :** élevée

**Références :** 01_liquidite_patterns.md

---

## LIQ.005 — Dépendance de la liquidité à l'écoulement des stocks

**Catégorie :** liquidité

**Objectif :** Détecter un écart significatif entre liquidité générale et liquidité immédiate, révélateur du poids des stocks dans la couverture du passif court terme.

**Conditions obligatoires (required) :**
- Current Ratio : dans_la_norme ou au_dessus_norme
- Quick Ratio : en_dessous_norme

**Conditions renforçant la confiance (optional) :**
- DIO : au_dessus_norme (voir 04_activite_patterns.md)

**Niveau de confiance :** moyen

**Diagnostic :**
L'écart entre le ratio de liquidité générale et le ratio de liquidité immédiate est susceptible d'indiquer que la capacité de l'entreprise à couvrir ses dettes à court terme repose en partie sur l'écoulement des stocks. Ce constat mérite d'être relativisé selon la nature de l'activité : il est attendu et peu préoccupant dans certains secteurs (distribution, industrie à stocks longs).

**Hypothèses possibles :**
- modèle économique intrinsèquement intensif en stocks (distribution, industrie)
- accumulation de stocks difficilement écoulables
- stratégie délibérée de constitution de stocks (anticipation de hausse de coûts, sécurisation d'approvisionnement)

**Actions d'investigation :**
- croiser avec le pattern ACT.003 (rotation des stocks lente)
- analyser la composition des stocks (matières premières, en-cours, produits finis)
- comparer le poids des stocks aux standards du secteur

**Niveau de risque :** modéré

**Priorité :** surveillance

**Références :** 01_liquidite_patterns.md, 04_activite_patterns.md

---

## LIQ.006 — Trésorerie immédiatement disponible très faible

**Catégorie :** liquidité

**Objectif :** Repérer un niveau de trésorerie immédiate très bas, indépendamment du niveau des autres ratios de liquidité.

**Conditions obligatoires (required) :**
- Cash Ratio : zone_a_interroger_bas

**Conditions renforçant la confiance (optional) :**
- Current Ratio : dans_la_norme ou en_dessous_norme

**Niveau de confiance :** moyen

**Diagnostic :**
Un niveau de trésorerie immédiatement disponible très faible peut réduire la marge de manœuvre de l'entreprise face à un imprévu ou un décalage de règlement, même lorsque les autres ratios de liquidité restent acceptables. Ce signal seul ne permet pas de conclure à une difficulté de paiement, la trésorerie pouvant être gérée de façon dynamique (mobilisation de créances, lignes de crédit court terme).

**Hypothèses possibles :**
- gestion de trésorerie « zéro cash » avec recours actif à des lignes de crédit
- règlement récent d'une échéance importante (dette, investissement, dividende)
- dépendance à un encaissement client attendu à court terme

**Actions d'investigation :**
- vérifier l'existence et le niveau d'utilisation de lignes de crédit court terme
- examiner le calendrier des encaissements et décaissements à venir
- analyser l'historique du Cash Ratio sur plusieurs clôtures

**Niveau de risque :** modéré

**Priorité :** à investiguer

**Références :** 01_liquidite_patterns.md

---

## LIQ.007 — Fonds de roulement négatif persistant

**Catégorie :** liquidité

**Objectif :** Distinguer un fonds de roulement négatif ponctuel d'une configuration structurelle, en croisant avec le niveau du ratio de liquidité générale.

**Conditions obligatoires (required) :**
- Working Capital : négatif
- Current Ratio : en_dessous_norme

**Conditions renforçant la confiance (optional) :**
- Constat observé sur plusieurs exercices consécutifs

**Niveau de confiance :** moyen

**Diagnostic :**
Un fonds de roulement négatif associé à un ratio de liquidité générale inférieur aux références est compatible avec une couverture insuffisante des passifs à court terme par les actifs circulants. Cette configuration peut néanmoins être normale dans certains modèles économiques à cycle d'encaissement rapide ; sa portée doit être appréciée au regard du secteur d'activité et de son caractère récurrent ou ponctuel.

**Hypothèses possibles :**
- déséquilibre financier structurel
- modèle économique à rotation rapide (paiement clients avant paiement fournisseurs)
- financement du besoin en fonds de roulement par de la dette court terme volontairement mobilisée

**Actions d'investigation :**
- vérifier la récurrence du phénomène sur plusieurs exercices
- comparer avec les standards du secteur d'activité
- rapprocher du pattern GLOB.006 (profil atypique nécessitant une contextualisation sectorielle)

**Niveau de risque :** élevé

**Priorité :** à investiguer

**Références :** 01_liquidite_patterns.md, 06_patterns_globaux.md

---

## LIQ.008 — Fonds de roulement à l'équilibre

**Catégorie :** liquidité

**Objectif :** Signaler une marge de sécurité réduite sur le fonds de roulement, même lorsque les ratios de liquidité restent dans les normes.

**Conditions obligatoires (required) :**
- Current Ratio : dans_la_norme
- Working Capital : proche_de_zero

**Conditions renforçant la confiance (optional) :**
- aucune

**Niveau de confiance :** faible

**Diagnostic :**
Le fonds de roulement proche de l'équilibre laisse un coussin de sécurité limité, bien que les ratios de liquidité restent dans les normes attendues à la date d'analyse. Ce constat n'indique pas de difficulté immédiate mais appelle un suivi régulier, la marge de manœuvre pouvant se réduire rapidement en cas de choc sur le cycle d'exploitation.

**Hypothèses possibles :**
- gestion fine et volontaire du fonds de roulement
- stade de transition entre deux configurations financières
- absence de réserve de précaution constituée

**Actions d'investigation :**
- suivre l'évolution du fonds de roulement sur les prochains exercices
- identifier les postes (stocks, créances, dettes fournisseurs) les plus sensibles à une variation

**Niveau de risque :** faible

**Priorité :** surveillance

**Références :** 01_liquidite_patterns.md
