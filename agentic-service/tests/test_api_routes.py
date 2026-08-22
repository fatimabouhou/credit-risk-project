import pytest
from fastapi import HTTPException

import api.routes as routes


def test_get_last_analysis_returns_404_when_client_is_unknown(monkeypatch):
    monkeypatch.setattr(routes, "get_latest_analysis", lambda client_id: None)

    with pytest.raises(HTTPException) as error:
        routes.get_last_analysis("client-inconnu")

    assert error.value.status_code == 404


def test_get_last_analysis_returns_saved_payload(monkeypatch):
    saved = {"client_id": "client-1", "decision": {"decision": "accord"}}
    monkeypatch.setattr(routes, "get_latest_analysis", lambda client_id: saved)

    assert routes.get_last_analysis("client-1") == saved


def test_analyze_returns_503_when_checkpointer_is_not_ready(monkeypatch):
    monkeypatch.setattr(routes, "checkpointer", None)

    with pytest.raises(HTTPException) as error:
        routes.analyze_client("client-1")

    assert error.value.status_code == 503


def test_decision_route_translates_agent_failure_to_500(monkeypatch):
    monkeypatch.setattr(routes, "decide_credit", lambda diagnostic: (_ for _ in ()).throw(RuntimeError("provider")))

    with pytest.raises(HTTPException) as error:
        routes.test_decision_agent({})

    assert error.value.status_code == 500