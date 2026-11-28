"""
Tests for the Supabase store's HTTP requests (mocked) and the job-key file.
"""

import json

import httpx
import pytest

from app.auth import SignedInUser
from app.jobs import JobKeys
from app.supabase_store import StoreError, SupabaseStore


USER = SignedInUser("user-1", "user.login.token")


def make_store(handler, jobs=None):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return SupabaseStore("https://proj.supabase.co", "sb_publishable_test", jobs=jobs, client=client)


def recorder(responses):
    """A handler that records requests and answers from a {path: json} map."""
    seen = []

    def handler(request):
        seen.append(request)
        body = responses.get(request.url.path, [])
        return httpx.Response(200, json=body)

    handler.seen = seen
    return handler


# ---- credentials ------------------------------------------------------------------

def test_user_calls_send_the_publishable_key_and_the_login_token():
    handler = recorder({"/rest/v1/playlist_songs": [{"song_id": "s1"}, {"song_id": "s2"}]})
    assert make_store(handler).playlist_song_count(USER, "p-1") == 2
    headers = handler.seen[0].headers
    assert headers["apikey"] == "sb_publishable_test"
    assert headers["authorization"] == "Bearer user.login.token"


def test_job_calls_send_no_login_token():
    jobs = JobKeys()
    jobs.remember("export", "e-1", "the-job-key")
    handler = recorder({})
    make_store(handler, jobs).update_export("e-1", percent=40)

    request = handler.seen[0]
    assert request.headers["apikey"] == "sb_publishable_test"
    assert "authorization" not in request.headers
    assert request.url.path == "/rest/v1/rpc/update_export_job"
    assert json.loads(request.content) == {
        "p_export_id": "e-1", "p_job_key": "the-job-key", "p_fields": {"percent": 40}}


def test_no_secret_key_anywhere():
    import app.config as config
    assert not hasattr(config, "SUPABASE_SECRET_KEY")


# ---- imports ----------------------------------------------------------------------

def test_start_import_remembers_the_job_key():
    jobs = JobKeys()
    result = {"batch_id": "b-1", "job_key": "k", "status": "processing", "items": []}
    handler = recorder({"/rest/v1/rpc/start_import": result})
    items = [{"line_no": 1, "submitted_url": "u", "video_id": "aaaaaaaaaaa",
              "status": "pending", "error_message": None}]

    assert make_store(handler, jobs).start_import(USER, items) == result
    assert json.loads(handler.seen[0].content) == {"p_items": items}
    assert jobs.key_for("b-1") == "k"


def test_start_import_without_work_has_no_key():
    jobs = JobKeys()
    handler = recorder({"/rest/v1/rpc/start_import": {"batch_id": "b-1", "job_key": None, "items": []}})
    make_store(handler, jobs).start_import(USER, [])
    assert jobs.key_for("b-1") is None


def test_record_and_finish_import():
    jobs = JobKeys()
    jobs.remember("import", "b-1", "k")
    handler = recorder({"/rest/v1/rpc/record_import_item": "duplicate",
                        "/rest/v1/rpc/finish_import": "completed"})
    store = make_store(handler, jobs)

    assert store.record_import_item("b-1", 2, "success", title="T", duration_seconds=9) == "duplicate"
    assert json.loads(handler.seen[0].content) == {
        "p_batch_id": "b-1", "p_job_key": "k", "p_line_no": 2, "p_status": "success",
        "p_error_message": None, "p_title": "T", "p_duration_seconds": 9}

    assert store.finish_import("b-1") == "completed"
    assert jobs.key_for("b-1") is None  # retired


def test_unknown_job_has_no_key_and_sends_nothing():
    def handler(request):
        raise AssertionError("no request expected")

    with pytest.raises(StoreError) as error:
        make_store(handler).record_import_item("b-9", 1, "failed", error_message="x")
    assert error.value.status_code == 403


# ---- exports ----------------------------------------------------------------------

def test_start_export_and_finishing_retires_the_key():
    jobs = JobKeys()
    result = {"export_id": "e-1", "job_key": "k", "playlist_name": "P", "tracks": []}
    handler = recorder({"/rest/v1/rpc/start_export": result})
    store = make_store(handler, jobs)

    assert store.start_export(USER, "p-1") == result
    assert json.loads(handler.seen[0].content) == {"p_playlist_id": "p-1"}
    assert jobs.key_for("e-1") == "k"

    store.update_export("e-1", status="processing")
    assert jobs.key_for("e-1") == "k"
    store.update_export("e-1", status="completed", percent=100)
    assert jobs.key_for("e-1") is None


def test_export_item_calls():
    jobs = JobKeys()
    jobs.remember("export", "e-1", "k")
    handler = recorder({})
    store = make_store(handler, jobs)
    store.update_export_item("e-1", 3, status="failed", error_message="Gone.")
    store.skip_pending_export_items("e-1", "Cancelled.")
    assert [r.url.path for r in handler.seen] == [
        "/rest/v1/rpc/update_export_item_job", "/rest/v1/rpc/skip_pending_export_items_job"]
    assert json.loads(handler.seen[0].content)["p_position"] == 3
    assert json.loads(handler.seen[1].content)["p_reason"] == "Cancelled."


def test_deleting_exports_is_done_as_the_user_and_only_finished_ones():
    handler = recorder({"/rest/v1/exports": [{"export_id": "e-1"}]})
    store = make_store(handler)
    assert store.delete_export(USER, "e-1") is True
    assert store.delete_finished_exports(USER) == ["e-1"]
    for request in handler.seen:
        assert request.method == "DELETE"
        assert request.headers["authorization"] == "Bearer user.login.token"
        assert request.url.params["owner_id"] == "eq.user-1"
        assert request.url.params["status"] == "not.in.(pending,processing,packaging)"


# ---- errors -----------------------------------------------------------------------

def test_database_messages_reach_the_user():
    def handler(request):
        return httpx.Response(409, json={"code": "PT409", "message": "An import is already running."})

    with pytest.raises(StoreError) as error:
        make_store(handler).start_import(USER, [])
    assert error.value.status_code == 409
    assert str(error.value) == "An import is already running."


def test_unexpected_errors_get_a_plain_message():
    def handler(request):
        return httpx.Response(500, text="<html>stack trace</html>")

    with pytest.raises(StoreError) as error:
        make_store(handler).playlist_song_count(USER, "p")
    assert "stack trace" not in str(error.value)
    assert error.value.status_code == 500


def test_network_failure_becomes_a_store_error():
    def handler(request):
        raise httpx.ConnectError("down")

    with pytest.raises(StoreError) as error:
        make_store(handler).playlist_song_count(USER, "p")
    assert error.value.status_code is None


# ---- jobs left from the last run --------------------------------------------------

def test_job_keys_survive_a_restart_and_are_then_interrupted(tmp_path):
    path = tmp_path / ".jobs.json"
    before = JobKeys(path)
    before.remember("export", "e-1", "k1")
    before.remember("import", "b-1", "k2")
    assert path.is_file()

    after = JobKeys(path)  # the backend starts again
    handler = recorder({})
    assert make_store(handler, after).recover_interrupted_jobs() == 2
    sent = sorted((json.loads(r.content)["p_kind"], json.loads(r.content)["p_job_key"]) for r in handler.seen)
    assert sent == [("export", "k1"), ("import", "k2")]
    assert {r.url.path for r in handler.seen} == {"/rest/v1/rpc/interrupt_job"}
    assert not path.exists()  # nothing left to remember


def test_jobs_already_closed_are_forgotten_and_offline_ones_kept(tmp_path):
    path = tmp_path / ".jobs.json"
    JobKeys(path).remember("export", "e-1", "k1")

    def offline(request):
        raise httpx.ConnectError("down")

    keys = JobKeys(path)
    assert make_store(offline, keys).recover_interrupted_jobs() == 0
    assert keys.key_for("e-1") == "k1"  # try again next time

    def closed(request):
        return httpx.Response(403, json={"message": "This job can no longer be updated."})

    keys = JobKeys(path)
    make_store(closed, keys).recover_interrupted_jobs()
    assert keys.key_for("e-1") is None
    assert not path.exists()


def test_an_unreadable_job_file_is_ignored(tmp_path):
    path = tmp_path / ".jobs.json"
    path.write_text("not json")
    assert JobKeys(path).left_from_last_run() == []
