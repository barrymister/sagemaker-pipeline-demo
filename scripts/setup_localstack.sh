#!/bin/bash
# setup_localstack.sh
# Initialize LocalStack with S3 buckets and mock IAM role needed for the pipeline.
# Run once after `docker-compose up -d`.

set -e

ENDPOINT="http://localhost:4566"
BUCKET="sagemaker-pipeline-demo-data"
REGION="us-east-1"

export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=$REGION

echo "=== Waiting for LocalStack to be ready ==="
until curl -s "$ENDPOINT/_localstack/health" | grep -q '"s3": "available"'; do
  echo "  Waiting..."
  sleep 2
done
echo "LocalStack ready."

echo ""
echo "=== Creating S3 bucket: $BUCKET ==="
aws --endpoint-url="$ENDPOINT" s3 mb "s3://$BUCKET" 2>/dev/null || echo "  Bucket already exists."

echo ""
echo "=== Creating S3 prefixes ==="
for prefix in raw/ processed/ train/ validation/ test/ models/ evaluation/; do
  aws --endpoint-url="$ENDPOINT" s3api put-object --bucket "$BUCKET" --key "$prefix" > /dev/null
  echo "  Created: s3://$BUCKET/$prefix"
done

echo ""
echo "=== Creating mock IAM role ==="
aws --endpoint-url="$ENDPOINT" iam create-role \
  --role-name SageMakerRole \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"sagemaker.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
  2>/dev/null || echo "  Role already exists."

echo ""
echo "=== LocalStack setup complete ==="
echo "Bucket:  s3://$BUCKET"
echo "Role:    arn:aws:iam::000000000000:role/SageMakerRole"
echo "Endpoint: $ENDPOINT"
