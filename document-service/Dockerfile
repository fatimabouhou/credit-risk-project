FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 1. Installation de Poetry
RUN pip install --no-cache-dir poetry

# 2. Copie des fichiers de configuration
COPY pyproject.toml poetry.lock* ./

# 3. Configuration de Poetry & installation des dépendances
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# 4. Copie du reste du code
COPY . .

# 5. Lancement de l'API FastAPI (les routes de app/main.py, dont l'extraction
# déclenchée par POST /analyze/{client_id} - pas le script de test autonome
# de document_processor.py, qui relançait une extraction à chaque démarrage
# du conteneur au lieu de servir l'API).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]