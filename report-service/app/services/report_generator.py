"""
Génération du rapport de crédit final (PDF) à partir des données déjà
récupérées (extraction + analyse/décision, voir infrastructure/http_client.py).

Aucun LLM ici : "conclusion" (agent 1) et "justification" (agent 2) sont
déjà du texte final rédigé ailleurs ; ce module se contente de les
insérer dans un template HTML fixe (templates/report.html) puis de le
convertir en PDF (WeasyPrint) — mise en page garantie identique à chaque
génération, contrairement à un LLM à qui on redemanderait de "suivre un
format" à chaque appel. Même choix, déjà fait ailleurs dans ce projet,
de sortir du LLM tout ce qui doit être fiable/reproductible (voir
agentic-service/app/graph/decision.py et _inject_altman_sentence dans
agentic-service/app/api/routes.py).
"""

import base64
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_LOGO_PATH = Path(__file__).resolve().parent.parent / "static" / "devoteam-logo.png"

_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)


def _load_logo_data_uri() -> str | None:
    """
    Encodée en base64 et embarquée directement dans le HTML plutôt que
    référencée par chemin de fichier : WeasyPrint résout les chemins
    relatifs par rapport à un `base_url` qu'il faudrait sinon configurer
    et garder cohérent entre le rendu HTML de dev (/preview) et le PDF —
    un data URI marche identiquement dans les deux cas, sans dépendance
    à l'endroit d'où le HTML est servi.
    """
    if not _LOGO_PATH.exists():
        return None
    encoded = base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


_LOGO_DATA_URI = _load_logo_data_uri()


def _v(entry):
    """
    Certains champs d'extraction (comptes_bancaires, centrale_risques,
    dette_existante — voir document-service/app/services/extractors/
    banking_extractor.py, _make_entry) sont tracés sous la forme
    {"value", "source", "page"}, d'autres (profil_administratif,
    conformite_reglementaire) sont des valeurs brutes. Ce helper
    uniformise les deux plutôt que de dupliquer la logique de
    dépaquetage dans le template.
    """
    if isinstance(entry, dict) and set(entry.keys()) == {"value", "source", "page"}:
        return entry["value"]
    return entry


def _build_context(client_id: str, extraction: dict, analysis: dict) -> dict:
    profil = extraction.get("profil_administratif") or {}
    conformite_extraction = extraction.get("conformite_reglementaire") or {}
    bancaire = extraction.get("comportement_bancaire") or {}

    fiche = profil.get("fiche_renseignements") or {}
    demande = profil.get("demande_credit") or {}

    centrale = bancaire.get("centrale_risques") or {}
    dette = bancaire.get("dette_existante") or {}
    comptes = bancaire.get("comptes_bancaires") or []

    decision = analysis.get("decision") or {}

    return {
        "client_id": client_id,
        "date_generation": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "logo_data_uri": _LOGO_DATA_URI,
        "extraction": {
            "raison_sociale": _v(fiche.get("raison_sociale")),
            "secteur_declare": _v(fiche.get("secteur")),
            "capital_social": _v(fiche.get("capital_social")),
            "date_creation": _v(fiche.get("creation")),
            "montant_demande": _v(demande.get("montant_demande")),
            "duree_demande": _v(demande.get("duree")),
            "objet_demande": _v(demande.get("objet")),
            "attestations": conformite_extraction.get("attestations_legales") or [],
            "centrale_risques": {
                "taux_utilisation": _v(centrale.get("taux_utilisation")),
                "statut_incidents": _v((centrale.get("incidents") or {}).get("statut_incidents")),
            },
            "dette_existante": {
                "mensualite_totale": _v(dette.get("mensualite_totale")),
                "capital_restant_total": _v(dette.get("capital_restant_total")),
            },
            "comptes_bancaires": [
                {
                    "banque": c.get("banque"),
                    "solde_fin_periode": _v(c.get("solde_fin_periode")),
                    "nombre_rejets": _v((c.get("comportement") or {}).get("nombre_rejets")),
                }
                for c in comptes
            ],
        },
        "analyse": {
            "secteur": analysis.get("secteur"),
            "taille": analysis.get("taille"),
            "ratios": analysis.get("ratios") or [],
            "anomalies": analysis.get("anomalies") or [],
            "patterns": analysis.get("patterns") or [],
            "altman_score": analysis.get("altman_score"),
            "dscr": analysis.get("dscr"),
            "conclusion": analysis.get("conclusion"),
            "alertes_coherence": analysis.get("alertes_coherence") or [],
        },
        "decision": {
            "decision": decision.get("decision"),
            "score": decision.get("score"),
            "justification": decision.get("justification"),
            "erreur": decision.get("erreur"),
        },
    }


def render_html(client_id: str, extraction: dict, analysis: dict) -> str:
    template = _env.get_template("report.html")
    return template.render(**_build_context(client_id, extraction, analysis))


def render_pdf(client_id: str, extraction: dict, analysis: dict) -> bytes:
    html_content = render_html(client_id, extraction, analysis)
    return HTML(string=html_content).write_pdf()
