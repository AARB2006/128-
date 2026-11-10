
from app.metadata import fetch_metadata, VideoRejected
from app.youtube import InvalidLink


# Public example video ID for testing.
TEST_URL = "https://youtu.be/qSLfaMncl_w?si=2wqlYb_KxiGgYHCX"


try:
    result = fetch_metadata(TEST_URL)

    print("\nMetadata lookup successful!")
    print("Video ID:", result["video_id"])
    print("Title:", result["title"])
    print("Duration:", result["duration_seconds"], "seconds")

except InvalidLink as error:
    print("Invalid URL:", error)

except VideoRejected as error:
    print("Video rejected:", error)

except Exception as error:
    print("Unexpected error:", error)
