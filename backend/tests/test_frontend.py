"""The installed app: the backend serves the built frontend from one address."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.frontend import mount_frontend


@pytest.fixture
def dist(tmp_path):
    folder = tmp_path / "dist"
    (folder / "assets").mkdir(parents=True)
    (folder / "index.html").write_text("<!doctype html><title>YT-MP3</title>")
    (folder / "assets" / "index-abc123.js").write_text("console.log('app')")
    (folder / "ytmp3-icon.svg").write_text("<svg/>")
    # A secret next to dist: nothing must ever serve it.
    (tmp_path / "secret.env").write_text("SUPABASE_SECRET_KEY=sb_secret_do_not_serve")
    return folder


@pytest.fixture
def client(dist):
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/imports")
    def imports():
        return {"started": True}

    mount_frontend(app, dist)
    return TestClient(app)


def test_api_routes_still_win(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.post("/imports").json() == {"started": True}


@pytest.mark.parametrize("path", ["/", "/app/library", "/app/playlists/123", "/no/such/page"])
def test_app_pages_get_index_html(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert "<title>YT-MP3</title>" in response.text
    assert response.headers["cache-control"] == "no-cache"


def test_built_files_are_served(client):
    assert client.get("/assets/index-abc123.js").text == "console.log('app')"
    assert client.get("/ytmp3-icon.svg").text == "<svg/>"


def test_missing_asset_is_404_not_the_page(client):
    assert client.get("/assets/missing.js").status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        "/../secret.env",
        "/%2e%2e/secret.env",
        "/assets/../../secret.env",
        "/assets/%2e%2e/%2e%2e/secret.env",
        "/..%2fsecret.env",
        "/secret.env",
    ],
)
def test_nothing_outside_dist_is_served(client, path):
    response = client.get(path)
    assert "sb_secret_do_not_serve" not in response.text


def test_missing_build_is_a_clear_error(tmp_path):
    with pytest.raises(RuntimeError, match="npm run build"):
        mount_frontend(FastAPI(), tmp_path / "dist")
