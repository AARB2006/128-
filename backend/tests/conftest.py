"""
Shared test helpers: a fake in-memory store and sample ids.
"""

import pytest


class FakeStore:
    """In-memory stand-in for SupabaseStore."""

    def __init__(self, library=None, recent=0, active=False):
        self.library = set(library or [])  # video ids the user already owns
        self.recent = recent
        self.active = active
        self.batches = {}
        self.items = {}  # (batch_id, line_no) -> dict
        self.songs = []  # (owner_id, track)
        self.fail_on_update = False

    def existing_video_ids(self, owner_id, video_ids):
        return {v for v in video_ids if v in self.library}

    def recent_link_count(self, owner_id, since):
        return self.recent

    def has_active_batch(self, owner_id):
        return self.active

    def create_batch(self, owner_id, total_links, status):
        batch_id = f"batch-{len(self.batches) + 1}"
        self.batches[batch_id] = {
            "owner_id": owner_id,
            "total_links": total_links,
            "status": status,
        }
        return batch_id

    def create_items(self, batch_id, items):
        for item in items:
            self.items[(batch_id, item["line_no"])] = dict(item)

    def insert_song(self, owner_id, track):
        if track["video_id"] in self.library:
            return None
        self.library.add(track["video_id"])
        self.songs.append((owner_id, track))
        return f"song-{len(self.songs)}"

    def update_item(self, batch_id, line_no, **fields):
        if self.fail_on_update:
            raise RuntimeError("Supabase is down")
        self.items[(batch_id, line_no)].update(fields)

    def finish_batch(self, batch_id, status):
        self.batches[batch_id]["status"] = status

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