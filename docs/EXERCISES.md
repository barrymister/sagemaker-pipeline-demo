# Exercises — sagemaker-pipeline-demo

Hands-on exercises mapped to AWS ML Engineer Associate (MLA-C01) exam domains.

These exercises reference real code in the repo. You don't need to run on real AWS — LocalStack is sufficient for most exercises.

---

## Exercise 1 — S3 and Data Ingestion

**Cert domain:** Data Preparation for ML (28%)

Open `pipeline/ingest.py`.

**Questions to answer:**

1. The `get_s3_client()` function returns different clients depending on `USE_LOCALSTACK`. What is the only line that changes between the LocalStack and real AWS client? What does removing `endpoint_url` do?

2. The `upload_dataset()` function calls `client.upload_file(local_path, s3_bucket, s3_key)`. On the AWS ML cert, a question asks: "You have a 50GB training dataset that needs to be uploaded efficiently to S3 for a SageMaker training job. What should you use?" The answer is **S3 multipart upload**. Where in boto3 would you enable this — what parameter or class handles it automatically for large files?

3. Why does the pipeline store data in S3 rather than writing directly to the training instance? Name the SageMaker data input mode that streams data from S3 during training without downloading it first (hint: it's in `TrainingInput` in `train.py`).

4. The `ensure_bucket()` function swallows the error if the bucket already exists. What exception does boto3 raise for a missing bucket? (Check the `except` clause.) In production, when would silently continuing be wrong?

---

## Exercise 2 — Feature Engineering and Processing Jobs

**Cert domain:** Data Preparation for ML (28%)

Open `pipeline/transform.py`.

**Questions to answer:**

1. The transform splits data 70/15/15 (train/val/test) using `df.sample(frac=0.70, random_state=42)`. Why is `random_state=42` important for reproducibility? What happens to experiment tracking if you remove it?

2. The comment says "SageMaker equivalent: SageMaker Processing Job running a ScriptProcessor or SKLearnProcessor." Name the difference between these two processor types. Which one would you use if your preprocessing code is pure Python with pandas? Which if you need scikit-learn's preprocessing classes?

3. In the `TODO` comment inside `run_local_transform()`, you'd add custom feature engineering. Name two feature engineering operations commonly tested on the AWS ML cert:
   - One for handling **categorical** features (string columns)
   - One for handling **numerical** features with very different scales

4. SageMaker Feature Store is a managed alternative to manually uploading processed features to S3. What problem does it solve that plain S3 doesn't? When would you use Feature Store vs plain S3?

---

## Exercise 3 — Training Jobs and Hyperparameters

**Cert domain:** ML Model Development (26%)

Open `pipeline/train.py`.

**Questions to answer:**

1. The hyperparameters dict includes `"objective": "binary:logistic"`. The AWS ML cert tests this directly: what does this objective function output — a raw score, a probability, or a class label? What would you change to train a multi-class classifier instead?

2. The `estimator.fit()` call passes `experiment_config` with `ExperimentName` and `TrialName`. In the SageMaker console, where would you find this experiment and its metrics? What is the difference between an **Experiment**, a **Trial**, and a **Trial Component** in SageMaker's tracking hierarchy?

3. The training instance type is `ml.t3.medium`. The cert tests your knowledge of when to choose different instance types. Match each scenario to the right instance family:
   - Training a large deep learning model that needs a GPU → `ml.___`
   - Training a small XGBoost model on <1GB of data → `ml.___`
   - Running batch transform inference on 10GB of data → `ml.___`

4. The `estimator.fit()` call has `wait=True`. What happens if you set it to `False`? In a Step Functions pipeline, which call pattern does the Step Functions resource `arn:aws:states:::sagemaker:createTrainingJob.sync` correspond to?

---

## Exercise 4 — Endpoints and Deployment

**Cert domain:** Deployment and Orchestration (22%)

Open `pipeline/deploy.py`.

**Questions to answer:**

1. The `deploy_endpoint()` function creates a SageMaker real-time endpoint. Explain the difference between these three SageMaker inference options:
   - **Real-time endpoint** (what `deploy_endpoint()` creates)
   - **Batch transform job**
   - **Serverless inference**
   Which would you use to score 100M rows overnight? Which for a low-traffic API that needs sub-second response?

2. The endpoint uses `instance_type="ml.t3.medium"` with `initial_instance_count=1`. A production endpoint needs to handle traffic spikes. Name the SageMaker feature that automatically adjusts `instance_count` based on load. What CloudWatch metric does it scale on by default?

3. The `run_inference()` function sends `ContentType="text/csv"` as a CSV string. What is the SageMaker equivalent of a "health check" for an endpoint? How would you verify the endpoint is accepting traffic before sending production requests?

4. The comment says "Always delete endpoints when done — they cost money when idle." Why does an idle SageMaker endpoint still cost money? Name the SageMaker feature (not endpoint deletion) that can reduce costs by taking the endpoint to zero capacity when there is no traffic.

---

## Exercise 5 — Monitoring and Data Drift

**Cert domain:** ML Solution Monitoring, Maintenance, and Security (24%)

**No code to open for this exercise — answer from memory, then verify with the AWS docs or tech stack reference.**

**Questions to answer:**

1. After deploying an endpoint, you want to detect when the real-world input data distribution starts to differ from the training data (data drift). Name the SageMaker service for this. What does it need from the training pipeline in order to establish a **baseline**?

2. What is the difference between **data quality drift** and **model quality drift** in SageMaker Model Monitor?
   - Data quality drift: monitors ___
   - Model quality drift: monitors ___
   Which one requires ground truth labels to compute?

3. The evaluation step in `pipeline/evaluate.py` writes an `evaluation.json` with `accuracy`, `precision`, `recall`, `f1_score`, and `auc_roc`. The cert tests metric interpretation. For a fraud detection model:
   - Which metric matters most and why — precision or recall?
   - What does a `roc_auc` of 0.5 mean about the model?
   - What does a high `precision` but low `recall` indicate about the fraud threshold?

4. SageMaker Model Registry stores models with an approval status of `PendingManualApproval`. In `pipeline/evaluate.py → register_model()`, this is set on registration. Name the AWS service/feature that can **automatically** trigger a deployment when approval status changes from `PendingManualApproval` to `Approved`. (Hint: it's not Lambda.)

---

## Exercise 6 — Step Functions Orchestration

**Cert domain:** Deployment and Orchestration (22%)

Open `step_functions/pipeline_definition.json`.

**Questions to answer:**

1. Every `Task` state has a `Catch` block with `"ResultPath": "$.error"`. Explain what `ResultPath` does: where does the error information go in the state machine's data object? Why is this useful for debugging a failed pipeline run?

2. The `QualityGate` state is a `Choice` type. What is the alternative to a `Choice` state in Step Functions for running multiple branches **in parallel** (not conditionally)? Where in an ML pipeline would you use parallel execution?

3. The `States.Format('ingest-{}', $$.Execution.Name)` expression builds a unique job name per execution. Why do SageMaker job names need to be unique per run? What happens if you resubmit a pipeline with the same execution name?

4. The `Train` state uses resource `arn:aws:states:::sagemaker:createTrainingJob.sync`. The `.sync` suffix is a Step Functions **optimized integration pattern**. What does `.sync` do that a plain `createTrainingJob` (without `.sync`) does not? Which is appropriate for a long-running training job?

---

## Production Cross-Reference

These exercises cover cert theory. The following production systems implement the same patterns at scale — reference them during interviews to demonstrate real-world application:

| Cert concept | Production implementation | Where |
|---|---|---|
| SageMaker Experiments (Ex. 3) | MLflow experiment tracking with direct API integration — single-run logging to avoid duplicate compute | [llm-eval-pipeline](https://github.com/barrymister/llm-eval-pipeline) |
| Model Registry + approval gates (Ex. 5) | Model catalog with 40+ models, capability metadata, and compatibility guards that reject incompatible model/task combinations before inference | [ai-model-selector](https://npmjs.com/package/ai-model-selector) |
| Step Functions orchestration (Ex. 6) | App Factory provisioning pipeline — 929-line idempotent pipeline with per-step skip guards, error handling, and resumption support | growth-engine (private) |
| S3 data pipeline (Ex. 1) | 55-vendor database with automated affiliate tracking, revenue classification, and AI-driven product selection | growth-engine (private) |
| Endpoint deployment + monitoring (Ex. 4-5) | SSE streaming endpoints with heartbeat keepalives for long-running inference, Cloudflare Tunnel routing, Coolify PaaS auto-deploy | growth-engine (private) |
