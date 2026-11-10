
import pytest

from app.youtube import (
    parse_video_id,
    watch_url,
    InvalidLink
)


VALID_ID = "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={VALID_ID}",
        f"https://youtu.be/{VALID_ID}",
        f"https://youtube.com/shorts/{VALID_ID}",
        f"https://youtube.com/embed/{VALID_ID}",
        f"https://youtube.com/live/{VALID_ID}",
        f"https://music.youtube.com/watch?v={VALID_ID}",
        f"youtube.com/watch?v={VALID_ID}",
        f"https://www.youtube.com/watch?v={VALID_ID}&t=30",
    ]
)
def test_valid_youtube_urls(url):
    assert parse_video_id(url) == VALID_ID


@pytest.mark.parametrize(
    "url",
    [
        "https://google.com",
        "https://youtube.com/playlist?list=PL123456",
        "https://youtube.com/watch",
        "https://youtu.be/invalid",
        "https://youtube.com.evil.example/watch?v=" + VALID_ID,
        "javascript:alert(1)",
        "https://youtube.com/watch?v=ABCDEFGHIJK&v=LMNOPQRSTUV",
    ]
)
def test_invalid_youtube_urls(url):
    with pytest.raises(InvalidLink):
        parse_video_id(url)


def test_canonical_watch_url():
    assert watch_url(VALID_ID) == (
        f"https://www.youtube.com/watch?v={VALID_ID}"
    )
