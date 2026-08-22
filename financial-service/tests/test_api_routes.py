import pytest
from fastapi import HTTPException

from app.api import routes


def test_evaluate_returns_404_when_document_service_has_no_audit(monkeypatch):
    monkeypatch.setattr(routes.db_service, "get_client_audit", lambda client_id: None)

    with pytest.raises(HTTPException) as error:
        routes.evaluate_client_dossier("client-1")

    assert error.value.status_code == 404


def test_evaluate_calculates_saves_and_returns_report(monkeypatch):
    audit = {"client_id": "client-1"}
    report = {"dscr": 1.5, "altman_score": {"zone": "safe"}}
    calls = {}

    monkeypatch.setattr(routes.db_service, "get_client_audit", lambda client_id: audit)
    monkeypatch.setattr(
        routes.FinancialEvaluator,
        "evaluate_full_dossier",
        lambda document, **options: calls.update(document=document, options=options) or report,
    )
    monkeypatch.setattr(
        routes.db_service,
        "save_evaluation_report",
        lambda client_id, value: calls.update(saved=(client_id, value)) or True,
    )

    result = routes.evaluate_client_dossier(
        "client-1", is_listed=True, is_manufacturier=False, market_value_equity=100.0
    )

    assert result["report"] == report
    assert calls["document"] is audit
    assert calls["options"] == {
        "is_listed": True,
        "is_manufacturier": False,
        "market_value_equity": 100.0,
    }
    assert calls["saved"] == ("client-1", report)