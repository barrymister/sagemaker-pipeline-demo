# Operations Guide — sagemaker-pipeline-demo

How to run the pipeline locally via LocalStack, understand each stage, and switch to real AWS when ready.

---

## What this project does

Demonstrates an end-to-end ML pipeline using SageMaker patterns:

```
Raw CSV → S3 ingest → ETL transform → XGBoost training → Evaluation → Endpoint deployment
```

Everything runs locally via **LocalStack** (a local AWS emulator) — no AWS account or cost needed for development. Switching to real AWS is one environment variable change.

---

## Prerequisites

- Docker + Docker Compose
- Python 3.11
- AWS CLI (`pip install awscli` or use the binary)

```bash
pip install -r requirements.txt
```

---

## Step 1 — Start LocalStack

```bash
docker-compose up -d
```

Wait ~15 seconds for LocalStack to initialize, then run setup:

```bash
bash scripts/setup_localstack.sh
```

This creates:
- S3 bucket: `sagemaker-pipeline-demo-data` with prefixes `raw/`, `processed/`, `models/`, etc.
- Mock IAM role: `arn:aws:iam::000000000000:role/SageMakerRole`

Verify it worked:
```bash
aws --endpoint-url=http://localhost:4566 s3 ls s3://sagemaker-pipeline-demo-data/
```

---

## Step 2 — Understand the pipeline stages

Each stage is a separate Python module in `pipeline/`. Run them in order, or look at `scripts/run_pipeline.py` for the full sequence.

### Stage 1: Ingest (`pipeline/ingest.py`)

Uploads a raw CSV file to S3. In real AWS this would be your data lake landing zone.

```python
from pipeline.ingest import ensure_bucket, upload_dataset

ensure_bucket("sagemaker-pipeline-demo-data")
s3_uri = upload_dataset("data/raw.csv", "sagemaker-pipeline-demo-data")
# → s3://sagemaker-pipeline-demo-data/raw/raw.csv
```

**LocalStack vs real AWS:** The `get_s3_client()` function reads `USE_LOCALSTACK=true` from the environment. Set `USE_LOCALSTACK=false` and remove `AWS_ENDPOINT_URL` to hit real AWS.

### Stage 2: Transform (`pipeline/transform.py`)

ETL: handles missing values, splits into train/val/test (70/15/15), uploads splits to S3.

In real SageMaker, this step runs as a **SageMaker Processing Job** on managed compute. Here it runs locally.

```python
from pipeline.transform import run_local_transform, upload_splits

splits = run_local_transform("data/raw.csv", "/tmp/processed")
s3_uris = upload_splits(splits, "sagemaker-pipeline-demo-data")
```

The `TODO` in `transform.py` marks where you'd add custom feature engineering.

### Stage 3: Train (`pipeline/train.py`)

Launches an XGBoost training job. LocalStack simulates the SageMaker API calls; actual XGBoost training would run on managed `ml.t3.medium` instances in real AWS.

Key hyperparameters (configured in `launch_training_job()`):
- `max_depth=5` — how deep each tree grows (controls complexity)
- `eta=0.2` — learning rate (smaller = more conservative)
- `num_round=100` — number of boosting rounds
- `objective=binary:logistic` — binary classification output

Metrics are logged to **SageMaker Experiments** via `experiment_config` in the `estimator.fit()` call.

### Stage 4: Evaluate (`pipeline/evaluate.py`)

Downloads the model artifact, scores the test set, writes `evaluation.json`. The `register_model()` function registers in the **SageMaker Model Registry** with `PendingManualApproval` status — meaning a human must approve before deployment.

### Stage 5: Deploy (`pipeline/deploy.py`)

Deploys an approved model to a SageMaker real-time **endpoint**.

```python
from pipeline.deploy import deploy_endpoint, run_inference, delete_endpoint

endpoint_name = deploy_endpoint(model_artifact_s3_uri)
result = run_inference(endpoint_name, "1.2,0.5,0.8,...")   # CSV features
delete_endpoint(endpoint_name)   # ALWAYS delete when done — endpoints cost money
```

**Cost warning:** On real AWS, a running endpoint costs ~$0.05/hr for `ml.t3.medium`. Always call `delete_endpoint()` when done.

---

## Step 3 — Read the Step Functions definition

Open `step_functions/pipeline_definition.json`. This is an AWS Step Functions state machine that orchestrates the full pipeline.

Key patterns to understand:

**State types:**
- `"Type": "Task"` — calls a SageMaker API (ProcessingJob, TrainingJob, Endpoint)
- `"Type": "Choice"` — branches based on a condition (the QualityGate)
- `"Type": "Succeed"` / `"Type": "Fail"` — terminal states

**Error handling pattern (on every Task state):**
```json
"Catch": [{
  "ErrorEquals": ["States.ALL"],
  "Next": "PipelineFailed",
  "ResultPath": "$.error"
}]
```
This means: if this step fails for any reason, jump to `PipelineFailed` state and store the error in `$.error`.

**Quality gate (the Choice state):**
```json
"QualityGate": {
  "Type": "Choice",
  "Choices": [{"Variable": "$.evaluation.metrics.f1_score", "NumericGreaterThan": 0.75, "Next": "Deploy"}],
  "Default": "ModelBelowThreshold"
}
```
Only deploys if F1 > 0.75. This is the same pattern used in SageMaker Pipelines with `ConditionStep`.

---

## Switch to real AWS

Change these env vars:
```bash
USE_LOCALSTACK=false
AWS_DEFAULT_REGION=us-east-1
SAGEMAKER_ROLE_ARN=arn:aws:iam::<your-account-id>:role/SageMakerRole
# Remove AWS_ENDPOINT_URL entirely
```

**Before running on real AWS:**
1. Set billing alert at $5 (the `setup_localstack.sh` script does not do this for you on real AWS — do it in the AWS Console under Billing → Budgets)
2. Run ingest + transform only first to verify S3 operations work
3. Training on `ml.t3.medium` costs ~$0.05/hr — a training job should finish in under an hour
4. Delete the endpoint immediately after testing: `aws sagemaker delete-endpoint --endpoint-name sagemaker-pipeline-demo`

**Full cleanup:**
```bash
aws sagemaker delete-endpoint --endpoint-name sagemaker-pipeline-demo
aws s3 rm s3://sagemaker-pipeline-demo-data --recursive
aws sagemaker delete-experiment --experiment-name sagemaker-pipeline-demo
```

---

## Stop LocalStack

```bash
docker-compose down         # stop, keep data
docker-compose down -v      # stop + wipe all LocalStack state
```
