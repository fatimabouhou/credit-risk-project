# --- Image de base ---
FROM python:3.11-slim

# Dépendances système nécessaires à sentencepiece / torch (compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# --- Installer Poetry ---
RUN pip install --no-cache-dir poetry

WORKDIR /code

# --- Copier UNIQUEMENT les fichiers de dépendances d'abord ---
# Astuce de cache Docker : tant que pyproject.toml/poetry.lock ne changent
# pas, Docker réutilise le layer d'installation (torch ne se réinstalle
# pas à chaque modification de code Python).
COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# --- Copier le code de l'application ---
COPY app ./app

# Le code du pipeline utilise des imports du type "ingestion.models" et
# est lancé depuis le dossier app/ (ex: python -m ingestion.chunker data/docs)
WORKDIR /code/app

# Commande par défaut : lance le service FastAPI.
# Pour tester le pipeline d'ingestion à la place, surcharge la commande
# au lancement (voir README / commandes docker run ci-dessous).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
