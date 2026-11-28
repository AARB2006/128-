"""
Checks the Supabase login token on each request and returns the signed-in
user: their id, and the token itself, which the backend uses to talk to the
database as that user.
"""

import logging
from dataclasses import dataclass

import httpx
from fastapi import Header

from . import config
from .errors import api_error


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SignedInUser:
    id: str
    token: str

    def __repr__(self) -> str:  # never print the token in logs
        return f"SignedInUser(id={self.id!r})"


def get_signed_in_user(authorization: str | None = Header(default=None)) -> SignedInUser:
    """
    Identify the caller from their Supabase login token.

    The browser sends `Authorization: Bearer <access token>`. We never trust a
    user id sent in the request body: we ask Supabase Auth who the token
    belongs to. This works with any signing-key setup (no JWT secret needed).
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        api_error(401, "You must be signed in to do this.")

    token = authorization[7:].strip()

    if not config.SUPABASE_URL or not config.SUPABASE_PUBLISHABLE_KEY:
        logger.error("SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY are not set")
        api_error(503, "The server is not configured yet.")

    try:
        response = httpx.get(
            f"{config.SUPABASE_URL}/auth/v1/user",
            headers={
                "apikey": config.SUPABASE_PUBLISHABLE_KEY,
                "Authorization": f"Bearer {token}",
            },
            timeout=10,
        )
    except httpx.HTTPError:
        logger.exception("Could not reach Supabase Auth")
        api_error(503, "Could not verify your sign-in. Please try again.")

    if response.status_code != 200:
        api_error(401, "Your session has expired. Please sign in again.")

    user_id = response.json().get("id")

    if not user_id:
        api_error(401, "Your session could not be verified.")

    return SignedInUser(id=user_id, token=token)