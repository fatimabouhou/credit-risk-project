import pytest
from fastapi import HTTPException

from app import main


def test_analyze_client_folder_returns_404_for_missing_folder(monkeypatch):
    monkeypatch.setattr(main.os.path, "exists", lambda path: False)

    with pytest.raises(HTTPException) as error:
        main.analyze_client_folder("client-inconnu", object())

    assert error.value.status_code == 404