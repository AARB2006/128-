"""
The only module that writes to Supabase with the secret key.

It talks to PostgREST (Supabase's REST layer) over plain HTTP. The secret key
bypasses row-level security, so every method that touches user data takes an
explicit owner_id that the caller got from a verified login token.
"""

import logging
from datetime import datetime, timezone

import httpx


logger = logging.getLogger(__name__)


class StoreError(Exception):
    """Raised when Supabase rejects or fails a request."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SupabaseStore:
    def __init__(self, url: str, secret_key: str, client: httpx.Client | None = None):
        self._base = f"{url}/rest/v1"

        # New-style secret keys are not JWTs, so they go in `apikey` ONLY.
        # (Putting one in an Authorization: Bearer header is rejected.)
        self._client = client or httpx.Client(
            timeout=15,
            headers={"apikey": secret_key},
        )

    # ---- low level ----------------------------------------------------------

    def _request(self, method, table, *, params=None, json=None, prefer=None):
        headers = {"Prefer": prefer} if prefer else None

        try:
            response = self._client.request(
                method,
                f"{self._base}/{table}",
                params=params,
                json=json,
                headers=headers,
            )
        except httpx.HTTPError as error:
            raise StoreError(f"Could not reach Supabase: {error}") from error

        if response.status_code >= 400:
            logger.error(
                "Supabase %s %s failed (%s): %s",
                method,
                table,
                response.status_code,
                response.text[:500],
            )
            raise StoreError(f"Supabase request failed ({response.status_code}).")

        return response.json() if response.content else None

    # ---- reads --------------------------------------------------------------

    def existing_video_ids(self, owner_id: str, video_ids: list[str]) -> set[str]:
        """Which of these videos are already in this user's library?"""
        if not video_ids:
            return set()

        rows = self._request(
            "GET",
            "songs",
            params={
                "select": "video_id",
                "owner_id": f"eq.{owner_id}",
                "video_id": f"in.({','.join(video_ids)})",
            },
        )
        return {row["video_id"] for row in rows}

    def recent_link_count(self, owner_id: str, since: datetime) -> int:
        """Links this user submitted since `since` (for the daily quota)."""
        rows = self._request(
            "GET",
            "import_batches",
            params={
                "select": "total_links",
                "owner_id": f"eq.{owner_id}",
                "created_at": f"gte.{since.isoformat()}",
            },
        )
        return sum(row["total_links"] for row in rows)

    def has_active_batch(self, owner_id: str) -> bool:
        rows = self._request(
            "GET",
            "import_batches",
            params={
                "select": "batch_id",
                "owner_id": f"eq.{owner_id}",
                "status": "in.(pending,processing)",
                "limit": "1",
            },
        )
        return bool(rows)

    # ---- writes -------------------------------------------------------------

    def create_batch(self, owner_id: str, total_links: int, status: str) -> str:
        rows = self._request(
            "POST",
            "import_batches",
            json={
                "owner_id": owner_id,
                "total_links": total_links,
                "status": status,
                "completed_at": _now() if status != "processing" else None,
            },
            prefer="return=representation",
        )
        return rows[0]["batch_id"]

    def create_items(self, batch_id: str, items: list[dict]) -> None:
        self._request(
            "POST",
            "import_items",
            json=[{**item, "batch_id": batch_id} for item in items],
            prefer="return=minimal",
        )

    def insert_song(self, owner_id: str, track: dict) -> str | None:
        """
        Save a song. Returns its new song_id, or None if this user already
        has that video (the unique (owner_id, video_id) rule decided it).
        """
        rows = self._request(
            "POST",
            "songs",
            params={"on_conflict": "owner_id,video_id"},
            json={
                "owner_id": owner_id,
                "video_id": track["video_id"],
                "source_url": track["source_url"],
                "title": track["title"],
                "duration_seconds": track["duration_seconds"],
                "metadata_fetched_at": _now(),
            },
            prefer="resolution=ignore-duplicates,return=representation",
        )
        return rows[0]["song_id"] if rows else None

    def update_item(self, batch_id: str, line_no: int, **fields) -> None:
        self._request(
            "PATCH",
            "import_items",
            params={"batch_id": f"eq.{batch_id}", "line_no": f"eq.{line_no}"},
            json={**fields, "processed_at": _now()},
            prefer="return=minimal",
        )

    def finish_batch(self, batch_id: str, status: str) -> None:
        self._request(
            "PATCH",
            "import_batches",
            params={"batch_id": f"eq.{batch_id}"},
            json={"status": status, "completed_at": _now()},
            prefer="return=minimal",
        )

    def fail_interrupted_batches(self) -> int:
        """
        Called once at startup. A restart kills any import that was running,
        so mark those batches (and their unfinished links) as failed instead of
        leaving them "processing" forever. Assumes ONE backend process.
        """
        rows = self._request(
            "GET",
            "import_batches",
            params={
                "select": "batch_id",
                "status": "in.(pending,processing)",
            },
        )
        if not rows:
            return 0

        ids = ",".join(row["batch_id"] for row in rows)

        self._request(
            "PATCH",
            "import_items",
            params={"batch_id": f"in.({ids})", "status": "eq.pending"},
            json={
                "status": "failed",
                "error_message": "The import was interrupted. Please try again.",
                "processed_at": _now(),
            },
            prefer="return=minimal",
        )
        self._request(
            "PATCH",
            "import_batches",
            params={"batch_id": f"in.({ids})"},
            json={"status": "failed", "completed_at": _now()},
            prefer="return=minimal",
        )
        return len(rows)