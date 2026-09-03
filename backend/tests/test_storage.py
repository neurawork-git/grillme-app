from __future__ import annotations

from app.config import get_settings
from app.storage import ensure_bucket, get_client


def test_ensure_bucket_is_idempotent():
    ensure_bucket()
    ensure_bucket()  # second call must not raise

    client = get_client()
    assert client.bucket_exists(get_settings().minio_bucket)
