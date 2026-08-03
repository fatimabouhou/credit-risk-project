"""
Outil de données déterministes — rapport financier calculé par financial-service.

Rôle : récupérer le rapport financier complet d'un client (ratios,
tendances sur 3 exercices, DSCR) déjà calculé par financial-service — la
"CALCULS & PRÉPARATION (DÉTERMINISTE)" du pipeline global, en amont de
l'analyse IA.

Appelle l'API HTTP de financial-service plutôt que MongoDB directement,
pour rester découplé de son schéma de base interne : document-service suit
déjà ce pattern (voir docker-compose.yml, FINANCIAL_SERVICE_URL) plutôt
que de lire ses collections en direct.

Anciennement "banking_tool.py" — renommé : l'endpoint qu'il appelle
retourne l'évaluation financière complète (ratios + tendances + DSCR), pas
spécifiquement des indicateurs bancaires (comportement_bancaire vit dans
client_audits, côté document-service, et n'est pas encore exposé par
financial-service).
"""

import os

import httpx

FINANCIAL_SERVICE_URL = os.environ.get("FINANCIAL_SERVICE_URL", "http://localhost:8001")


def get_financial_report(client_id: str, timeout: float = 30.0) -> dict:
    """
    Déclenche/récupère l'évaluation financière complète d'un client
    (ratios_financiers_n, analyse_tendances_3ans, couverture_dette_dscr).

    L'endpoint financial-service calcule à la volée (pas de cache côté
    agentic-service) : un appel répété reflète toujours l'état courant de
    client_audits. Lève httpx.HTTPStatusError si le client est introuvable
    (404) ou si le calcul échoue côté financial-service (500).
    """
    url = f"{FINANCIAL_SERVICE_URL}/api/v1/financial/evaluate/{client_id}"
    response = httpx.post(url, timeout=timeout)
    response.raise_for_status()
    return response.json()["report"]


if __name__ == "__main__":
    import json
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    client_id = sys.argv[1] if len(sys.argv) > 1 else "data"
    report = get_financial_report(client_id)
    print(json.dumps(report["ratios_financiers_n"], ensure_ascii=False, indent=2))
