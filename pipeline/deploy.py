"""
Endpoint Deployment
--------------------
Deploys an approved model from the Model Registry to a SageMaker real-time endpoint.

SageMaker equivalent: sagemaker.model.Model.deploy() or
Model Registry → Approved → auto-deploy via EventBridge.

IMPORTANT: Always delete endpoints when done — they cost money when idle.
Cleanup: aws sagemaker delete-endpoint --endpoint-name <name>
"""

import os
import boto3
import sagemaker
from sagemaker.model import Model


ENDPOINT_NAME = "sagemaker-pipeline-demo"


def deploy_endpoint(model_artifact_s3_uri: str, endpoint_name: str = ENDPOINT_NAME) -> str:
    """
    Deploy model to a SageMaker real-time endpoint.

    Args:
        model_artifact_s3_uri: S3 URI of model.tar.gz
        endpoint_name: Name for the deployed endpoint

    Returns:
        Endpoint name
    """
    from pipeline.train import get_sagemaker_session

    session = get_sagemaker_session()
    role = os.getenv("SAGEMAKER_ROLE_ARN", "arn:aws:iam::000000000000:role/SageMakerRole")

    # TODO: Replace with actual XGBoost container URI for your region
    container_uri = sagemaker.image_uris.retrieve(
        framework="xgboost",
        region=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        version="1.7-1",
    )

    model = Model(
        image_uri=container_uri,
        model_data=model_artifact_s3_uri,
        role=role,
        sagemaker_session=session,
    )

    predictor = model.deploy(
        initial_instance_count=1,
        instance_type=os.getenv("INFERENCE_INSTANCE_TYPE", "ml.t3.medium"),
        endpoint_name=endpoint_name,
    )

    print(f"Endpoint deployed: {endpoint_name}")
    print(f"REMEMBER: Run 'aws sagemaker delete-endpoint --endpoint-name {endpoint_name}' when done")
    return endpoint_name


def delete_endpoint(endpoint_name: str = ENDPOINT_NAME) -> None:
    """Delete endpoint to avoid ongoing costs."""
    from pipeline.ingest import get_s3_client
    import boto3

    client = boto3.client(
        "sagemaker",
        endpoint_url=os.getenv("AWS_ENDPOINT_URL") if os.getenv("USE_LOCALSTACK", "true").lower() == "true" else None,
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )
    client.delete_endpoint(EndpointName=endpoint_name)
    print(f"Endpoint deleted: {endpoint_name}")


def run_inference(endpoint_name: str, payload: str) -> dict:
    """
    Call a deployed endpoint with a CSV payload.

    Args:
        endpoint_name: Deployed endpoint name
        payload: CSV string of features (no header)

    Returns:
        Prediction result dict
    """
    runtime = boto3.client(
        "sagemaker-runtime",
        endpoint_url=os.getenv("AWS_ENDPOINT_URL") if os.getenv("USE_LOCALSTACK", "true").lower() == "true" else None,
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )
    response = runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType="text/csv",
        Body=payload,
    )
    result = response["Body"].read().decode("utf-8")
    return {"prediction": result, "endpoint": endpoint_name}
