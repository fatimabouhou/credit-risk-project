# 1. Utiliser une image Python officielle légère
FROM python:3.12-slim

# 2. Définir le répertoire de travail
WORKDIR /app

# 3. Variables d'environnement pour Python et Poetry
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

# 4. Installer Poetry directement via pip (version 2.x compatible avec le format PEP 621)
RUN pip install --no-cache-dir poetry==2.1.1

# 5. Copier uniquement les fichiers de dépendances pour le cache
COPY pyproject.toml poetry.lock* ./

# 6. Installer les dépendances Python via Poetry
RUN poetry install --no-root --only main

# 7. Copier tout le reste du code source
COPY . .

# 8. Exposer le port (8001 pour le financial-service)
EXPOSE 8001

# 9. Démarrer le serveur FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]