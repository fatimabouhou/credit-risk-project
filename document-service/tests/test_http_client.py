import asyncio

import httpx

from app.infrastructure import http_client


class FakeAsyncClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def post(self, endpoint, timeout):
        self.calls.append((endpoint, timeout))
        return self.response


def test_notify_financial_service_sends_expected_request(monkeypatch):
    fake = FakeAsyncClient(httpx.Response(200, request=httpx.Request("POST", "http://test")))
    monkeypatch.setattr(http_client.httpx, "AsyncClient", lambda: fake)
    monkeypatch.setattr(http_client, "FINANCIAL_SERVICE_URL", "http://financial.test")

    assert asyncio.run(http_client.notify_financial_service("client-1")) is True
    assert fake.calls == [("http://financial.test/api/v1/financial/evaluate/client-1", 15.0)]


def test_notify_financial_service_returns_false_on_http_error(monkeypatch):
    fake = FakeAsyncClient(httpx.Response(503, request=httpx.Request("POST", "http://test")))
    monkeypatch.setattr(http_client.httpx, "AsyncClient", lambda: fake)

    assert asyncio.run(http_client.notify_financial_service("client-1")) is False