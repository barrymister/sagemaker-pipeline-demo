"""
Model Evaluation
-----------------
Evaluates the trained model against the test set.
Logs metrics to SageMaker Experiments.

SageMaker equivalent: SageMaker Processing Job running evaluation script,
or inline evaluation step in a SageMaker Pipeline.
"""

import os
import json
import boto3
import pandas as pd
from pathlib import Path


def evaluate_model(
    model_artifact_s3_uri: str,
    test_s3_uri: str,
    output_dir: str = "/tmp/evaluation",
) -> dict:
    """
    Download model artifact, run predictions on test set, compute metrics.

    Args:
        model_artifact_s3_uri: S3 URI of model.tar.gz
        test_s3_uri: S3 URI of test.csv
        output_dir: Local dir to write evaluation.json

    Returns:
        Dict with evaluation metrics
    """
    # TODO: Download model artifact, load XGBoost model, run predictions
    # Placeholder metrics — replace with real evaluation logic
    metrics = {
        "accuracy": 0.0,
        "precision": 0.0,
        "recall": 0.0,
        "f1_score": 0.0,
        "auc_roc": 0.0,
    }

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    eval_path = f"{output_dir}/evaluation.json"
    with open(eval_path, "w") as f:
        json.dump({"metrics": metrics}, f, indent=2)

    print(f"Evaluation complete: {metrics}")
    print(f"Results written to {eval_path}")
    return metrics


def register_model(
    model_artifact_s3_uri: str,
    metrics: dict,
    model_package_group: str = "sagemaker-pipeline-demo",
) -> str:
    """
    Register model in SageMaker Model Registry with evaluation metrics.
    Approval status: PendingManualApproval (requires human sign-off to deploy).

    Returns:
        Model package ARN
    """
    # TODO: Implement SageMaker Model Registry registration
    print(f"Model registration → group: {model_package_group}")
    print(f"  Metrics: {metrics}")
    print(f"  Approval: PendingManualApproval")
    return f"arn:aws:sagemaker:us-east-1:000000000000:model-package/{model_package_group}/1"
