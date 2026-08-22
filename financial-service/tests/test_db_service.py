from app.db import database_service


class FakeDatabase:
    def __init__(self):
        self.raw_collection = FakeCollection()
        self.eval_collection = FakeCollection()

    def __getitem__(self, name):
        return self.raw_collection if name == "client_audits" else self.eval_collection

    def command(self, name):
        assert name == "ping"


class FakeCollection:
    def __init__(self):
        self.calls = []

    def find_one(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"client_id": "client-1"}

    def update_one(self, *args, **kwargs):
        self.calls.append((args, kwargs))


class FakeClient:
    def __init__(self, uri, serverSelectionTimeoutMS):
        self.db = FakeDatabase()

    def __getitem__(self, name):
        return self.db


def test_financial_db_reads_raw_data_and_upserts_report(monkeypatch):
    monkeypatch.setattr(database_service, "MongoClient", FakeClient)
    service = database_service.DatabaseService(uri="mongodb://test", db_name="test")

    assert service.get_client_audit("client-1") == {"client_id": "client-1"}
    assert service.save_evaluation_report("client-1", {"dscr": 1.5}) is True
    read_args, read_kwargs = service.raw_collection.calls[0]
    save_args, save_kwargs = service.eval_collection.calls[0]
    assert read_args[1] == {"_id": 0}
    assert save_args[0] == {"client_id": "client-1"}
    assert save_kwargs["upsert"] is True