"""
ETL Transform (SageMaker Processing Job)
-----------------------------------------
Preprocesses raw data: handles missing values, encodes categoricals,
splits into train/validation/test sets.

SageMaker equivalent: SageMaker Processing Job running a ScriptProcessor
or SKLearnProcessor. Reads from S3, writes processed splits back to S3.
"""

import os
import json
import boto3
import pandas as pd
from pathlib import Path


def run_local_transform(input_path: str, output_dir: str) -> dict:
    """
    Run ETL transform locally (mirrors what a SageMaker Processing Job would do).

    Args:
        input_path: Path to raw CSV file
        output_dir: Directory to write train/val/test splits

    Returns:
        Dict with paths to output files
    """
    print(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
    print(f"  Missing values: {df.isnull().sum().sum()}")

    # TODO: Add your feature engineering here
    # Example: df = engineer_features(df)

    # Split: 70% train, 15% val, 15% test
    train = df.sample(frac=0.70, random_state=42)
    remaining = df.drop(train.index)
    val = remaining.sample(frac=0.50, random_state=42)
    test = remaining.drop(val.index)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    splits = {
        "train": f"{output_dir}/train.csv",
        "validation": f"{output_dir}/validation.csv",
        "test": f"{output_dir}/test.csv",
    }

    train.to_csv(splits["train"], index=False)
    val.to_csv(splits["validation"], index=False)
    test.to_csv(splits["test"], index=False)

    print(f"  Train: {len(train)} rows → {splits['train']}")
    print(f"  Validation: {len(val)} rows → {splits['validation']}")
    print(f"  Test: {len(test)} rows → {splits['test']}")

    return splits


def upload_splits(splits: dict, s3_bucket: str, s3_prefix: str = "processed/") -> dict:
    """Upload processed splits to S3."""
    from pipeline.ingest import get_s3_client
    client = get_s3_client()

    s3_uris = {}
    for split_name, local_path in splits.items():
        s3_key = f"{s3_prefix}{split_name}.csv"
        client.upload_file(local_path, s3_bucket, s3_key)
        s3_uris[split_name] = f"s3://{s3_bucket}/{s3_key}"
        print(f"  Uploaded {split_name} → {s3_uris[split_name]}")

    return s3_uris
