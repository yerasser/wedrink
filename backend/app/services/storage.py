import boto3
from botocore.client import Config

from app.core.config import settings

_s3 = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

def ensure_bucket():
    try:
        _s3.head_bucket(Bucket=settings.S3_BUCKET)
    except Exception:
        _s3.create_bucket(Bucket=settings.S3_BUCKET)

def put_object(key: str, data: bytes, content_type: str | None = None):
    ensure_bucket()
    extra = {}
    if content_type:
        extra["ContentType"] = content_type
    _s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=data, **extra)

def get_object(key: str) -> bytes:
    resp = _s3.get_object(Bucket=settings.S3_BUCKET, Key=key)
    return resp["Body"].read()

def delete_object(key: str):
    _s3.delete_object(Bucket=settings.S3_BUCKET, Key=key)
