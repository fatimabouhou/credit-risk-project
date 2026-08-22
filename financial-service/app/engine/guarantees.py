from typing import Any, Dict, List, Optional


HAIRCUTS = {
    "hypotheque": 0.70,
    "nantissement": 0.50,
    "caution": 0.00,
}


def assess_guarantees(
    garanties: Optional[List[Dict[str, Any]]],
    montant_nouveau_credit: Optional[float],
) -> Dict[str, Any]:
    """Calcule une couverture indicative après décote, jamais une validation juridique."""
    garanties = garanties or []
    details = []
    valeur_retenue_totale = 0.0

    for garantie in garanties:
        type_garantie = garantie.get("type")
        valeur_declaree = garantie.get("valeur_declaree")
        haircut = HAIRCUTS.get(type_garantie, 0.0)
        valeur_retenue = valeur_declaree * haircut if isinstance(valeur_declaree, (int, float)) else None
        if valeur_retenue is not None:
            valeur_retenue_totale += valeur_retenue
        details.append(
            {
                **garantie,
                "decote": haircut,
                "valeur_retenue_indicative": round(valeur_retenue, 2) if valeur_retenue is not None else None,
            }
        )

    if not montant_nouveau_credit or montant_nouveau_credit <= 0:
        return {
            "evaluable": False,
            "couverture_pct": None,
            "valeur_retenue_indicative": round(valeur_retenue_totale, 2),
            "garanties": details,
            "statut": "montant_credit_manquant",
        }

    couverture_pct = valeur_retenue_totale / montant_nouveau_credit * 100
    return {
        "evaluable": True,
        "couverture_pct": round(couverture_pct, 2),
        "valeur_retenue_indicative": round(valeur_retenue_totale, 2),
        "garanties": details,
        "statut": "a_verifier",
    }
