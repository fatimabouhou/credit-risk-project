from typing import Optional

from fastapi import APIRouter, HTTPException, status
import logging

from app.db.database_service import DatabaseService
from app.engine.evaluator import FinancialEvaluator

logger = logging.getLogger("FinancialAPI")
router = APIRouter()

# On instancie le service de base de données une seule fois
db_service = DatabaseService()

@router.post("/evaluate/{client_id}", status_code=status.HTTP_200_OK)
def evaluate_client_dossier(
    client_id: str,
    is_listed: bool = False,
    is_manufacturier: Optional[bool] = None,
    market_value_equity: Optional[float] = None,
):
    """
    Endpoint déclenché pour analyser un client.

    `is_listed` / `is_manufacturier` / `market_value_equity` : utilisés
    uniquement pour choisir la formule du score Altman Z (voir
    ScoringEngine.calculate_altman_z_score) — aucune de ces données
    n'est extraite automatiquement du dossier aujourd'hui, destinées à
    être saisies par l'utilisateur via une future interface. Sans elles,
    la formule Z'' (1995), la plus générale, est utilisée par défaut.
    """
    logger.info(f"📩 Requête reçue : Évaluation du client '{client_id}'")

    # 1. Récupération des données brutes depuis MongoDB (extraites par document-service)
    document_brut = db_service.get_client_audit(client_id)
    if not document_brut:
        logger.warning(f"⚠️ Client {client_id} introuvable.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Les données du client '{client_id}' sont introuvables. Le document-service a-t-il terminé ?"
        )

    # 2. Exécution des moteurs de calcul (Evaluator)
    try:
        report = FinancialEvaluator.evaluate_full_dossier(
            document_brut,
            is_listed=is_listed,
            is_manufacturier=is_manufacturier,
            market_value_equity=market_value_equity,
        )
    except Exception as e:
        logger.error(f"❌ Erreur critique lors du calcul pour {client_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne lors de l'évaluation financière : {str(e)}"
        )

    # 3. Sauvegarde du rapport final dans MongoDB
    saved = db_service.save_evaluation_report(client_id, report)
    if not saved:
        logger.error("❌ Échec de la sauvegarde du rapport en base de données.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Le calcul a réussi, mais l'enregistrement en BDD a échoué."
        )

    # 4. Retourne le rapport complet au service appelant
    return {
        "message": "Évaluation financière terminée avec succès.",
        "client_id": client_id,
        "report": report
    }