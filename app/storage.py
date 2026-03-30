"""S3-compatible storage client.

Works with RunPod object storage, AWS S3, Cloudflare R2, or any S3-compatible service.
Only active when S3_BUCKET and S3_ACCESS_KEY are set in config — otherwise the app
falls back to local file storage as before.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        import boto3
        from app.config import settings

        kwargs: dict = {
            "aws_access_key_id": settings.S3_ACCESS_KEY,
            "aws_secret_access_key": settings.S3_SECRET_KEY,
            "region_name": settings.S3_REGION,
        }
        if settings.S3_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
        _client = boto3.client("s3", **kwargs)
    return _client


def s3_enabled() -> bool:
    from app.config import settings
    return bool(settings.S3_BUCKET and settings.S3_ACCESS_KEY)


def upload(file_bytes: bytes, key: str, content_type: str = "image/jpeg") -> str:
    """Upload bytes to S3 and return the public URL."""
    from app.config import settings

    _get_client().put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )

    if settings.S3_ENDPOINT_URL:
        return f"{settings.S3_ENDPOINT_URL.rstrip('/')}/{settings.S3_BUCKET}/{key}"
    return f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/{key}"


def _extract_s3_key(url: str) -> str | None:
    """If the URL points to our S3 bucket, return the object key. Otherwise None."""
    from app.config import settings
    if not (settings.S3_ENDPOINT_URL and settings.S3_BUCKET):
        return None
    prefix = f"{settings.S3_ENDPOINT_URL.rstrip('/')}/{settings.S3_BUCKET}/"
    if url.startswith(prefix):
        return url[len(prefix):]
    return None


def download_to_temp(url: str) -> Path:
    """Download a file to a temporary file. Uses boto3 for S3 URLs, plain HTTP otherwise."""
    suffix = Path(url.split("?")[0]).suffix or ".png"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.close()
    tmp_path = Path(tmp.name)

    key = _extract_s3_key(url)
    if key is not None:
        from app.config import settings
        response = _get_client().get_object(Bucket=settings.S3_BUCKET, Key=key)
        tmp_path.write_bytes(response["Body"].read())
    else:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "VehicleMLAgent/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            tmp_path.write_bytes(resp.read())

    return tmp_path
