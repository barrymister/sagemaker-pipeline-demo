# ADR 001: Use LocalStack for Local Development Instead of Real AWS

**Status:** Accepted
**Date:** 2026-03-18

## Context

SageMaker, Step Functions, and S3 are the core AWS services this pipeline demonstrates. Real AWS development would require:
- Active AWS account with SageMaker access
- IAM roles and policies configured
- ml.t3.medium training instances ($0.05/hr but accumulates during dev)
- Endpoint costs while debugging ($0.05/hr per endpoint, easy to forget)
- Slow iteration: SageMaker training jobs take 3–10 minutes to spin up even on small instances

The goal is a portfolio project that can be developed and demoed locally, then validated on real AWS for the final portfolio artifact.

## Decision

Use [LocalStack](https://localstack.io) (open source, Docker Compose) for all local development. LocalStack implements the AWS API surface locally — the same Boto3 calls work against both LocalStack and real AWS.

One env var (`USE_LOCALSTACK=true/false`) switches between environments. All `boto3.client()` calls route through a factory function that injects the `endpoint_url` when LocalStack is active.

## Consequences

**Good:**
- Zero cost during development — iterate as fast as needed
- No real AWS credentials needed on developer machines
- Full pipeline runnable from `docker-compose up` + `python scripts/run_pipeline.py`
- Identical Boto3 API surface — code validated locally runs on real AWS unchanged
- CI/CD friendly — can run in GitHub Actions without cloud credentials

**Bad:**
- LocalStack free tier has limitations (SageMaker training jobs are simulated, not actually run)
- Some SageMaker-specific container behaviors can't be replicated locally
- Must validate against real AWS before treating the portfolio demo as authoritative

## Alternatives considered

**Real AWS from the start:** Rejected — cost and iteration speed make local development impractical for scaffolding and learning.

**Moto (Python mocking library):** Rejected — moto mocks at the Python object level, not at the HTTP level. LocalStack intercepts real HTTP calls, which means the code path is identical to real AWS.

**SageMaker Studio on free tier:** Rejected — no free tier for SageMaker Studio. JupyterLab instance costs money idle.
