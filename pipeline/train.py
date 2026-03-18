"""
SageMaker Training Job
-----------------------
Launches an XGBoost training job against processed S3 data.
Logs parameters + metrics to SageMaker Experiments.

SageMaker equivalent: sagemaker.estimator.Estimator with XGBoost built-in algorithm.
LocalStack: Simulates the API calls; actual training runs locally via sklearn.
"""

import os
import json
import boto3
import sagemaker
from sagemaker.xgboost import XGBoost
from sagemaker.inputs import TrainingInput


def get_sagemaker_session():
    """Return SageMaker session — LocalStack-aware."""
    if os.getenv("USE_LOCALSTACK", "true").lower() == "true":
        boto_session = boto3.Session(
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        )
        return sagemaker.Session(
            boto_session=boto_session,
            sagemaker_client=boto3.client(
                "sagemaker",
                endpoint_url=os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566"),
                region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
                aws_access_key_id="test",
                aws_secret_access_key="test",
            ),
        )
    return sagemaker.Session()


def launch_training_job(
    train_s3_uri: str,
    val_s3_uri: str,
    output_s3_uri: str,
    experiment_name: str = "sagemaker-pipeline-demo",
    hyperparameters: dict = None,
) -> str:
    """
    Launch a SageMaker XGBoost training job.

    Args:
        train_s3_uri: S3 URI of training data
        val_s3_uri: S3 URI of validation data
        output_s3_uri: S3 URI for model artifacts
        experiment_name: SageMaker Experiments name for tracking
        hyperparameters: XGBoost hyperparameters (uses defaults if None)

    Returns:
        Training job name
    """
    if hyperparameters is None:
        hyperparameters = {
            "max_depth": 5,
            "eta": 0.2,
            "gamma": 4,
            "min_child_weight": 6,
            "subsample": 0.8,
            "objective": "binary:logistic",
            "num_round": 100,
        }

    session = get_sagemaker_session()
    role = os.getenv("SAGEMAKER_ROLE_ARN", "arn:aws:iam::000000000000:role/SageMakerRole")

    estimator = XGBoost(
        entry_point="train.py",  # TODO: add custom training script if needed
        role=role,
        instance_count=1,
        instance_type=os.getenv("TRAINING_INSTANCE_TYPE", "ml.t3.medium"),
        framework_version="1.7-1",
        hyperparameters=hyperparameters,
        output_path=output_s3_uri,
        sagemaker_session=session,
    )

    estimator.fit(
        inputs={
            "train": TrainingInput(train_s3_uri, content_type="text/csv"),
            "validation": TrainingInput(val_s3_uri, content_type="text/csv"),
        },
        experiment_config={
            "ExperimentName": experiment_name,
            "TrialName": f"{experiment_name}-trial",
            "TrialComponentDisplayName": "Training",
        },
        wait=True,
    )

    job_name = estimator.latest_training_job.name
    print(f"Training complete: {job_name}")
    return job_name
