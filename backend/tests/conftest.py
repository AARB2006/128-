"""
Shared test helpers: a fake in-memory store and sample ids.

FakeStore behaves like the database functions start_import,
record_import_item and finish_import (database/schema.sql, section 10):
the same rules and the same messages. The functions themselves are tested
against a real Postgres separately.
"""

import pytest

from app.supabase_store import StoreError


def user_id(user):
    """Tests pass a plain id string; the app passes a SignedInUser."""
    return getattr(user, "id", user)


class FakeStore:
    """In-memory stand-in for SupabaseStore (the import half)."""

    def __init__(self, library=None, recent=0, active=False, daily_limit=100):
        self.library = set(library or [])  # video ids the user already owns
        self.recent = recent  # links submitted in the last 24 hours
        self.active = active  # another import is running
        self.daily_limit = daily_limit
        self.batches = {}
        self.items = {}  # (batch_id, line_no) -> dict
        self.songs = []  # (owner_id, track)
        self.keys = {}  # batch_id -> job key, while the batch runs
        self.fail_after_records = None  # simulate Supabase going down

    # ---- as the user --------------------------------------------------------

    def start_import(self, user, items):
        if self.active:
            raise StoreError("An import is already running. Wait for it to finish.", 409)
        if self.recent + len(items) > self.daily_limit:
            remaining = max(self.daily_limit - self.recent, 0)
            raise StoreError(
                f"Daily import limit reached. You can import {remaining} more link(s) "
                "in the next 24 hours.",
                429,
            )

        batch_id = f"batch-{len(self.batches) + 1}"
        planned = []
        for item in items:
            item = dict(item)
            if item["status"] == "pending" and item["video_id"] in self.library:
                item.update(status="duplicate", error_message="Already in your library.")
            item["processed_at"] = None if item["status"] == "pending" else "now"
            planned.append(item)

        work = any(i["status"] == "pending" for i in planned)
        status = (
            "processing" if work
            else "failed" if any(i["status"] == "invalid" for i in planned)
            else "completed"
        )
        self.batches[batch_id] = {
            "owner_id": user_id(user),
            "total_links": len(items),
            "status": status,
        }
        for item in planned:
            self.items[(batch_id, item["line_no"])] = item
        key = f"key-{batch_id}" if work else None
        if key:
            self.keys[batch_id] = key
        return {
            "batch_id": batch_id,
            "job_key": key,
            "status": status,
            "items": [
                {"line_no": i["line_no"], "status": i["status"], "error_message": i["error_message"]}
                for i in planned
            ],
        }

    # ---- with the job key ---------------------------------------------------

    def _check(self, batch_id):
        if batch_id not in self.keys:
            raise StoreError("This job can no longer be updated.", 403)

    def record_import_item(self, batch_id, line_no, status, error_message=None,
                           title=None, duration_seconds=None):
        self._check(batch_id)
        if self.fail_after_records is not None:
            if self.fail_after_records == 0:
                raise StoreError("Could not reach Supabase: down")
            self.fail_after_records -= 1

        item = self.items[(batch_id, line_no)]
        song_id = None
        if status == "success":
            video_id = item["video_id"]
            if video_id in self.library:
                status, error_message = "duplicate", "Already in your library."
            else:
                self.library.add(video_id)
                self.songs.append((
                    self.batches[batch_id]["owner_id"],
                    {
                        "video_id": video_id,
                        "source_url": f"https://www.youtube.com/watch?v={video_id}",
                        "title": title,
                        "duration_seconds": duration_seconds,
                    },
                ))
                song_id = f"song-{len(self.songs)}"
                error_message = None
        item.update(status=status, error_message=error_message, song_id=song_id, processed_at="now")
        return status

    def finish_import(self, batch_id):
        self._check(batch_id)
        mine = [v for k, v in self.items.items() if k[0] == batch_id]
        for item in mine:
            if item["status"] == "pending":
                item.update(status="failed", error_message="The import stopped unexpectedly.")
        added = any(i["status"] == "success" for i in mine)
        problems = any(i["status"] in ("failed", "invalid") for i in mine)
        status = "partial" if problems and added else "failed" if problems else "completed"
        self.batches[batch_id]["status"] = status
        del self.keys[batch_id]
        return status

    def statuses(self, batch_id):
        return [
            self.items[key]["status"]
            for key in sorted(k for k in self.items if k[0] == batch_id)
        ]


@pytest.fixture
def store():
    return FakeStore()


def url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


# Valid 11-character video ids for tests.
A, B, C, D = "aaaaaaaaaaa", "bbbbbbbbbbb", "ccccccccccc", "ddddddddddd"
