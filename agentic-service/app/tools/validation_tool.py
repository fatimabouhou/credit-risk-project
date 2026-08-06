"""
Outil de validation — cohérence et conformité du dossier client.

document-service calcule déjà des contrôles de cohérence croisés à
l'extraction (`alertes_coherence` dans client_audits, ex. incidents de
paiement détectés à la Centrale des Risques BAM) et extrait le statut de
conformité réglementaire (`conformite_reglementaire` : attestations
DGI/CNSS). Ce module n'ajoute aucun contrôle nouveau — il extrait ces
deux sections précises du profil client (voir client_profile_tool.py),
pour que l'agent puisse juger de la fiabilité du dossier avant
d'interpréter les ratios qui en dérivent.

Un ratio "dans la norme" calculé à partir d'un dossier avec des alertes
de cohérence non résolues doit être lu différemment — d'où l'intérêt
d'un outil dédié plutôt que de laisser ce signal noyé dans le profil
complet retourné par outil_profil_client.
"""

from tools.client_profile_tool import get_client_profile


def get_validation_report(client_id: str) -> dict:
    """
    Retourne les alertes de cohérence croisée et le statut de conformité
    réglementaire (DGI/CNSS) déjà calculés par document-service pour ce
    client.
    """
    profile = get_client_profile(client_id)
    return {
        "client_id": client_id,
        "alertes_coherence": profile.get("alertes_coherence", []),
        "conformite_reglementaire": profile.get("conformite_reglementaire", {}),
    }


if __name__ == "__main__":
    import json
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    client_id = sys.argv[1] if len(sys.argv) > 1 else "data"
    print(json.dumps(get_validation_report(client_id), ensure_ascii=False, indent=2))
