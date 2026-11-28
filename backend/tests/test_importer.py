"""
Tests for the import logic (link checks, results, limits).
"""

import pytest

from app import importer
from app.importer import ImportRejected, prepare_import, run_import
from app.metadata import VideoRejected
from app.supabase_store import StoreError

from conftest import A, B, C, D, FakeStore, url


@pytest.fixture(autouse=True)
def fake_metadata(monkeypatch):
    """Replace yt-dlp: every video 'exists' unless it is listed as bad."""
    bad = {}

    def fetch(watch_url):
        video_id = watch_url.rsplit("=", 1)[1]
        if video_id in bad:
            raise bad[video_id]
        return {"video_id": video_id, "title": f"Song {video_id[:1]}", "duration_seconds": 200}

    monkeypatch.setattr(importer, "fetch_metadata", fetch)
    return bad


def start_and_run(store, urls, owner="user-1"):
    batch_id, entries = prepare_import(store, owner, urls)
    run_import(store, batch_id, entries)
    return batch_id


# ---- prepare_import (before anything runs) ----------------------------------

def test_blank_lines_are_ignored_and_numbering_follows_the_links():
    store = FakeStore()
    batch_id, entries = prepare_import(store, "u", ["", url(A), "  ", url(B)])
    assert [e.line_no for e in entries] == [1, 2]
    assert store.batches[batch_id]["total_links"] == 2


def test_nothing_to_import_is_rejected():
    with pytest.raises(ImportRejected) as error:
        prepare_import(FakeStore(), "u", ["", "   "])
    assert error.value.status_code == 422


def test_more_than_ten_links_is_rejected():
    links = [url(f"{i:011d}") for i in range(11)]
    with pytest.raises(ImportRejected) as error:
        prepare_import(FakeStore(), "u", links)
    assert error.value.status_code == 422
    assert "10" in error.value.message


def test_second_import_while_one_is_running_is_rejected():
    with pytest.raises(ImportRejected) as error:
        prepare_import(FakeStore(active=True), "u", [url(A)])
    assert error.value.status_code == 409


def test_daily_quota_message_comes_from_the_database():
    with pytest.raises(ImportRejected) as error:
        prepare_import(FakeStore(recent=9, daily_limit=10), "u", [url(A), url(B)])
    assert error.value.status_code == 429
    assert "1 more" in error.value.message


def test_quota_allows_exactly_the_limit():
    prepare_import(FakeStore(recent=8, daily_limit=10), "u", [url(A), url(B)])  # 8 + 2 == 10


def test_database_outage_is_not_shown_as_a_rejection():
    class Down(FakeStore):
        def start_import(self, user, items):
            raise StoreError("Could not reach Supabase: down")

    with pytest.raises(StoreError):
        prepare_import(Down(), "u", [url(A)])


def test_invalid_links_and_duplicates_are_decided_up_front():
    store = FakeStore(library={C})
    batch_id, entries = prepare_import(
        store, "u", [url(A), "https://google.com", url(A), url(C)]
    )
    assert [e.status for e in entries] == ["pending", "invalid", "duplicate", "duplicate"]
    assert "not a YouTube link" in entries[1].error
    assert entries[3].error == "Already in your library."
    # Settled links already carry a processed_at; the pending one does not.
    assert store.items[(batch_id, 1)]["processed_at"] is None
    assert store.items[(batch_id, 2)]["processed_at"] is not None


def test_batch_with_no_work_left_is_closed_immediately():
    store = FakeStore(library={A})
    batch_id, _ = prepare_import(store, "u", [url(A)])
    assert store.batches[batch_id]["status"] == "completed"


def test_batch_with_work_starts_processing():
    store = FakeStore()
    batch_id, _ = prepare_import(store, "u", [url(A)])
    assert store.batches[batch_id]["status"] == "processing"


# ---- run_import -------------------------------------------------------------

def test_all_links_imported():
    store = FakeStore()
    batch_id = start_and_run(store, [url(A), url(B)])
    assert store.statuses(batch_id) == ["success", "success"]
    assert store.batches[batch_id]["status"] == "completed"
    assert [song["title"] for _, song in store.songs] == ["Song a", "Song b"]
    assert store.items[(batch_id, 1)]["song_id"] == "song-1"


def test_songs_are_saved_with_the_canonical_url_for_the_right_owner():
    store = FakeStore()
    start_and_run(store, ["youtu.be/" + A], owner="user-42")
    owner, song = store.songs[0]
    assert owner == "user-42"
    assert song["source_url"] == url(A)
    assert song["duration_seconds"] == 200


def test_one_bad_video_does_not_cancel_the_others(fake_metadata):
    fake_metadata[B] = VideoRejected("The video is private.")
    store = FakeStore()
    batch_id = start_and_run(store, [url(A), url(B), url(C)])
    assert store.statuses(batch_id) == ["success", "failed", "success"]
    assert store.items[(batch_id, 2)]["error_message"] == "The video is private."
    assert store.batches[batch_id]["status"] == "partial"


def test_unexpected_error_is_reported_without_leaking_details(fake_metadata):
    fake_metadata[A] = RuntimeError("secret internal detail /etc/passwd")
    store = FakeStore()
    batch_id = start_and_run(store, [url(A)])
    message = store.items[(batch_id, 1)]["error_message"]
    assert "secret" not in message
    assert store.batches[batch_id]["status"] == "failed"


def test_all_failed_marks_the_batch_failed(fake_metadata):
    fake_metadata[A] = VideoRejected("The video is private.")
    store = FakeStore()
    batch_id = start_and_run(store, ["https://google.com", url(A)])
    assert store.batches[batch_id]["status"] == "failed"


def test_only_duplicates_counts_as_completed():
    store = FakeStore(library={A})
    batch_id = start_and_run(store, [url(A), url(A)])
    assert store.batches[batch_id]["status"] == "completed"
    assert store.songs == []


def test_song_added_by_a_parallel_request_becomes_a_duplicate(monkeypatch):
    store = FakeStore()
    batch_id, entries = prepare_import(store, "u", [url(A)])
    store.library.add(A)  # appears after planning, before saving
    run_import(store, batch_id, entries)
    assert store.statuses(batch_id) == ["duplicate"]


def test_supabase_failing_midway_still_closes_the_batch():
    store = FakeStore()
    batch_id, entries = prepare_import(store, "u", [url(A), url(B)])
    store.fail_after_records = 1  # the first link is saved, then Supabase goes down
    run_import(store, batch_id, entries)

    # The batch is never left "processing". The first song was really saved
    # before the outage, so the batch is partial; the second never ran.
    assert store.batches[batch_id]["status"] == "partial"
    assert len(store.songs) == 1
    assert [e.status for e in entries] == ["success", "failed"]
    assert store.keys == {}  # the job key is retired


def test_job_key_is_retired_when_the_import_ends():
    store = FakeStore()
    batch_id = start_and_run(store, [url(A)])
    assert store.keys == {}
    with pytest.raises(StoreError):
        store.record_import_item(batch_id, 1, "success", title="again")

# ---- Shorts are imported like any other video ---------------------------------

def test_shorts_links_are_imported(fake_metadata):
    store = FakeStore()
    batch_id = start_and_run(store, [f"https://youtube.com/shorts/{A}", url(B)])

    assert store.statuses(batch_id) == ["success", "success"]
    assert {track["video_id"] for _, track in store.songs} == {A, B}
