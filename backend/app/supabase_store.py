"""
The backend's only connection to the database (Supabase's REST layer, PostgREST).

It holds NO secret key. Every call is made either
  * as the signed-in user, with their login token, so row-level security and
    the database functions decide what they may read and change; or
  * with a job key, for the background work of an import or export (the login
    token may expire during a long export). A job key can only update its own
    job; see database/schema.sql, section 10.

Rules such as "one import at a time" and the daily limits are enforced by the
database functions, which answer with the message to show the user.
"""

import logging

import httpx

from .jobs import JobKeys


logger = logging.getLogger(__name__)

FINISHED = ("completed", "partial", "failed", "cancelled")


class StoreError(Exception):
    """Raised when Supabase rejects or fails a request. str(error) is the
    message to show; status_code is None when Supabase couldn't be reached."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _error_message(response: httpx.Response) -> str:
    try:
        message = response.json().get("message")
    except (ValueError, AttributeError):
        message = None
    return message or f"Supabase request failed ({response.status_code})."


class SupabaseStore:
    def __init__(
        self,
        url: str,
        publishable_key: str,
        jobs: JobKeys | None = None,
        client: httpx.Client | None = None,
    ):
        self._base = f"{url}/rest/v1"
        self._publishable_key = publishable_key
        self.jobs = jobs or JobKeys()
        self._client = client or httpx.Client(timeout=15)

    # ---- low level ----------------------------------------------------------

    def _request(self, method, path, *, token=None, params=None, json=None, prefer=None):
        # The publishable key identifies the app; the login token (if any)
        # identifies the user. Without a token, the database treats the call
        # as anonymous, which may only use job-key functions.
        headers = {"apikey": self._publishable_key}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if prefer:
            headers["Prefer"] = prefer

        try:
            response = self._client.request(
                method, f"{self._base}/{path}", params=params, json=json, headers=headers
            )
        except httpx.HTTPError as error:
            raise StoreError(f"Could not reach Supabase: {error}") from error

        if response.status_code >= 400:
            message = _error_message(response)
            logger.warning("Supabase %s %s: %s %s", method, path, response.status_code, message)
            raise StoreError(message, status_code=response.status_code)

        return response.json() if response.content else None

    def _rpc(self, name: str, args: dict, *, token: str | None = None):
        return self._request("POST", f"rpc/{name}", token=token, json=args)

    def _job_key(self, job_id: str) -> str:
        key = self.jobs.key_for(job_id)
        if key is None:
            raise StoreError("This job can no longer be updated.", status_code=403)
        return key

    # ---- as the signed-in user ------------------------------------------------

    def start_import(self, user, items: list[dict]) -> dict:
        """Record an import. Returns {batch_id, job_key, status, items}."""
        result = self._rpc("start_import", {"p_items": items}, token=user.token)
        if result.get("job_key"):
            self.jobs.remember("import", result["batch_id"], result["job_key"])
        return result

    def playlist_song_count(self, user, playlist_id: str) -> int:
        """Songs in one of the user's playlists (0 if it isn't theirs)."""
        rows = self._request(
            "GET",
            "playlist_songs",
            token=user.token,
            params={"select": "song_id", "playlist_id": f"eq.{playlist_id}"},
        )
        return len(rows)

    def start_export(self, user, playlist_id: str) -> dict:
        """Record an export. Returns {export_id, job_key, playlist_name, tracks}."""
        result = self._rpc("start_export", {"p_playlist_id": playlist_id}, token=user.token)
        self.jobs.remember("export", result["export_id"], result["job_key"])
        return result

    def get_export(self, user, export_id: str) -> dict | None:
        """The export row, with `playlist` = {name} (None if it was deleted)."""
        rows = self._request(
            "GET",
            "exports",
            token=user.token,
            params={"select": "*,playlist:playlists(name)", "export_id": f"eq.{export_id}"},
        )
        return rows[0] if rows else None

    def delete_export(self, user, export_id: str) -> bool:
        """Delete one finished export (its song rows go with it). A running
        export is never deleted. Returns whether a row was removed."""
        rows = self._request(
            "DELETE",
            "exports",
            token=user.token,
            params={
                "export_id": f"eq.{export_id}",
                "owner_id": f"eq.{user.id}",
                "status": "not.in.(pending,processing,packaging)",
                "select": "export_id",
            },
            prefer="return=representation",
        )
        return bool(rows)

    def delete_finished_exports(self, user) -> list[str]:
        """Delete all of the user's finished exports. Returns their ids."""
        rows = self._request(
            "DELETE",
            "exports",
            token=user.token,
            params={
                "owner_id": f"eq.{user.id}",
                "status": "not.in.(pending,processing,packaging)",
                "select": "export_id",
            },
            prefer="return=representation",
        )
        return [row["export_id"] for row in rows]

    # ---- with a job key (background work) -----------------------------------------

    def record_import_item(
        self,
        batch_id: str,
        line_no: int,
        status: str,
        error_message: str | None = None,
        title: str | None = None,
        duration_seconds: int | None = None,
    ) -> str:
        """Save one link's result. Returns its final status ('duplicate' if
        the song was added in the meantime)."""
        return self._rpc(
            "record_import_item",
            {
                "p_batch_id": batch_id,
                "p_job_key": self._job_key(batch_id),
                "p_line_no": line_no,
                "p_status": status,
                "p_error_message": error_message,
                "p_title": title,
                "p_duration_seconds": duration_seconds,
            },
        )

    def finish_import(self, batch_id: str) -> str:
        """Close the batch; links still pending are marked failed."""
        status = self._rpc(
            "finish_import", {"p_batch_id": batch_id, "p_job_key": self._job_key(batch_id)}
        )
        self.jobs.forget(batch_id)
        return status

    def update_export(self, export_id: str, **fields) -> None:
        self._rpc(
            "update_export_job",
            {"p_export_id": export_id, "p_job_key": self._job_key(export_id), "p_fields": fields},
        )
        if fields.get("status") in FINISHED:
            self.jobs.forget(export_id)

    def update_export_item(self, export_id: str, position: int, **fields) -> None:
        self._rpc(
            "update_export_item_job",
            {
                "p_export_id": export_id,
                "p_job_key": self._job_key(export_id),
                "p_position": position,
                "p_status": fields["status"],
                "p_error_message": fields.get("error_message"),
            },
        )

    def skip_pending_export_items(self, export_id: str, reason: str) -> None:
        self._rpc(
            "skip_pending_export_items_job",
            {"p_export_id": export_id, "p_job_key": self._job_key(export_id), "p_reason": reason},
        )

    # ---- at startup -------------------------------------------------------------------

    def recover_interrupted_jobs(self) -> int:
        """
        Mark jobs that were running when the backend last stopped (on this
        computer) as interrupted. Returns how many were closed.
        """
        closed = 0
        for kind, job_id, key in self.jobs.left_from_last_run():
            try:
                self._rpc("interrupt_job", {"p_kind": kind, "p_job_id": job_id, "p_job_key": key})
                closed += 1
            except StoreError as error:
                if error.status_code is None:
                    continue  # offline: try again next time
                # Any other answer means the job is already closed.
            self.jobs.forget(job_id)
        return closed
