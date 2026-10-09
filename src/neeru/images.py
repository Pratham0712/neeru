"""Identify an uploaded image by its first bytes instead of trusting a file name or header."""

MAX_IMAGE_BYTES = 3_500_000  # stays under Bedrock's per-image limit


def detect_format(data: bytes) -> str | None:
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None
