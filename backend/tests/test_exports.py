import errno
import os
import uuid
import zipfile
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import auth, config
from app.exports import audio, packager, service, workspace
from app.exports.service import ExportRejected, prepare_export, run_export
from app.main import app, get_store
from app.supabase_store import StoreError


PLAYLIST = "11111111-1111-1111-1111-111111111111"


class FakeExportStore:
    """In-memory stand-in for the export half of SupabaseStore."""

    def __init__(self, titles=("First", "Second", "Third"), owner="user-1"):
        self.owner = owner
        self.playlist = {"playlist_id": PLAYLIST, "name": "goku vs saitama"}
        self.tracks = [
            {
                "position": i,
                "song_id": f"song-{i}",
                "video_id": f"{i:011d}",
                "title": title,
            }
            for i, title in enumerate(titles, start=1)
        ]
        self.recent = 0
        self.playlist_deleted = False
        self.exports = {}
        self.items = {}  # (export_id, position) -> dict
        self.updates = []  # every update_export call, in order

    def get_owned_playlist(self, owner_id, playlist_id):
        if owner_id == self.owner and playlist_id == PLAYLIST:
            return dict(self.playlist)
        return None

    def get_playlist_tracks(self, owner_id, playlist_id):
        return [dict(t) for t in self.tracks]

    def recent_export_song_count(self, owner_id, since):
        return self.recent

    def create_export(self, owner_id, playlist, total_songs):
        if any(e["status"] in service.ACTIVE for e in self.exports.values()):
            raise StoreError("duplicate", status_code=409)
        export_id = str(uuid.uuid4())
        self.exports[export_id] = {
            "export_id": export_id,
            "owner_id": owner_id,
            "playlist_id": playlist["playlist_id"],
            "total_songs": total_songs,
            "status": "pending",
            "file_expires_at": None,
        }
        return export_id

    def create_export_items(self, export_id, tracks):
        for t in tracks:
            # Only references are stored, never titles or video ids.
            self.items[(export_id, t["position"])] = {
                "position": t["position"],
                "song_id": t["song_id"],
                "status": "pending",
            }

    def get_export(self, owner_id, export_id):
        row = self.exports.get(export_id)
        if not row or row["owner_id"] != owner_id:
            return None
        # Like the real query: the playlist's current name, or None if deleted.
        playlist = self.playlist if row["playlist_id"] == PLAYLIST and not self.playlist_deleted else None
        return {**row, "playlist": {"name": playlist["name"]} if playlist else None}

    def update_export(self, export_id, **fields):
        self.updates.append(fields)
        self.exports[export_id].update(fields)

    def update_export_item(self, export_id, position, **fields):
        self.items[(export_id, position)].update(fields)

    def skip_pending_export_items(self, export_id, reason):
        for (eid, _), item in self.items.items():
            if eid == export_id and item["status"] == "pending":
                item.update(status="skipped", error_message=reason)

    def delete_export(self, owner_id, export_id):
        row = self.exports.get(export_id)
        if not row or row["owner_id"] != owner_id or row["status"] in service.ACTIVE:
            return False
        del self.exports[export_id]
        self.items = {k: v for k, v in self.items.items() if k[0] != export_id}
        return True

    def delete_finished_exports(self, owner_id):
        ids = [
            eid for eid, row in self.exports.items()
            if row["owner_id"] == owner_id and row["status"] not in service.ACTIVE
        ]
        for eid in ids:
            self.delete_export(owner_id, eid)
        return ids

    def item_statuses(self, export_id):
        return [self.items[k]["status"] for k in sorted(k for k in self.items if k[0] == export_id)]


@pytest.fixture(autouse=True)
def environment(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "EXPORT_DIR", tmp_path / "exports")
    monkeypatch.setattr(service, "ffmpeg_available", lambda: True)
    monkeypatch.setattr(workspace, "free_mb", lambda: 10**6)
    monkeypatch.setattr(service, "PROGRESS_WRITE_SECONDS", 0)


@pytest.fixture
def downloads(monkeypatch):
    """Fake AudioProcessor: video_id -> exception to raise, otherwise succeed."""
    failures = {}
    calls = []

    def fake(video_id, work_dir, stem, on_progress=lambda f: None, should_cancel=lambda: False):
        calls.append(video_id)
        on_progress(0.5)
        if should_cancel():
            raise audio.Cancelled()
        if video_id in failures:
            raise failures[video_id]
        path = work_dir / f"{stem}.mp3"
        path.write_bytes(b"ID3 fake mp3 " + video_id.encode())
        on_progress(1.0)
        return path

    monkeypatch.setattr(audio, "download_mp3", fake)
    fake.failures = failures
    fake.calls = calls
    return fake


def start_and_run(store, owner="user-1"):
    job = prepare_export(store, owner, PLAYLIST)
    run_export(store, job)
    return job.export_id


def zip_names(export_id):
    with zipfile.ZipFile(workspace.ready_path(export_id)) as archive:
        return archive.namelist()


# ---- the normal flow -----------------------------------------------------------

def test_all_songs_exported_in_saved_order(downloads):
    store = FakeExportStore()
    export_id = start_and_run(store)

    row = store.exports[export_id]
    assert row["status"] == "completed"
    assert row["percent"] == 100
    assert row["exported_songs"] == 3
    assert zip_names(export_id) == ["01 - First.mp3", "02 - Second.mp3", "03 - Third.mp3"]
    assert store.item_statuses(export_id) == ["success"] * 3
    assert not workspace.work_dir(export_id).exists()  # cleanup guarantee


def test_progress_only_goes_up_and_ends_at_100(downloads):
    store = FakeExportStore()
    start_and_run(store)

    percents = [u["percent"] for u in store.updates if "percent" in u]
    assert percents == sorted(percents)
    assert percents[-1] == 100
    assert any(0 < p < 95 for p in percents)


def test_progress_writes_are_throttled(monkeypatch):
    store = FakeExportStore()
    store.exports["e"] = {"status": "processing"}
    clock = iter([0.0, 0.2, 0.4, 1.5])
    progress = service.Progress(store, "e", total=1, clock=lambda: next(clock))
    progress.written_at = -10

    monkeypatch.setattr(service, "PROGRESS_WRITE_SECONDS", 1.0)
    for fraction in (0.1, 0.2, 0.3, 0.4):
        progress.song(0, fraction)

    assert [u["percent"] for u in store.updates] == [9, 38]


def test_history_stores_references_not_copies(downloads):
    store = FakeExportStore()
    export_id = start_and_run(store)

    assert "playlist_name" not in store.exports[export_id]
    for item in (i for (eid, _), i in store.items.items() if eid == export_id):
        assert set(item) <= {"position", "song_id", "status", "error_message"}


def test_the_playlist_and_library_are_not_changed(downloads):
    store = FakeExportStore()
    before = [dict(t) for t in store.tracks]
    start_and_run(store)
    assert store.tracks == before


def test_same_playlist_can_be_exported_again(downloads):
    store = FakeExportStore()
    first = start_and_run(store)
    second = start_and_run(store)
    assert first != second
    assert store.exports[second]["status"] == "completed"


def test_unsafe_titles_become_safe_file_names(downloads):
    store = FakeExportStore(titles=('AC/DC: "Back" <In> Black?', "CON", "   "))
    export_id = start_and_run(store)
    assert zip_names(export_id) == [
        "01 - ACDC Back In Black.mp3",
        "02 - _CON.mp3",
        "03 - track_3.mp3",
    ]


# ---- E1: songs that can't be exported ---------------------------------------------

def test_a_failed_song_is_skipped_and_reported(downloads):
    store = FakeExportStore()
    downloads.failures["00000000002"] = Exception("ERROR: Private video")
    export_id = start_and_run(store)

    row = store.exports[export_id]
    assert row["status"] == "partial"
    assert row["exported_songs"] == 2
    assert zip_names(export_id) == ["01 - First.mp3", "03 - Third.mp3"]

    item = store.items[(export_id, 2)]
    assert item["status"] == "failed"
    assert item["error_message"] == "The video is private."


def test_unknown_errors_get_a_plain_reason(downloads):
    store = FakeExportStore()
    downloads.failures["00000000001"] = Exception("something odd")
    export_id = start_and_run(store)
    assert store.items[(export_id, 1)]["error_message"] == service.GENERIC_SONG_REASON


def test_no_file_when_every_song_fails(downloads):
    store = FakeExportStore()
    for t in store.tracks:
        downloads.failures[t["video_id"]] = Exception("Video unavailable")
    export_id = start_and_run(store)

    row = store.exports[export_id]
    assert row["status"] == "failed"
    assert row["error_message"] == "None of the songs could be exported."
    assert not workspace.ready_path(export_id).exists()


def test_stops_early_when_youtube_keeps_blocking(downloads):
    store = FakeExportStore(titles=("a", "b", "c", "d", "e"))
    for t in store.tracks:
        downloads.failures[t["video_id"]] = Exception("Sign in to confirm you're not a bot")
    export_id = start_and_run(store)

    assert len(downloads.calls) == 3  # gave up instead of trying all 5
    assert store.exports[export_id]["status"] == "failed"
    assert store.exports[export_id]["error_message"] == service.RATE_LIMITED_REASON
    assert store.item_statuses(export_id) == ["failed"] * 3 + ["skipped"] * 2


def test_unrelated_failures_do_not_trigger_the_early_stop(downloads):
    store = FakeExportStore(titles=("a", "b", "c", "d"))
    for t in store.tracks[:3]:
        downloads.failures[t["video_id"]] = Exception("Video unavailable")
    export_id = start_and_run(store)
    assert len(downloads.calls) == 4
    assert store.exports[export_id]["status"] == "partial"


# ---- E2 / E3: generation failures -------------------------------------------------------

def test_packaging_failure_leaves_no_file(downloads, monkeypatch):
    def broken(files, zip_path):
        zip_path.with_name(zip_path.name + ".part").write_bytes(b"half")
        raise packager.PackagingError("boom")

    monkeypatch.setattr(packager, "build_zip", broken)
    store = FakeExportStore()
    export_id = start_and_run(store)

    assert store.exports[export_id]["status"] == "failed"
    assert not workspace.ready_path(export_id).exists()
    assert not list((config.EXPORT_DIR / "ready").glob("*.part"))
    assert not workspace.work_dir(export_id).exists()


def test_real_packager_writes_a_checked_zip(tmp_path):
    files = []
    for name in ("01 - a.mp3", "02 - b.mp3"):
        path = tmp_path / name
        path.write_bytes(b"x" * 100)
        files.append(path)

    target = tmp_path / "out" / "x.zip"
    size = packager.build_zip(files, target)

    assert size == target.stat().st_size
    assert not target.with_name("x.zip.part").exists()
    with zipfile.ZipFile(target) as archive:
        assert archive.namelist() == ["01 - a.mp3", "02 - b.mp3"]


def test_disk_full_fails_the_export(downloads):
    store = FakeExportStore()
    downloads.failures["00000000002"] = OSError(errno.ENOSPC, "No space left on device")
    export_id = start_and_run(store)

    row = store.exports[export_id]
    assert row["status"] == "failed"
    assert "ran out of space" in row["error_message"]
    assert store.item_statuses(export_id) == ["success", "skipped", "skipped"]
    assert not workspace.ready_path(export_id).exists()
    assert not workspace.work_dir(export_id).exists()


def test_unexpected_error_is_reported_and_cleaned_up(downloads, monkeypatch):
    store = FakeExportStore()
    monkeypatch.setattr(service, "file_name_for", lambda *a: 1 / 0)
    export_id = start_and_run(store)
    assert store.exports[export_id]["status"] == "failed"
    assert not workspace.work_dir(export_id).exists()


# ---- cancelling ------------------------------------------------------------------------------

def test_cancel_while_running(downloads, monkeypatch):
    store = FakeExportStore()
    job = prepare_export(store, "user-1", PLAYLIST)

    original = audio.download_mp3

    def cancel_on_second(video_id, *args, **kwargs):
        if video_id == "00000000002":
            service.request_cancel(store, "user-1", job.export_id)
        return original(video_id, *args, **kwargs)

    monkeypatch.setattr(audio, "download_mp3", cancel_on_second)
    run_export(store, job)

    assert store.exports[job.export_id]["status"] == "cancelled"
    assert store.item_statuses(job.export_id) == ["success", "skipped", "skipped"]
    assert not workspace.ready_path(job.export_id).exists()
    assert not workspace.work_dir(job.export_id).exists()


def test_cancel_while_still_queued(downloads):
    store = FakeExportStore()
    job = prepare_export(store, "user-1", PLAYLIST)
    service.request_cancel(store, "user-1", job.export_id)
    run_export(store, job)

    assert downloads.calls == []
    assert store.exports[job.export_id]["status"] == "cancelled"
    assert store.item_statuses(job.export_id) == ["skipped"] * 3


def test_cannot_cancel_a_finished_export(downloads):
    store = FakeExportStore()
    export_id = start_and_run(store)
    with pytest.raises(ExportRejected) as error:
        service.request_cancel(store, "user-1", export_id)
    assert error.value.status_code == 409


# ---- checks before starting ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "setup, status",
    [
        (lambda s, m: setattr(s, "owner", "someone-else"), 404),
        (lambda s, m: setattr(s, "tracks", []), 409),
        (lambda s, m: m.setattr(config, "MAX_EXPORT_SONGS", 2), 422),
        (lambda s, m: setattr(s, "recent", 299), 429),
        (lambda s, m: m.setattr(service, "ffmpeg_available", lambda: False), 503),
        (lambda s, m: m.setattr(workspace, "free_mb", lambda: 100), 507),
    ],
    ids=["not-owner", "empty", "too-many-songs", "daily-limit", "no-ffmpeg", "low-disk"],
)
def test_start_is_refused(setup, status, monkeypatch):
    store = FakeExportStore()
    setup(store, monkeypatch)
    with pytest.raises(ExportRejected) as error:
        prepare_export(store, "user-1", PLAYLIST)
    assert error.value.status_code == status
    assert store.exports == {}


def test_only_one_running_export_per_user():
    store = FakeExportStore()
    prepare_export(store, "user-1", PLAYLIST)
    with pytest.raises(ExportRejected) as error:
        prepare_export(store, "user-1", PLAYLIST)
    assert error.value.status_code == 409


# ---- downloading -----------------------------------------------------------------------------------

def test_download_link_works_for_the_owner(downloads):
    store = FakeExportStore()
    export_id = start_and_run(store)
    store.exports[export_id]["file_expires_at"] = (
        datetime.now(timezone.utc) + timedelta(minutes=5)
    ).isoformat()

    path = service.create_download_link(store, "user-1", export_id)
    file_path, name = service.redeem_download_link(path.rsplit("/", 1)[1])
    assert file_path == workspace.ready_path(export_id)
    assert name == "goku vs saitama.zip"


def test_download_is_named_after_the_current_playlist_name(downloads):
    store = FakeExportStore()
    export_id = start_and_run(store)

    store.playlist["name"] = "renamed: mix?"
    token = service.create_download_link(store, "user-1", export_id).rsplit("/", 1)[1]
    assert service.redeem_download_link(token)[1] == "renamed mix.zip"

    store.playlist_deleted = True
    token = service.create_download_link(store, "user-1", export_id).rsplit("/", 1)[1]
    assert service.redeem_download_link(token)[1] == "playlist.zip"


def test_download_link_refusals(downloads):
    store = FakeExportStore()
    export_id = start_and_run(store)

    with pytest.raises(ExportRejected) as error:
        service.create_download_link(store, "someone-else", export_id)
    assert error.value.status_code == 404

    store.exports[export_id]["file_expires_at"] = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    ).isoformat()
    with pytest.raises(ExportRejected) as error:
        service.create_download_link(store, "user-1", export_id)
    assert error.value.status_code == 410

    store.exports[export_id]["status"] = "processing"
    with pytest.raises(ExportRejected) as error:
        service.create_download_link(store, "user-1", export_id)
    assert error.value.status_code == 409


def test_download_links_expire(downloads, monkeypatch):
    store = FakeExportStore()
    export_id = start_and_run(store)
    store.exports[export_id]["file_expires_at"] = (
        datetime.now(timezone.utc) + timedelta(minutes=5)
    ).isoformat()
    token = service.create_download_link(store, "user-1", export_id).rsplit("/", 1)[1]

    real = service.time.monotonic
    monkeypatch.setattr(service.time, "monotonic", lambda: real() + 61)
    with pytest.raises(ExportRejected) as error:
        service.redeem_download_link(token)
    assert error.value.status_code == 404


# ---- housekeeping ----------------------------------------------------------------------------------

def test_sweep_removes_expired_zips_and_leftover_work(monkeypatch):
    ready = config.EXPORT_DIR / "ready"
    ready.mkdir(parents=True)
    old, new = ready / "old.zip", ready / "new.zip"
    old.write_bytes(b"x")
    new.write_bytes(b"x")
    workspace.create("left-over")
    workspace.create("running")

    now = old.stat().st_mtime + config.EXPORT_FILE_TTL_MINUTES * 60 + 1
    os.utime(new, (now, now))
    workspace.sweep(active_ids={"running"}, now=now)

    assert not old.exists() and new.exists()
    assert not workspace.work_dir("left-over").exists()
    assert workspace.work_dir("running").exists()


# ---- HTTP layer -------------------------------------------------------------------------------------

@pytest.fixture
def client(downloads, monkeypatch):
    store = FakeExportStore()
    monkeypatch.setattr(service, "submit", lambda s, job: run_export(s, job))
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[auth.get_current_user_id] = lambda: "user-1"
    test_client = TestClient(app)
    test_client.store = store
    yield test_client
    app.dependency_overrides.clear()


def test_export_then_download_over_http(client):
    response = client.post("/exports", json={"playlist_id": PLAYLIST})
    assert response.status_code == 202
    assert response.json()["total_songs"] == 3
    export_id = response.json()["export_id"]

    link = client.post(f"/exports/{export_id}/download-link")
    assert link.status_code == 200

    download = client.get(link.json()["path"])
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/zip"
    assert "attachment" in download.headers["content-disposition"]
    assert "goku" in download.headers["content-disposition"]

    other = client.post(f"/exports/{uuid.uuid4()}/download-link")
    assert other.status_code == 404


def test_http_errors_use_the_shared_shape(client):
    client.store.tracks = []
    response = client.post("/exports", json={"playlist_id": PLAYLIST})
    assert response.status_code == 409
    assert response.json()["detail"]["message"] == "This playlist has no songs to export."


def test_bad_ids_are_rejected_before_any_work(client):
    assert client.post("/exports", json={"playlist_id": "nope"}).status_code == 422
    assert client.post("/exports", json={"playlist_id": PLAYLIST, "format": "folder"}).status_code == 422
    assert client.post("/exports/not-a-uuid/cancel").status_code == 422


def test_unknown_download_token_is_404(client):
    assert client.get("/exports/download/made-up").status_code == 404


def test_exports_need_a_sign_in():
    app.dependency_overrides[get_store] = lambda: FakeExportStore()
    try:
        response = TestClient(app).post("/exports", json={"playlist_id": PLAYLIST})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 401


# ---- deleting history -------------------------------------------------------------------------------

def test_delete_removes_the_row_and_the_zip(downloads):
    store = FakeExportStore()
    export_id = start_and_run(store)
    assert workspace.ready_path(export_id).exists()

    service.delete_export(store, "user-1", export_id)

    assert export_id not in store.exports
    assert not [k for k in store.items if k[0] == export_id]
    assert not workspace.ready_path(export_id).exists()


def test_delete_refusals(downloads):
    store = FakeExportStore()
    finished = start_and_run(store)
    with pytest.raises(ExportRejected) as error:
        service.delete_export(store, "someone-else", finished)
    assert error.value.status_code == 404

    running = prepare_export(store, "user-1", PLAYLIST)
    with pytest.raises(ExportRejected) as error:
        service.delete_export(store, "user-1", running.export_id)
    assert error.value.status_code == 409
    assert running.export_id in store.exports


def test_clear_history_keeps_a_running_export(downloads):
    store = FakeExportStore()
    first = start_and_run(store)
    second = start_and_run(store)
    running = prepare_export(store, "user-1", PLAYLIST)

    assert service.clear_history(store, "user-1") == 2

    assert set(store.exports) == {running.export_id}
    assert not workspace.ready_path(first).exists()
    assert not workspace.ready_path(second).exists()


def test_a_locked_zip_does_not_break_deleting(downloads, monkeypatch):
    store = FakeExportStore()
    export_id = start_and_run(store)

    def locked(_):
        raise PermissionError("in use")

    monkeypatch.setattr(workspace, "discard_ready", locked)
    service.delete_export(store, "user-1", export_id)  # must not raise
    assert export_id not in store.exports


def test_delete_over_http(client):
    export_id = client.post("/exports", json={"playlist_id": PLAYLIST}).json()["export_id"]
    assert client.delete(f"/exports/{export_id}").status_code == 204
    assert client.delete(f"/exports/{export_id}").status_code == 404

    client.post("/exports", json={"playlist_id": PLAYLIST})
    assert client.delete("/exports").json() == {"deleted": 1}
    assert client.store.exports == {}
