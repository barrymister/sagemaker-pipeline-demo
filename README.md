# sagemaker-pipeline-demo

End-to-end ML data pipeline demonstrating AWS SageMaker patterns. Raw CSV → ETL → SageMaker training job → Step Functions orchestration → deployed endpoint → inference.

Runs 100% locally via LocalStack during development. One env var change switches to real AWS.

---

## What it does

```
S3 (raw data)
    │
    ▼
ETL Transform (preprocessing + feature engineering)
    │
    ▼
SageMaker Training Job (XGBoost classifier)
    │
    ▼
Step Functions Pipeline (orchestrates all stages)
    │
    ▼
SageMaker Endpoint (real-time inference)
    │
    ▼
Model Monitor (data drift + quality alerts)
```

---

## AWS cert alignment

This project covers all 4 domains of the AWS ML Engineer Associate (MLA-C01) exam:

| This project | AWS concept | Exam domain |
|---|---|---|
| `pipeline/ingest.py` | S3 data lake ingestion | Domain 1: Data Preparation |
| `pipeline/transform.py` | SageMaker Processing Job | Domain 1: Data Preparation |
| `pipeline/train.py` | SageMaker Training Job | Domain 2: Model Development |
| `step_functions/pipeline_definition.json` | SageMaker Pipelines / Step Functions | Domain 2: Model Development |
| `pipeline/evaluate.py` | SageMaker Experiments + evaluation metrics | Domain 2: Model Development |
| `pipeline/deploy.py` | SageMaker Endpoint + Model Registry | Domain 3: Deployment |
| Model Monitor config | SageMaker Model Monitor | Domain 4: Monitoring |
| LocalStack swap | Cost-aware architecture | All domains |

---

## Quick start

### Local development (LocalStack — $0)

**Prerequisites:** Docker + Docker Compose, Python 3.11, AWS CLI configured for LocalStack

```bash
git clone https://github.com/barrymister/sagemaker-pipeline-demo.git
cd sagemaker-pipeline-demo

cp .env.example .env
# Edit .env: set USE_LOCALSTACK=true

# Start LocalStack
docker-compose up -d

# Initialize S3 buckets and IAM roles
bash scripts/setup_localstack.sh

# Run the full pipeline
python scripts/run_pipeline.py
```

### Real AWS (free tier — $0–$20 total)

```bash
# Edit .env: set USE_LOCALSTACK=false, add real AWS credentials
# Set billing alerts FIRST (see below)
python scripts/run_pipeline.py

# IMPORTANT: Clean up after demo run
aws sagemaker delete-endpoint --endpoint-name sagemaker-pipeline-demo
aws s3 rb s3://sagemaker-pipeline-demo-data --force
```

### AWS billing safety

```bash
# Set alert at $5 BEFORE running on real AWS
aws budgets create-budget --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://scripts/billing_alert.json \
  --notifications-with-subscribers file://scripts/billing_alert_notifications.json
```

Expected real AWS cost: **< $5** for a single end-to-end demo run using `ml.t3.medium`.

---

## Project structure

```
sagemaker-pipeline-demo/
├── pipeline/
│   ├── ingest.py           # S3 data ingestion
│   ├── transform.py        # ETL preprocessing (SageMaker Processing Job)
│   ├── train.py            # SageMaker training job (XGBoost)
│   ├── evaluate.py         # Model evaluation + Experiments logging
│   └── deploy.py           # Endpoint deployment + Model Registry
├── step_functions/
│   └── pipeline_definition.json   # Step Functions state machine
├── scripts/
│   ├── setup_localstack.sh        # LocalStack init + S3 bucket setup
│   └── run_pipeline.py            # End-to-end pipeline runner
├── data/sample/                   # Small sample dataset (add your own)
├── docs/adr/
│   └── 001-localstack-for-local-dev.md
├── docker-compose.yml             # LocalStack
├── requirements.txt
├── .env.example
└── CONTRIBUTING.md
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `USE_LOCALSTACK` | `true` | `true` = local dev, `false` = real AWS |
| `AWS_ENDPOINT_URL` | `http://localhost:4566` | LocalStack endpoint (ignored when `USE_LOCALSTACK=false`) |
| `AWS_DEFAULT_REGION` | `us-east-1` | AWS region |
| `S3_BUCKET` | `sagemaker-pipeline-demo-data` | S3 bucket for data + artifacts |
| `SAGEMAKER_ROLE_ARN` | — | IAM role ARN (real AWS only) |
| `AWS_ACCESS_KEY_ID` | `test` | Use `test` for LocalStack |
| `AWS_SECRET_ACCESS_KEY` | `test` | Use `test` for LocalStack |

---

## MLOps concepts demonstrated

| Pattern | Implementation |
|---|---|
| Experiment tracking | SageMaker Experiments — every training run logged |
| Model versioning | SageMaker Model Registry — approve/reject model versions |
| Pipeline orchestration | Step Functions state machine — retry logic, error handling |
| Feature store pattern | S3-based feature store with versioned datasets |
| Endpoint management | SageMaker real-time endpoint with auto-scaling config |
| Cost control | LocalStack for dev, billing alerts for real AWS |

---

## Infrastructure

Development: LocalStack (Docker Compose, runs on any machine with Docker)
Production demo: AWS free tier (`ml.t3.medium`, `us-east-1`)

---

## License

MIT — use freely, attribution appreciated.
