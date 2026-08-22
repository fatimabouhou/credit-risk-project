import os
import re
from typing import Dict, List, NamedTuple

from fastapi import HTTPException, UploadFile

# Mapping catégorie -> (sous-dossier, nom de fichier final). Le nom de
# fichier est TOUJOURS généré côté serveur (jamais celui envoyé par
# l'utilisateur) : le routage des extracteurs (document_processor.py) est
# basé sur un test `"motclé" in filename.lower()` sur le nom de fichier
# (voir administrative_extractor.py, compliance_extractor.py,
# financial_extractor.py, banking_extractor.py) — un nom généré garantit
# que le mot-clé attendu est toujours présent, plutôt que de dépendre de
# ce que l'utilisateur a nommé son fichier sur son poste.
#
_CATEGORY_TO_SUBFOLDER = {
    "fiche_renseignements": "01_administratif",
    "demande_credit": "01_administratif",
    "attestation_dgi": "02_conformite",
    "attestation_cnss": "02_conformite",
    "bilan": "03_financier",
    "releve_attijariwafa": "04_bancaire",
    "releve_cih": "04_bancaire",
    "amortissement": "04_bancaire",
    "centrale_risques": "04_bancaire",
    "garanties": "05_garanties",
}

_CATEGORIES_REQUIRING_YEAR = {"bilan"}

_MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 Mo, largement suffisant pour un PDF de quelques pages
_CLIENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_YEAR_PATTERN = re.compile(r"^20\d{2}$")


class CategorizedFile(NamedTuple):
    file: UploadFile
    category: str
    year: str  # "" si non applicable (toutes les catégories sauf "bilan")


def _filename_for(category: str, year: str) -> str:
    if category == "bilan":
        return f"bilan_{year}.pdf"
    return f"{category}.pdf"


def validate_client_id(client_id: str) -> None:
    """Anti path-traversal : `client_id` finit dans un os.path.join non sanitisé
    en aval (voir main.py, POST /analyze/{client_id}) — un `../../etc` y
    passerait tel quel sans ce contrôle, rien d'existant ne le faisait avant."""
    if not _CLIENT_ID_PATTERN.match(client_id):
        raise HTTPException(
            status_code=400,
            detail="Identifiant client invalide : uniquement lettres, chiffres, '-' et '_'.",
        )


def _validate_entry(category: str, year: str) -> None:
    if category not in _CATEGORY_TO_SUBFOLDER:
        raise HTTPException(status_code=400, detail=f"Catégorie de document inconnue : '{category}'.")
    if category in _CATEGORIES_REQUIRING_YEAR and not _YEAR_PATTERN.match(year):
        raise HTTPException(
            status_code=400,
            detail=f"Catégorie '{category}' : année requise au format AAAA (ex: 2023), reçu '{year}'.",
        )


async def save_uploaded_documents(root_folder: str, entries: List[CategorizedFile]) -> Dict[str, List[str]]:
    """
    Valide et écrit chaque fichier uploadé au bon endroit dans l'arborescence
    attendue par DocumentProcessor. Écrase silencieusement un fichier
    précédent de la même catégorie/année (comportement volontaire : un
    nom de fichier généré est déterministe, un ré-upload est un remplacement,
    pas un ajout — évite l'accumulation de doublons que le processeur ne
    déduplique pas lui-même, voir document_processor.py).

    Retourne {sous_dossier: [noms de fichiers écrits]} pour le message de
    confirmation renvoyé au frontend.
    """
    written: Dict[str, List[str]] = {}

    for entry in entries:
        _validate_entry(entry.category, entry.year)

        filename = entry.file.filename or ""
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"'{filename}' : seuls les fichiers PDF sont acceptés.",
            )
        if entry.file.content_type not in ("application/pdf", "application/octet-stream"):
            raise HTTPException(
                status_code=400,
                detail=f"'{filename}' : type de fichier invalide ({entry.file.content_type}), un PDF est attendu.",
            )

        content = await entry.file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail=f"'{filename}' : fichier vide.")
        if len(content) > _MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"'{filename}' : dépasse la taille maximale autorisée ({_MAX_FILE_SIZE_BYTES // (1024 * 1024)} Mo).",
            )

        subfolder = _CATEGORY_TO_SUBFOLDER[entry.category]
        target_dir = os.path.join(root_folder, subfolder)
        os.makedirs(target_dir, exist_ok=True)

        target_filename = _filename_for(entry.category, entry.year)
        with open(os.path.join(target_dir, target_filename), "wb") as f:
            f.write(content)

        written.setdefault(subfolder, []).append(target_filename)

    return written
