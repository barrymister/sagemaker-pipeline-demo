# Contributing

## Development approach

This project uses AI-assisted development. Architecture, design decisions, and operational choices are human-authored. Implementation scaffolding and boilerplate leverage Claude Code for velocity.

Architecture Decision Records (`docs/adr/`) document the reasoning behind key choices — those are the signal for understanding how the system was designed.

## Adding a new pipeline stage

1. Create `pipeline/<stage_name>.py` with a clear docstring explaining the SageMaker equivalent
2. Add the stage to `scripts/run_pipeline.py`
3. Add the Step Functions state to `step_functions/pipeline_definition.json`
4. Update the README cert alignment table if the stage maps to a new exam domain

## LocalStack vs real AWS

Always develop and test against LocalStack first. The `USE_LOCALSTACK=true` env var routes all Boto3 calls to `http://localhost:4566`. Switching to real AWS is a single env var change — validate this works before any demo or interview.

## Cost discipline

- Set AWS billing alerts at $5 before any real AWS work
- Delete endpoints immediately after testing: `aws sagemaker delete-endpoint --endpoint-name sagemaker-pipeline-demo`
- Never commit real AWS credentials — `.env` is in `.gitignore`
