from app.infrastructure import db_service


class FakeAdmin:
    def command(self, name):
        assert name == "ping"


class FakeCollection:
    def __init__(self):
        self.calls = []

    def update_one(self, *args, **kwargs):
        self.calls.append((args, kwargs))

    def find_one(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"client_id": "client-1"}


class FakeDatabase:
    def __init__(self):
        self.collection = FakeCollection()

    def __getitem__(self, name):
        return self.collection


class FakeClient:
    def __init__(self, uri, serverSelectionTimeoutMS):
        self.admin = FakeAdmin()
        self.database = FakeDatabase()

    def __getitem__(self, name):
        return self.database


def test_document_db_upserts_audit_and_excludes_mongo_id(monkeypatch):
    monkeypatch.setattr(db_service, "MongoClient", FakeClient)
    service = db_service.DatabaseService(uri="mongodb://test", db_name="test")

    assert service.save_client_audit({"client_id": "client-1", "score": 2}) == "client-1"
    assert service.get_client_audit("client-1") == {"client_id": "client-1"}
    save_args, save_kwargs = service.collection.calls[0]
    read_args, read_kwargs = service.collection.calls[1]
    assert save_args[0] == {"client_id": "client-1"}
    assert save_kwargs["upsert"] is True
    assert read_args[0] == {"client_id": "client-1"}
    assert read_args[1] == {"_id": 0}
