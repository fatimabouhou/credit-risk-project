# --- Image de base ---
# bookworm (Debian stable) plutôt que le tag flottant "slim" (résolu vers
# trixie/testing au moment où ce Dockerfile a été écrit) : le dépôt de
# testing change sous les pieds pendant un build (paquets remplacés entre
# le apt-get update et le fetch réel), d'où des 403/hash mismatch récurrents
# et non reproductibles avec l'image flottante.
#
# --- Build en 2 étapes ---
# build-essential (gcc/g++/make, ~46 paquets/300+ Mo) a été retiré : il ne
# servait qu'à compiler sentencepiece depuis les sources si aucune wheel
# précompilée n'était disponible. Vérifié le 2026-08-17 dans poetry.lock :
# TOUS les paquets (dont sentencepiece 0.2.2, tokenizers, safetensors,
# hf-xet) publient une wheel manylinux/x86_64 compatible cp311 — plus
# aucune compilation native n'est déclenchée par `poetry install`. Cet
# apt-get (46 paquets Debian, sujet à des 403/timeouts sur un mirroir lent,
# jusqu'à 23 min constatées) est donc devenu un coût pur sans bénéfice.
# Le stage "builder" reste utile (poetry + fichiers de deps n'ont pas à
# vivre dans l'image finale), il n'a juste plus besoin d'un compilateur.
FROM python:3.11-slim-bookworm AS builder

RUN pip install --no-cache-dir poetry

WORKDIR /code

# --- Copier UNIQUEMENT les fichiers de dépendances d'abord ---
# Astuce de cache Docker : tant que pyproject.toml/poetry.lock ne changent
# pas, Docker réutilise le layer d'installation (torch ne se réinstalle
# pas à chaque modification de code Python).
COPY pyproject.toml poetry.lock ./

# Le venv est créé DANS le projet (.venv) pour pouvoir être copié tel quel
# vers le stage final, plutôt qu'installé dans les site-packages système
# (virtualenvs.create false), qui ne se copient pas proprement seuls).
# Cache pip persistant (BuildKit --mount=type=cache, survit même à un
# --no-cache) : les wheels déjà téléchargées (torch, sentence-transformers...)
# ne sont pas re-téléchargées si ce layer doit être reconstruit.
RUN --mount=type=cache,target=/root/.cache/pypoetry,sharing=locked \
    --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    poetry config virtualenvs.in-project true \
    && poetry install --no-root --no-interaction --no-ansi --only main

# --- Image finale (sans compilateur) ---
FROM python:3.11-slim-bookworm

WORKDIR /code

COPY --from=builder /code/.venv /code/.venv
ENV PATH="/code/.venv/bin:$PATH"

# --- Copier le code de l'application ---
COPY app ./app

# Le code du pipeline utilise des imports du type "ingestion.models" et
# est lancé depuis le dossier app/ (ex: python -m ingestion.chunker data/docs)
WORKDIR /code/app

# Commande par défaut : lance le service FastAPI.
# Pour tester le pipeline d'ingestion à la place, surcharge la commande
# au lancement (voir README / commandes docker run ci-dessous).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
