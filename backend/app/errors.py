"""
One shared error format for every API response.
"""

from fastapi import HTTPException


def api_error(status_code: int, message: str, problems=None):
    """Every error uses one shape: {"detail": {"message", "problems"}}."""
    raise HTTPException(
        status_code=status_code,
        detail={"message": message, "problems": problems or []},
    )