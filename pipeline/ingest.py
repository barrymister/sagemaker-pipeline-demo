"""
S3 Data Ingestion
-----------------
Uploads raw CSV data to S3 (LocalStack or real AWS).
SageMaker equivalent: S3 data lake ingestion step.
"""

import os
import boto3
from pathlib import Path


def get_s3_client():
    """Return boto3 S3 client — LocalStack or real AWS based on USE_LOCALSTACK env var."""
    if os.getenv("USE_LOCALSTACK", "true").lower() == "true":
        return boto3.client(
            "s3",
            endpoint_url=os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        )
    return boto3.client("s3", region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))


def upload_dataset(local_path: str, s3_bucket: str, s3_prefix: str = "raw/") -> str:
    """
    Upload a local CSV dataset to S3.

    Args:
        local_path: Path to local CSV file
        s3_bucket: Target S3 bucket name
        s3_prefix: S3 key prefix (default: 'raw/')

    Returns:
        S3 URI of the uploaded file (s3://bucket/prefix/filename)
    """
    client = get_s3_client()
    filename = Path(local_path).name
    s3_key = f"{s3_prefix}{filename}"

    print(f"Uploading {local_path} → s3://{s3_bucket}/{s3_key}")
    client.upload_file(local_path, s3_bucket, s3_key)

    s3_uri = f"s3://{s3_bucket}/{s3_key}"
    print(f"Upload complete: {s3_uri}")
    return s3_uri


def ensure_bucket(s3_bucket: str) -> None:
    """Create S3 bucket if it doesn't exist."""
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=s3_bucket)
        print(f"Bucket exists: {s3_bucket}")
    except client.exceptions.ClientError:
        print(f"Creating bucket: {s3_bucket}")
        client.create_bucket(Bucket=s3_bucket)
