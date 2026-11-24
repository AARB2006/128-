"""
Tests for the Supabase store's HTTP requests (mocked).
"""

import json
from datetime import datetime, timezone

import httpx
import pytest

from app.supabase_store import StoreError, SupabaseStore


def make_store(handler):
    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        headers={"apikey": "sb_secret_test"},
    )
    return SupabaseStore("https://proj.supabase.co", "sb_secret_test", client=client)


def test_secret_key_is_sent_on_apikey_only():
    seen = {}

    def handler(request):
        seen["headers"] = request.headers
        return httpx.Response(200, json=[])

    make_store(handler).has_active_batch("owner-1")
    assert seen["headers"]["apikey"] == "sb_secret_test"
    assert "authorization" not in seen["headers"]


def test_existing_video_ids_query():
    def handler(request):
        assert request.url.path == "/rest/v1/songs"
        assert request.url.params["owner_id"] == "eq.owner-1"
        assert request.url.params["video_id"] == "in.(aaaaaaaaaaa,bbbbbbbbbbb)"
        return httpx.Response(200, json=[{"video_id": "aaaaaaaaaaa"}])

    store = make_store(handler)
    assert store.existing_video_ids("owner-1", ["aaaaaaaaaaa", "bbbbbbbbbbb"]) == {"aaaaaaaaaaa"}


def test_existing_video_ids_skips_the_request_when_empty():
    def handler(request):
        raise AssertionError("no request expected")

    assert make_store(handler).existing_video_ids("o", []) == set()


def test_recent_link_count_sums_batches():
    def handler(request):
        assert request.url.params["created_at"].startswith("gte.2026-")
        return httpx.Response(200, json=[{"total_links": 4}, {"total_links": 6}])

    since = datetime(2026, 11, 16, tzinfo=timezone.utc)
    assert make_store(handler).recent_link_count("o", since) == 10


def test_insert_song_ignores_duplicates_by_owner_and_video():
    captured = {}

    def handler(request):
        captured["params"] = dict(request.url.params)
        captured["prefer"] = request.headers["prefer"]
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json=[{"song_id": "song-1"}])

    track = {"video_id": "aaaaaaaaaaa", "source_url": "u", "title": "T", "duration_seconds": 1}
    assert make_store(handler).insert_song("owner-1", track) == "song-1"
    assert captured["params"]["on_conflict"] == "owner_id,video_id"
    assert "ignore-duplicates" in captured["prefer"]
    assert captured["body"]["owner_id"] == "owner-1"


def test_insert_song_returns_none_when_it_already_exists():
    store = make_store(lambda request: httpx.Response(201, json=[]))
    track = {"video_id": "aaaaaaaaaaa", "source_url": "u", "title": "T", "duration_seconds": 1}
    assert store.insert_song("owner-1", track) is None


def test_update_item_targets_one_link():
    captured = {}

    def handler(request):
        captured["method"] = request.method
        captured["params"] = dict(request.url.params)
        captured["body"] = json.loads(request.content)
        return httpx.Response(204)

    make_store(handler).update_item("b1", 3, status="success", song_id="s1")
    assert captured["method"] == "PATCH"
    assert captured["params"] == {"batch_id": "eq.b1", "line_no": "eq.3"}
    assert captured["body"]["status"] == "success"
    assert "processed_at" in captured["body"]


def test_create_batch_closed_immediately_gets_a_completed_at():
    def handler(request):
        body = json.loads(request.content)
        assert body["completed_at"] is not None
        return httpx.Response(201, json=[{"batch_id": "b1"}])

    assert make_store(handler).create_batch("o", 2, "completed") == "b1"


def test_errors_become_store_errors_without_leaking_the_body():
    store = make_store(lambda request: httpx.Response(401, text="invalid key sb_secret_x"))
    with pytest.raises(StoreError) as error:
        store.has_active_batch("o")
    assert "sb_secret" not in str(error.value)


def test_network_failure_becomes_a_store_error():
    def handler(request):
        raise httpx.ConnectError("boom")

    with pytest.raises(StoreError):
        make_store(handler).has_active_batch("o")


def test_fail_interrupted_batches_closes_batches_and_pending_items():
    calls = []

    def handler(request):
        calls.append((request.method, request.url.path, dict(request.url.params)))
        if request.method == "GET":
            return httpx.Response(200, json=[{"batch_id": "b1"}, {"batch_id": "b2"}])
        return httpx.Response(204)

    assert make_store(handler).fail_interrupted_batches() == 2
    patches = [c for c in calls if c[0] == "PATCH"]
    assert patches[0][1].endswith("import_items")
    assert patches[0][2]["status"] == "eq.pending"
    assert patches[1][1].endswith("import_batches")
    assert patches[1][2]["batch_id"] == "in.(b1,b2)"


def test_fail_interrupted_batches_does_nothing_when_none_are_stuck():
    calls = []

    def handler(request):
        calls.append(request.method)
        return httpx.Response(200, json=[])

    assert make_store(handler).fail_interrupted_batches() == 0
    assert calls == ["GET"]