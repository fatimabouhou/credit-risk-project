# Rapport d'analyse de sécurité statique (SAST)

**Date** : 23 août 2026
**Périmètre** : les 4 services Python, le frontend, l'infrastructure Docker et l'historique Git
**Nature** : analyse statique du code au repos, sans exploitation

## Outils utilisés

| Outil | Cible | Résultat |
|---|---|---|
| Bandit 1.9.4 | 5 750 lignes Python | 3 alertes (0 haute) |
| Recherche de motifs de secrets | 24 commits, historique complet | 0 secret |
| pip-audit | Dépendances Python déclarées | 2 CVE |
| npm audit | Dépendances frontend | 0 vulnérabilité |
| Revue manuelle | Routes, templates, conteneurs | 5 constats |

---

## Synthèse

| Sévérité | Nombre | Titres |
|---|---|---|
| **Haute** | 1 | Traversée de chemin sur `POST /analyze/{client_id}` |
| **Moyenne** | 4 | Absence d'authentification · mongo-express sans auth · bases exposées sur l'hôte · dépendances vulnérables |
| **Basse** | 4 | Conteneurs en root · mot de passe de repli en dur · modèle HF non épinglé · `node_modules` versionné |
| **Faux positifs** | 2 | Injections SQL signalées par Bandit (B608) |

**Points solides constatés** : aucun secret dans l'historique Git, `.gitignore` correct, échappement Jinja2 actif, CORS restreint, uploads validés (type, extension, taille), aucune vulnérabilité npm.

---

## 🔴 HAUTE — Traversée de chemin sur `POST /analyze/{client_id}`

**Fichier** : `document-service/app/main.py:162-176`

L'identifiant client est concaténé dans un chemin de système de fichiers sans aucune validation :

```python
BASE_DIR = os.path.dirname(CURRENT_DIR)
folder_path = os.path.join(BASE_DIR, "simulators", client_id)   # client_id non validé
...
audit_result = processor.process_client_folder(root_folder=folder_path, save_to_db=True)
```

Un identifiant contenant `../` fait sortir le chemin du dossier prévu. Le service lit alors les PDF du répertoire atteint, les extrait, et enregistre leur contenu en base — soit une **lecture de fichiers arbitraires** limitée aux PDF.

**Ce qui rend ce point notable** : la protection existe déjà dans le code.

```python
# document-service/app/services/upload_service.py:48
def validate_client_id(client_id: str) -> None:
    """Anti path-traversal : `client_id` finit dans un os.path.join non sanitisé
    en aval (voir main.py, POST /analyze/{client_id}) ..."""
```

La docstring **désigne nommément la route `/analyze`** comme la zone à risque, mais l'appel n'a été posé que sur `/upload` (`main.py:133`). La fonction protège la route qui n'en avait pas le plus besoin.

**Routes concernées**

| Route | Validation | Chemin construit | Risque |
|---|---|---|---|
| `POST /upload/{client_id}` | ✅ ligne 133 | oui | couvert |
| `POST /analyze/{client_id}` | ❌ | **oui** | **traversée** |
| `GET /client/{client_id}` | ❌ | non (requête MongoDB) | faible |

**Correction** — appeler la validation existante en tête des deux routes :

```python
@app.post("/analyze/{client_id}")
def analyze_client_folder(client_id: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    validate_client_id(client_id)
    ...

@app.get("/client/{client_id}")
def get_client_audit(client_id: str) -> Dict[str, Any]:
    validate_client_id(client_id)
    ...
```

En défense en profondeur, vérifier après résolution que le chemin reste sous la racine :

```python
racine = os.path.realpath(os.path.join(BASE_DIR, "simulators"))
folder_path = os.path.realpath(os.path.join(racine, client_id))
if os.path.commonpath([racine, folder_path]) != racine:
    raise HTTPException(status_code=400, detail="Identifiant client invalide.")
```

---

## 🟠 MOYENNE

### M1 — Aucune authentification sur les quatre API

Aucun service n'implémente d'authentification. Toute personne atteignant les ports peut déposer des documents, déclencher des analyses, lire les dossiers clients et consommer le quota LLM.

Déjà identifié comme limite fonctionnelle dans le rapport de projet. En sécurité, c'est le prérequis de tout le reste : les autres protections n'ont de sens qu'une fois l'accès contrôlé.

**Correction** : une clé d'API partagée en en-tête, vérifiée par une dépendance FastAPI, suffirait pour un environnement de démonstration. Un vrai déploiement demande OAuth2/OIDC avec rôles (analyste, administrateur).

### M2 — mongo-express exposé sans authentification

`docker-compose.yml:19-30`

```yaml
ports:
  - "8081:8081"
environment:
  ME_CONFIG_BASICAUTH: false
```

Interface d'administration complète de MongoDB, accessible sans mot de passe sur le port 8081, avec les identifiants admin de la base injectés dedans. Lecture **et écriture** sur tous les dossiers clients.

**Correction** : activer `ME_CONFIG_BASICAUTH: true` avec des identifiants, ne publier le port que sur `127.0.0.1`, ou retirer le service des environnements autres que le poste de développement (profil Compose dédié).

### M3 — Bases de données publiées sur l'hôte

| Port | Service |
|---|---|
| 27017 | MongoDB |
| 5432 | PostgreSQL |
| 8010 | ChromaDB |

Ces ports n'ont pas besoin d'être joignables depuis l'extérieur : les services communiquent par le réseau Docker interne. Les publier élargit la surface d'attaque sans contrepartie.

**Correction** : supprimer ces `ports:` (le réseau `credit_risk_network` suffit), ou les restreindre à `127.0.0.1:27017:27017`.

### M4 — Deux dépendances vulnérables (`document-service`)

| Paquet | Version | Avis | Correctif |
|---|---|---|---|
| cryptography | 49.0.0 | PYSEC-2026-3552 | 50.0.0 |
| pypdf2 | 3.0.1 | PYSEC-2026-1835 | 3.9.0 |

`PyPDF2` est par ailleurs **abandonné en amont** (remplacé par `pypdf`). À vérifier : le code utilise `pdfplumber` pour l'extraction — si `PyPDF2` n'est plus appelé, le retirer purement et simplement est la meilleure correction.

---

## 🟡 BASSE

### B1 — Tous les conteneurs tournent en root

Aucun des cinq `Dockerfile` ne contient de directive `USER`. Une exécution de code dans un conteneur s'y fait avec les droits root.

```dockerfile
RUN adduser --disabled-password --gecos "" appuser
USER appuser
```

### B2 — Mot de passe PostgreSQL de repli en dur

`agentic-service/app/db/checkpointer.py:25`

```python
POSTGRES_CHECKPOINT_URI = os.environ.get(
    "POSTGRES_CHECKPOINT_URI",
    "postgresql://agentic:agentic_checkpoint_pwd@localhost:5432/agentic_checkpoints",
)
```

Le repli n'est utilisé qu'en développement local hors Docker, et la variable est bien fournie en conteneur. Le risque réel est faible, mais le mot de passe est versionné. Préférer une erreur explicite en l'absence de variable.

### B3 — Modèle Hugging Face chargé sans révision épinglée

`agentic-service/app/ingestion/chunker.py:63` — `AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)` sans paramètre `revision`. Le contenu téléchargé peut changer en amont sans que rien ne le signale (risque de chaîne d'approvisionnement). Épingler un commit : `from_pretrained(nom, revision="<sha>")`.

### B4 — `node_modules` versionné

1 495 fichiers de `frontend/node_modules` sont suivis par Git. Ce n'est pas une faille en soi, mais cela alourdit le dépôt, pollue toute analyse de sécurité (les faux positifs relevés plus haut en venaient tous) et fige des dépendances hors du contrôle du gestionnaire de paquets.

**Correction** : ajouter `node_modules/` au `.gitignore` puis `git rm -r --cached frontend/node_modules`.

---

## ⚪ Faux positifs analysés

**Bandit B608 — injection SQL** (`agentic-service/app/db/analysis_store.py:63` et `:84`)

Signalé parce que la requête est construite par f-string. La partie interpolée est une **constante de module** (`_TABLE = "analysis_results"`), et toutes les valeurs venant de l'appelant passent par des paramètres liés `%s`. Aucune injection possible.

Pour éteindre l'alerte sans masquer de vraies détections :

```python
cur.execute(  # nosec B608 - nom de table constant, valeurs en paramètres liés
    f"SELECT payload FROM {_TABLE} WHERE client_id = %s", (client_id,)
)
```

---

## Ce que le SAST ne couvre pas

Trois risques propres à cette architecture, qu'aucun outil statique ne détecte :

1. **Injection de prompt** — le contenu des PDF remonte jusqu'au LLM. Un document contenant des instructions peut tenter de détourner l'agent d'analyse. Atténuation partielle déjà en place : l'agent ne produit aucune valeur chiffrée, et la décision est calculée en Python hors de son contrôle. L'impact se limite donc à la conclusion rédigée.
2. **Fuite de données vers les fournisseurs LLM** — des données financières client sont envoyées à Groq et OpenRouter. À traiter contractuellement et à mentionner dans toute analyse d'impact.
3. **Absence de journalisation d'audit** — aucune trace de qui a déclenché quelle analyse. Indispensable en environnement réglementé.

---

## Ordre de traitement recommandé

1. **Immédiat** — appeler `validate_client_id` sur `/analyze` et `/client` (2 lignes)
2. **Immédiat** — `ME_CONFIG_BASICAUTH: true` et dépublier les ports de bases
3. **Court terme** — retirer ou mettre à jour PyPDF2, mettre à jour cryptography
4. **Court terme** — sortir `node_modules` du suivi Git
5. **Moyen terme** — authentification des API, utilisateur non-root dans les images
6. **À planifier** — journal d'audit, épinglage du modèle HF

---

## Intégration en CI

À ajouter au `.gitlab-ci.yml`, en `allow_failure: true` le temps du tri, puis à durcir :

```yaml
security:sast:
  stage: test
  image: python:3.12-slim
  before_script:
    - pip install --quiet bandit pip-audit
  script:
    - bandit -r */app -f json -o bandit.json -ll
    - pip-audit -r document-service/requirements.txt
  allow_failure: true
```

Le scan de secrets, lui, doit bloquer dès sa mise en place : un secret commité ne se négocie pas.

---

# Correctifs appliqués — 23 août 2026

Vérification après correction : **Bandit 0 alerte** sur 5 763 lignes (contre 3), **pip-audit 0 CVE** (contre 2), **npm audit 0**, et les quatre suites de tests au vert (292 tests).

| # | Constat | Statut | Fichiers |
|---|---|---|---|
| 🔴 | Traversée de chemin sur `/analyze` | **Corrigé** | `document-service/app/main.py` |
| 🟠 M2 | mongo-express sans authentification | **Corrigé** | `docker-compose.yml` |
| 🟠 M3 | Bases exposées sur l'hôte | **Corrigé** | `docker-compose.yml` |
| 🟠 M4 | 2 dépendances vulnérables | **Corrigé** | `document-service/requirements.txt` |
| 🟡 B1 | Conteneurs en root | **Corrigé** | 4 `Dockerfile` |
| 🟡 B2 | Mot de passe de repli en dur | **Corrigé** | `agentic-service/app/db/` |
| 🟡 B3 | Modèle HF non épinglé | **Corrigé** | `chunker.py` |
| 🟡 B4 | `node_modules` versionné | **Corrigé** | `.gitignore` |
| ⚪ | Faux positifs B608 | **Cause supprimée** | `analysis_store.py` |
| 🟠 M1 | Authentification des API | **Non traité** | décision produit |

## Détail des corrections

**Traversée de chemin.** `validate_client_id` est désormais appelée sur `/analyze` et `/client`, en plus de `/upload`. Défense en profondeur ajoutée : le chemin est résolu par `os.path.realpath` puis confiné sous la racine via `os.path.commonpath`, pour que la sécurité ne repose pas uniquement sur la forme de l'identifiant.

**mongo-express.** `ME_CONFIG_BASICAUTH` passé à `true`, avec identifiants par variables d'environnement. `MONGO_EXPRESS_PASSWORD` est déclarée obligatoire via la syntaxe `:?` : le service refuse de démarrer si elle manque, plutôt que de repartir sur une valeur par défaut.

**Ports.** MongoDB, PostgreSQL, ChromaDB et mongo-express ne sont plus publiés que sur `127.0.0.1`. Les services continuent de communiquer par le réseau interne `credit_risk_network`, inchangé.

**Dépendances.** `PyPDF2` supprimé — vérifié comme jamais importé, l'extraction passant par `pdfplumber`, et abandonné en amont. `cryptography` monté en 50.0.0. Le fichier `requirements.txt` est en UTF-16, son encodage a été préservé.

**Conteneurs.** Utilisateur `appuser` ajouté aux quatre images. Pour `agentic-service`, deux ajustements étaient nécessaires : l'arborescence est `/code` et non `/app`, et le modèle d'embedding écrit dans le cache HuggingFace au premier usage — `HF_HOME` est donc déplacé sous le répertoire personnel de `appuser`, avec le volume `hf_cache` repointé en conséquence. Sans cela, le téléchargement du modèle aurait échoué en écriture.

**Mot de passe de repli.** Retiré du dépôt. La garde a été placée **à l'usage** et non à l'import : lever une erreur au chargement du module aurait rendu `agentic-service` non importable par les tests et la CI, qui n'ouvrent jamais de connexion. Une fonction `_uri_requise()` centralise le contrôle, appelée par `checkpointer.py`, `analysis_store.py` et `history.py`.

**Modèle HuggingFace.** `AutoTokenizer.from_pretrained` reçoit désormais un paramètre `revision`, piloté par `EMBEDDING_MODEL_REVISION` et valant `main` par défaut — comportement identique au précédent, mais épinglable sur un commit sans toucher au code.

**Faux positifs B608.** Plutôt que d'ajouter `# nosec`, la cause a été supprimée : le nom de table étant une constante, il est écrit littéralement dans les requêtes. L'alerte disparaît sans suppression, et le code ne contient plus aucune construction SQL dynamique.

## Dépendances de test complétées

Les suites ajoutées récemment (`test_api_routes.py`, `test_db_service.py`, `test_api.py`) tiraient des imports absents de `agentic-service/requirements-test.txt` : `fastapi`, `psycopg[binary]` et `langgraph-checkpoint-postgres` y ont été ajoutés. Les autres services les installent déjà via la CI.

## Reste à traiter

**M1 — Authentification.** Non appliqué volontairement : c'est une décision produit, pas un correctif technique. Une clé d'API partagée en en-tête, vérifiée par une dépendance FastAPI, suffirait pour une démonstration ; un déploiement réel demande OAuth2/OIDC avec rôles, et impacterait le frontend.

**Journal d'audit** et **contractualisation de l'envoi de données financières aux fournisseurs LLM** restent ouverts.

## À faire avant de relancer la plateforme

Ajouter au fichier `.env` de la racine :

```
MONGO_EXPRESS_USER=admin
MONGO_EXPRESS_PASSWORD=<mot_de_passe_choisi>
```

Puis reconstruire les images, les Dockerfiles ayant changé :

```
docker compose build
docker compose up -d
```

Le volume `hf_cache` ayant changé de point de montage, le modèle d'embedding sera retéléchargé une fois (environ 2 Go).

---

# Complément — analyse complétée le 23 août 2026

La première passe n'avait couvert que Bandit, pip-audit et npm audit. Les outils manquants ont été exécutés : **Semgrep**, **Gitleaks**, **Trivy** et **Hadolint**.

## Résultats des outils ajoutés

| Outil | Périmètre | Résultat |
|---|---|---|
| Gitleaks 8.30.1 | 20 commits, 33,7 Mo d'historique | **0 fuite** |
| Gitleaks (disque) | Arborescence complète | 10 secrets, tous dans des `.env` non suivis |
| Semgrep 1.174 | 267 règles, 174 fichiers, Python **et TypeScript** | 1 alerte, **corrigée** |
| Trivy config | 5 Dockerfiles + compose | **0 mauvaise configuration** |
| Trivy fs | Verrous de dépendances | **14 CVE** (1 critique) |
| Hadolint 2.15.1 | 5 Dockerfiles | 4 avertissements d'épinglage |

## Ce que ces outils ont trouvé et que les précédents avaient manqué

### 1. Semgrep — `frontend/Dockerfile` sans `USER` — **CORRIGÉ**

J'avais ajouté un utilisateur non privilégié aux quatre services Python mais oublié le frontend. Semgrep l'a relevé (`dockerfile.security.missing-user`, CWE-250). Corrigé : l'image `node` fournit déjà un utilisateur `node`, désormais propriétaire de `/app`.

C'est aussi la confirmation que **Bandit seul laissait le frontend sans aucune analyse de code** : il n'analyse pas le TypeScript.

### 2. Trivy — 14 CVE dans les `poetry.lock` — **NON CORRIGÉ**

Découverte la plus importante de cette seconde passe. `pip-audit` avait été lancé sur les `requirements.txt`, mais `agentic-service` et `document-service` déclarent leurs dépendances dans des **`poetry.lock`**, jamais audités.

**`agentic-service` — 10 CVE**

| Paquet | Version | CVE | Sévérité | Correctif |
|---|---|---|---|---|
| langchain-core | 0.3.76 | CVE-2025-68664 | **CRITIQUE** | 0.3.81 |
| langchain-core | 0.3.76 | CVE-2025-65106 | Haute | 0.3.80 |
| langchain-core | 0.3.76 | CVE-2026-44843 | Haute | 0.3.85 |
| langchain-core | 0.3.76 | CVE-2026-34070 | Haute | 1.2.22 (majeure) |
| langgraph-checkpoint | 2.1.2 | CVE-2025-64439 | Haute | 3.0.0 (majeure) |
| transformers | 4.57.6 | CVE-2026-4372 | Haute | 5.3.0 (majeure) |
| transformers | 4.57.6 | CVE-2026-5241 | Haute | 5.5.0 (majeure) |
| starlette | 0.37.2 | CVE-2024-47874 | Haute | 0.40.0 |
| starlette | 0.37.2 | CVE-2026-48818 | Haute | 1.1.0 (majeure) |
| starlette | 0.37.2 | CVE-2026-54283 | Haute | 1.3.1 (majeure) |

**`document-service` — 4 CVE** : `cryptography` 49.0.0 et les trois mêmes `starlette`.

### Exploitabilité réelle, vérifiée dans le code

Toutes ces CVE ne se valent pas dans ce projet. Vérification faite :

| CVE | Applicable ici ? | Justification |
|---|---|---|
| CVE-2025-64439 — RCE dans le sérialiseur LangGraph | **Oui, directement** | `PostgresSaver` est utilisé pour tous les checkpoints d'agents (`checkpointer.py:48`) |
| CVE-2025-68664 — exécution de code par injection de sérialisation | **Oui** | Même chaîne de sérialisation d'état |
| CVE-2024-47874 — déni de service multipart | **Oui** | `document-service` accepte des `UploadFile` (`main.py:121`) |
| CVE-2026-48818 — SSRF via chemins UNC dans `StaticFiles` | **Non** | `StaticFiles` n'est utilisé nulle part |
| CVE-2026-5241 — exécution de code via `trust_remote_code` | **Non** | Ce paramètre n'apparaît nulle part |
| CVE-2026-4372 — RCE `transformers` | **Faible** | Un seul modèle chargé, fixe et désormais épinglé par révision |

### Correctifs recommandés, par ordre de risque de régression

**Sans risque — montées de version corrective :**

```
langchain-core : 0.3.76 -> 0.3.85   (corrige 3 CVE sur 4, dont la CRITIQUE)
starlette      : 0.37.2 -> 0.40.0   (corrige le déni de service multipart, le seul applicable)
cryptography   : 49.0.0 -> 50.0.0   (déjà fait dans requirements.txt, reste à faire dans poetry.lock)
```

**À tester — montées de version majeures :**

```
langgraph-checkpoint : 2.1.2 -> 3.0.0   ⚠️ RCE applicable, mais couplé à la version de langgraph
transformers         : 4.57.6 -> 5.x    ⚠️ couplé à sentence-transformers, risque de rupture
starlette            : -> 1.3.1         ⚠️ transitive de FastAPI, impose de monter FastAPI
```

Ces montées n'ont **pas** été appliquées : elles demandent une exécution de la plateforme complète pour valider qu'aucune rupture n'apparaît, et Docker n'était pas disponible en fin de session. La montée de `langgraph-checkpoint` est celle à traiter en priorité, la vulnérabilité étant réellement atteignable.

### 3. Hadolint — épinglage de versions

| Règle | Fichiers | Constat |
|---|---|---|
| DL3013 | document, agentic, report | `pip install poetry` sans version : la version de Poetry peut dériver d'une construction à l'autre |
| DL3008 | report-service | `apt-get install` sans version |
| DL3066 | les 5 | Utilisateur désigné par son nom plutôt que par un identifiant numérique — informatif |

Même nature que l'épinglage du modèle HuggingFace déjà corrigé : reproductibilité et chaîne d'approvisionnement, pas de vulnérabilité directe.

### 4. Gitleaks — confirmation du premier constat

Les 20 commits de l'historique sont **propres**, avec les ~150 règles de Gitleaks et non plus seulement les motifs que j'avais écrits à la main. Les 10 secrets détectés sur le disque sont dans `.env` et `agentic-service/.env`, tous deux non suivis par Git et couverts par le `.gitignore`. C'est le comportement attendu.

## Intégration en CI — faite

Quatre travaux ajoutés à `.gitlab-ci.yml` :

| Travail | Outil | Régime |
|---|---|---|
| `security:secrets` | Gitleaks sur l'historique | **Bloquant** |
| `security:sast` | Bandit + Semgrep | `allow_failure` |
| `security:dependances` | Trivy (verrous de dépendances) | `allow_failure` |
| `security:conteneurs` | Trivy config | `allow_failure` |

La détection de secrets bloque d'emblée : un secret commité doit être révoqué, pas discuté en revue. Les trois autres sont en `allow_failure` le temps du tri, à durcir une fois les CVE traitées.

## État final

| Contrôle | Résultat |
|---|---|
| Bandit | 0 alerte / 5 763 lignes |
| Semgrep | 0 alerte / 267 règles, après correction |
| Gitleaks (historique) | 0 fuite |
| Trivy config | 0 mauvaise configuration |
| npm audit | 0 vulnérabilité |
| pip-audit | 0 CVE |
| **Trivy fs** | **14 CVE — à traiter** |

## Reste ouvert

1. **Les 14 CVE de dépendances** — 3 corrigeables sans risque, le reste demande des tests
2. **M1 — authentification des API** — décision produit
3. **Scan des images Docker construites** — `trivy image`, nécessite Docker démarré
4. **Journal d'audit** et contractualisation de l'envoi de données aux fournisseurs LLM

---

# Traitement des CVE de dépendances — 23 août 2026

Docker étant redevenu disponible, les montées de version ont pu être appliquées **et vérifiées en exécution**.

## Résultat

| | Avant | Après |
|---|---|---|
| CVE totales | **14** | **4** |
| dont CRITIQUE | 1 | **0** |
| `document-service` | 4 | **0** |
| `agentic-service` | 10 | 4 |

## Ce qui a été monté

| Paquet | Avant | Après | CVE corrigées |
|---|---|---|---|
| langchain-core | 0.3.76 | **0.3.86** | 3 dont la CRITIQUE (CVE-2025-68664) |
| fastapi | 0.111.0 | **0.141.1** | — (débloque starlette) |
| starlette | 0.37.2 | **1.6.0** | 3, dans les **deux** services |
| cryptography | 49.0.0 | **50.0.0** | 1 |

### Une correction de mon analyse initiale

J'avais classé la montée de `starlette` comme « sans risque ». C'était faux : `fastapi ^0.111` épingle `starlette <0.38.0`, la montée était donc **impossible sans monter FastAPI**. Vérifié après coup :

```
fastapi 0.111.0 -> starlette<0.38.0,>=0.37.2
fastapi 0.115.14 -> starlette<0.47.0,>=0.40.0
fastapi 0.141.1 -> starlette>=0.46.0        (plus de borne haute)
```

Le passage à FastAPI 0.141 était le seul moyen d'atteindre une version de starlette corrigée sur les trois CVE. C'est un saut de trente versions mineures, donc un changement réel — et c'est pourquoi il a été validé par une exécution, pas seulement par une résolution de dépendances.

### Vérification en exécution

`document-service` reconstruit et démarré avec FastAPI 0.141.1 / starlette 1.6.0 / pydantic 2.13.4. Comportement contrôlé sur les trois cas :

| Requête | Réponse | Vérifie |
|---|---|---|
| `POST /analyze/mauvais!identifiant` | **400** « Identifiant client invalide » | Le correctif de traversée est atteint |
| `GET /client/mauvais!identifiant` | **400** idem | Idem sur la seconde route |
| `POST /analyze/client_valide_inexistant` | **404** « Dossier introuvable » | Le chemin nominal fonctionne toujours |

La faille de traversée de chemin est donc fermée et vérifiée en conditions réelles, pas seulement par lecture du code.

## Les 4 CVE restantes — et pourquoi elles ne sont pas traitées

Toutes exigent des **versions majeures** couplées à d'autres paquets du projet.

| Paquet | Correctif requis | Couplage bloquant | Applicable au projet ? |
|---|---|---|---|
| langgraph-checkpoint 2.1.2 | 3.0.0 | Lié à la version de `langgraph` (^0.2) — les deux doivent monter ensemble | **Oui** : `PostgresSaver` sérialise tous les états d'agents |
| langchain-core 0.3.86 | 1.2.22 | Rupture majeure de l'écosystème LangChain, impose de monter `langgraph`, `langchain-groq` et `langchain-openai` | Partiellement |
| transformers 4.57.6 | 5.3.0 / 5.5.0 | Lié à `sentence-transformers ^3.0` | **Faible** : un seul modèle chargé, fixe, désormais épinglé par révision |

**La priorité parmi les quatre est `langgraph-checkpoint`** : c'est la seule dont la vulnérabilité soit directement atteignable dans le flux normal de la plateforme. Sa correction impose de migrer LangGraph 0.2 → 1.x, ce qui touche le graphe d'agents, le checkpointer et le routage — un chantier à part entière, à mener avec la suite de tests comme filet.

Les deux autres sont à traiter lors d'une montée planifiée de l'écosystème, pas en correctif de sécurité isolé.

## Scan des images Docker construites

Dernier point du plan, réalisé une fois Docker disponible.

| Image | CVE critiques | Correctif disponible |
|---|---|---|
| document-service | 3 (`perl-base`) | **Aucun en amont** |
| financial-service | 3 (`perl-base`) | **Aucun en amont** |
| report-service | 7 (`perl-base`, `libxml2`, `libsqlite3`, `zlib1g`, `libglib2.0`) | **Aucun en amont** |
| frontend | 1 (`tar`) | 7.5.19, non encore livrée par Node |

Toutes ces vulnérabilités proviennent des **images de base**, pas du code du projet. Les paquets Debian concernés n'ont, à ce jour, aucun correctif publié en amont : il n'y a rien à monter. La seule mitigation est de reconstruire régulièrement les images pour absorber les mises à jour dès qu'elles paraissent.

Le cas du frontend a été traité partiellement : l'image de base est passée de `node:20-alpine` à `node:22-alpine`, ce qui monte le `tar` embarqué dans npm de 6.2.1 à 7.5.11. Le correctif complet est en 7.5.19, non encore présente dans une image Node officielle. Exploitabilité faible : ce `tar` appartient à npm et n'est sollicité qu'à l'installation des paquets, jamais à l'exécution de l'application. Le passage à Node 22 aligne au passage l'image sur celle déjà utilisée par la CI.

## Vérification finale en exécution

Plateforme entièrement reconstruite et démarrée avec l'ensemble des correctifs :

| Contrôle | Résultat |
|---|---|
| Les 9 conteneurs démarrent | ✅ |
| `/health` des 4 services applicatifs | ✅ 200 |
| Frontend | ✅ 200 |
| Utilisateur des conteneurs | ✅ `appuser` (×4), `node` (frontend) — plus aucun root |
| mongo-express sans identifiants | ✅ **401** |
| Ports des bases et de mongo-express | ✅ liés à `127.0.0.1` uniquement |
| Traversée de chemin, identifiant invalide | ✅ **400** sur `/analyze` et `/client` |
| Chemin nominal | ✅ 404 « dossier introuvable », comportement inchangé |
