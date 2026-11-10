
import re
import unicodedata


INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WHITESPACE = re.compile(r"\s+")

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def safe_filename(value: str, fallback: str = "track") -> str:
    if not isinstance(value, str):
        value = ""

    # Remove invisible control and formatting characters.
    value = "".join(
        char
        for char in value
        if unicodedata.category(char) not in {"Cc", "Cf"}
    )

    value = INVALID_CHARS.sub("", value)
    value = WHITESPACE.sub(" ", value)
    value = value.strip().rstrip(".")

    if not value:
        value = fallback

    # Windows reserves certain filenames even when they have extensions.
    first_part = value.split(".", 1)[0].upper()

    if first_part in WINDOWS_RESERVED_NAMES:
        value = f"_{value}"

    # Avoid excessively long filenames.
    return value[:150].rstrip(" .") or fallback
