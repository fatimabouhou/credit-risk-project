"""
Outil de profil client — données brutes extraites du dossier (document-service).

Rôle : donner à l'agent accès aux informations déclaratives réelles du
client (raison sociale, secteur d'activité en texte libre, comportement
bancaire...), extraites par document-service depuis les PDF du dossier.

Sans cet outil, l'agent n'a aucun moyen de connaître le secteur réel d'un
client — ratios_financiers_n (financial_report_tool) ne contient aucune
donnée de profil, et le RAG ne connaît que des normes génériques, jamais
un client en particulier. C'est ce manque qui faisait deviner un secteur
à l'agent au lieu de le lire (voir 00_segmentation_reference.md § 4 : le
secteur doit être déterminé à partir des données disponibles, jamais
choisi par défaut).

Appelle l'API HTTP de document-service (GET /client/{client_id}, lecture
seule — ne relance jamais l'extraction), même pattern que
financial_report_tool.py vers financial-service.
"""

import os

import httpx

DOCUMENT_SERVICE_URL = os.environ.get("DOCUMENT_SERVICE_URL", "http://localhost:8000")


def get_client_profile(client_id: str, timeout: float = 15.0) -> dict:
    """
    Récupère le dossier client déjà extrait (profil administratif,
    conformité, historique financier, comportement bancaire).
    Lève httpx.HTTPStatusError (404) si aucune extraction n'a encore été
    faite pour ce client — dans ce cas, le POST /analyze/{client_id} de
    document-service doit être déclenché avant de pouvoir lire son profil.
    """
    url = f"{DOCUMENT_SERVICE_URL}/client/{client_id}"
    response = httpx.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    import json
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    client_id = sys.argv[1] if len(sys.argv) > 1 else "data"
    profile = get_client_profile(client_id)
    print(json.dumps(profile.get("profil_administratif"), ensure_ascii=False, indent=2))
