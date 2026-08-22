import re
import unicodedata
from typing import Any, Dict, List

import pdfplumber


class GuaranteeExtractor:
    """Extrait les garanties déclarées, sans prétendre les valider juridiquement."""

    _TYPE_LABELS = {
        "hypotheque": "hypotheque",
        "nantissement": "nantissement",
        "caution": "caution",
    }

    @staticmethod
    def _normalize(value: str) -> str:
        return "".join(
            character for character in unicodedata.normalize("NFD", value.lower())
            if unicodedata.category(character) != "Mn"
        )

    @staticmethod
    def _parse_amount(value: str) -> float | None:
        normalized = value.replace("\u202f", "").replace(" ", "")
        normalized = normalized.replace(".", "").replace(",", ".")
        try:
            amount = float(normalized)
        except ValueError:
            return None
        return amount if amount > 0 else None

    def extract(self, pdf_path: str) -> Dict[str, Any]:
        garanties: List[Dict[str, Any]] = []
        current: Dict[str, Any] | None = None

        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception:
            return {"garanties": [], "statut_extraction": "echec"}

        for raw_line in text.splitlines():
            line = " ".join(raw_line.split())
            lower = line.lower()
            normalized = self._normalize(line)
            detected_type = next(
                (value for key, value in self._TYPE_LABELS.items() if key in normalized and re.match(r"^\d+\.", line)),
                None,
            )
            if detected_type:
                current = {"type": detected_type, "valeur_declaree": None, "statut": "a_verifier"}
                garanties.append(current)
                continue
            if current is None:
                continue

            amount_match = re.search(
                r"(?:valeur estimée|valeur d'acquisition|valeur)\s*:\s*([\d .]+(?:,[\d]+)?)",
                line,
                flags=re.IGNORECASE,
            )
            if amount_match:
                current["valeur_declaree"] = self._parse_amount(amount_match.group(1))

            engagement_match = re.search(r"couverture\s+à\s+hauteur\s+de\s+(\d+(?:[,.]\d+)?)\s*%", lower)
            if engagement_match:
                current["taux_engagement_pct"] = float(engagement_match.group(1).replace(",", "."))

        return {"garanties": garanties, "statut_extraction": "succes"}

    def process_folder(self, folder_path: str) -> Dict[str, Any]:
        import os

        files = [name for name in os.listdir(folder_path) if name.lower().endswith(".pdf")]
        if not files:
            return {"garanties": [], "statut_extraction": "aucun_document"}
        return self.extract(os.path.join(folder_path, sorted(files)[0]))
