# slim-bookworm plutôt que le tag flottant "slim" : celui-ci résout vers
# trixie/testing, dont le dépôt a renommé/retiré libgdk-pixbuf2.0-0 (utilisé
# ci-dessous), faisant échouer l'install avec "no installation candidate" —
# même classe de problème déjà rencontrée et corrigée dans
# agentic-service/Dockerfile (voir son commentaire d'en-tête).
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dépendances système requises par WeasyPrint (rendu HTML -> PDF via
# pango/cairo pour le texte et la mise en page ; pas un navigateur headless,
# donc pas de JS/Chromium ici, juste ces libs de rendu).
#
# Le sed force les sources APT en HTTPS : en clair (http://deb.debian.org),
# ce build subissait des "403 Forbidden" et "Hash Sum mismatch" en boucle sur
# le CDN Fastly qui sert ce mirror (44 min de build ; 3 paquets en échec
# définitif) — signature d'une interception/altération du trafic HTTP en
# clair sur le chemin réseau (proxy, pare-feu, antivirus), pas d'une lenteur
# du mirror lui-même (un simple "apt-get update" en HTTP répondait en 16s).
# Testé : le même install passe en HTTPS en ~1 minute, sans aucune erreur.
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

COPY . .


# Exécution sans privilèges : une exécution de code dans le conteneur ne doit
# pas se faire avec les droits root. Les fichiers copiés lui appartiennent.
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
