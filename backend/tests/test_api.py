"""
Tests for the import API endpoints.
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from app import auth, config, importer
from app.main import app, get_store

from conftest import A, B, FakeStore, url


@pytest.fixture
def client(monkeypatch):
    store = FakeStore()
    monkeypatch.setattr(
        importer,
        "fetch_metadata",
        lambda u: {"video_id": u[-11:], "title": "A song", "duration_seconds": 120},
    )
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[auth.get_current_user_id] = lambda: "user-1"
    test_client = TestClient(app)
    test_client.store = store
    yield test_client
    app.dependency_overrides.clear()


def test_import_starts_and_finishes(client):
    response = client.post("/imports", json={"urls": [url(A), url(B)]})
    assert response.status_code == 202
    body = response.json()
    assert body["total_links"] == 2

    # TestClient runs background tasks before returning.
    batch = client.store.batches[body["batch_id"]]
    assert batch["status"] == "completed"
    assert batch["owner_id"] == "user-1"
    assert len(client.store.songs) == 2


def test_owner_comes_from_the_token_not_from_the_body(client):
    client.post("/imports", json={"urls": [url(A)], "owner_id": "someone-else"})
    assert client.store.songs[0][0] == "user-1"


def test_rejections_use_one_error_shape(client):
    response = client.post("/imports", json={"urls": ["", " "]})
    assert response.status_code == 422
    assert response.json()["detail"]["message"] == "Enter at least one YouTube link."


def test_running_import_returns_409(client):
    client.store.active = True
    response = client.post("/imports", json={"urls": [url(A)]})
    assert response.status_code == 409


# ---- authentication (no dependency override) ---------------------------------

@pytest.fixture
def real_auth_client(monkeypatch):
    monkeypatch.setattr(config, "SUPABASE_URL", "https://proj.supabase.co")
    monkeypatch.setattr(config, "SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test")
    app.dependency_overrides[get_store] = lambda: FakeStore()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_missing_token_is_401(real_auth_client):
    response = real_auth_client.post("/imports", json={"urls": [url(A)]})
    assert response.status_code == 401


def test_token_is_checked_with_supabase_auth(real_auth_client, monkeypatch):
    captured = {}

    def fake_get(address, headers, timeout):
        captured["address"] = address
        captured["headers"] = headers
        return httpx.Response(200, json={"id": "user-from-supabase"})

    monkeypatch.setattr(auth.httpx, "get", fake_get)
    monkeypatch.setattr(
        importer, "fetch_metadata",
        lambda u: {"video_id": "x", "title": "T", "duration_seconds": 1},
    )

    response = real_auth_client.post(
        "/imports", json={"urls": [url(A)]}, headers={"Authorization": "Bearer abc.def"}
    )
    assert response.status_code == 202
    assert captured["address"] == "https://proj.supabase.co/auth/v1/user"
    assert captured["headers"]["apikey"] == "sb_publishable_test"
    assert captured["headers"]["Authorization"] == "Bearer abc.def"


def test_rejected_token_is_401(real_auth_client, monkeypatch):
    monkeypatch.setattr(
        auth.httpx, "get", lambda *a, **k: httpx.Response(401, json={"msg": "bad"})
    )
    response = real_auth_client.post(
        "/imports", json={"urls": [url(A)]}, headers={"Authorization": "Bearer nope"}
    )
    assert response.status_code == 401


def test_supabase_unreachable_is_503_not_a_crash(real_auth_client, monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(auth.httpx, "get", boom)
    response = real_auth_client.post(
        "/imports", json={"urls": [url(A)]}, headers={"Authorization": "Bearer x"}
    )
    assert response.status_code == 503


def test_cors_allows_the_authorization_header(real_auth_client):
    response = real_auth_client.options(
        "/imports",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert "authorization" in response.headers["access-control-allow-headers"].lower()