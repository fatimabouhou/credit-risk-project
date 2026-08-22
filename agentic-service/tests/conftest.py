"""
Configuration commune des tests.

PROBLÈME RÉEL CONTOURNÉ ICI
---------------------------
Aucun module de ce service ne peut être importé isolément : la chaîne

    graph/decision.py
      -> tools/patterns/pattern_tool.py
        -> tools/patterns/context_builder.py
          -> tools/benchmark_tool.py
            -> tools/rag_tool.py
              -> ingestion/embedder.py
                -> sentence_transformers  (-> torch, ~2 Go)

fait que tester `compute_risk_score`, une fonction purement arithmétique qui
ne touche jamais au RAG, imposerait d'installer toute la pile d'embedding.
La même chaîne bloque `graph/workflow.py`, donc les tests de routage
existants.

Ces stubs remplacent uniquement les FEUILLES lourdes de cette chaîne, jamais
du code métier : rien de ce qui est testé ne passe par elles. Si un test
venait à en dépendre réellement, il échouerait bruyamment (les stubs lèvent
une erreur à l'usage) plutôt que de renvoyer un faux résultat.

La correction de fond serait de rendre ces imports paresseux dans
`context_builder.py` et `rag_tool.py`, pour que la logique déterministe soit
importable sans la pile ML. Tant que ce n'est pas fait, ce fichier garde la
CI légère (~50 Mo d'install au lieu de ~2 Go).
"""

import sys
import types


def _stub(nom: str, **attributs) -> types.ModuleType:
    """Module factice dont tout attribut non prévu explose à l'utilisation."""
    module = types.ModuleType(nom)
    for cle, valeur in attributs.items():
        setattr(module, cle, valeur)
    return module


class _IndisponibleEnTest:
    """Sentinelle : utilisable comme symbole importé, jamais comme service."""

    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "Dépendance d'embedding neutralisée dans les tests unitaires "
            "(voir tests/conftest.py). Un test qui en a besoin relève de "
            "l'intégration, pas de l'unitaire."
        )

    def __call__(self, *args, **kwargs):
        raise RuntimeError("Dépendance d'embedding neutralisée dans les tests unitaires.")


# Installés AVANT la collecte : pytest importe conftest.py en premier.
sys.modules.setdefault(
    "sentence_transformers",
    _stub("sentence_transformers", SentenceTransformer=_IndisponibleEnTest),
)
