"""
End-to-end pipeline runner.
Executes all stages: ingest → transform → train → evaluate → deploy.

Usage:
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --skip-deploy   # Train + evaluate only
    python scripts/run_pipeline.py --cleanup       # Delete endpoint after run
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.ingest import ensure_bucket, upload_dataset
from pipeline.transform import run_local_transform, upload_splits
from pipeline.train import launch_training_job
from pipeline.evaluate import evaluate_model, register_model
from pipeline.deploy import deploy_endpoint, delete_endpoint


def main():
    parser = argparse.ArgumentParser(description="Run the SageMaker pipeline demo")
    parser.add_argument("--skip-deploy", action="store_true", help="Skip endpoint deployment")
    parser.add_argument("--cleanup", action="store_true", help="Delete endpoint after run")
    parser.add_argument("--data", default="data/sample/dataset.csv", help="Path to input CSV")
    args = parser.parse_args()

    s3_bucket = os.getenv("S3_BUCKET", "sagemaker-pipeline-demo-data")
    use_localstack = os.getenv("USE_LOCALSTACK", "true").lower() == "true"

    print("=" * 60)
    print(f"SageMaker Pipeline Demo")
    print(f"Mode: {'LocalStack (local)' if use_localstack else 'Real AWS'}")
    print(f"Bucket: s3://{s3_bucket}")
    print("=" * 60)

    # Step 1: Ingest
    print("\n[1/4] Ingest")
    ensure_bucket(s3_bucket)
    raw_s3_uri = upload_dataset(args.data, s3_bucket)

    # Step 2: Transform
    print("\n[2/4] Transform")
    splits = run_local_transform(args.data, "/tmp/processed")
    s3_uris = upload_splits(splits, s3_bucket)

    # Step 3: Train
    print("\n[3/4] Train")
    job_name = launch_training_job(
        train_s3_uri=s3_uris["train"],
        val_s3_uri=s3_uris["validation"],
        output_s3_uri=f"s3://{s3_bucket}/models/",
    )

    # Step 4: Evaluate
    print("\n[4/4] Evaluate")
    metrics = evaluate_model(
        model_artifact_s3_uri=f"s3://{s3_bucket}/models/{job_name}/output/model.tar.gz",
        test_s3_uri=s3_uris["test"],
    )
    register_model(f"s3://{s3_bucket}/models/{job_name}/output/model.tar.gz", metrics)

    # Step 5: Deploy (optional)
    if not args.skip_deploy:
        print("\n[5/5] Deploy")
        endpoint_name = deploy_endpoint(f"s3://{s3_bucket}/models/{job_name}/output/model.tar.gz")
        if args.cleanup:
            print("\nCleaning up endpoint...")
            delete_endpoint(endpoint_name)
    else:
        print("\n[5/5] Deploy — SKIPPED")

    print("\n" + "=" * 60)
    print("Pipeline complete.")
    print(f"MLflow / SageMaker Experiments: check AWS console or LocalStack UI")
    print("=" * 60)


if __name__ == "__main__":
    main()
