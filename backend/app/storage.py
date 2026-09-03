from __future__ import annotations

from minio import Minio

from app.config import get_settings


def get_client() -> Minio:
    settings = get_settings()
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_root_user,
        secret_key=settings.minio_root_password,
        secure=settings.minio_secure,
    )


def ensure_bucket() -> None:
    """Create the configured bucket if it does not exist yet. Idempotent."""
    settings = get_settings()
    client = get_client()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)
