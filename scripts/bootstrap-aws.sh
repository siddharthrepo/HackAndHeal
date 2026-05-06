#!/usr/bin/env bash
# bootstrap-aws.sh — one-time idempotent setup of AWS prerequisites for the pipelines.
# Creates:
#   * S3 bucket for Terraform remote state  (healthmeter-terraform-state)
#   * DynamoDB table for state locking      (terraform-locks)
# Run locally with AWS credentials configured (admin or sufficient IAM).

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
STATE_BUCKET="healthmeter-terraform-state"
LOCK_TABLE="terraform-locks"

echo "Region: $REGION"

# --- S3 bucket for Terraform state ---
if aws s3api head-bucket --bucket "$STATE_BUCKET" 2>/dev/null; then
  echo "✓ S3 bucket $STATE_BUCKET already exists"
else
  echo "→ Creating S3 bucket $STATE_BUCKET"
  if [ "$REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$STATE_BUCKET" --region "$REGION"
  else
    aws s3api create-bucket --bucket "$STATE_BUCKET" --region "$REGION" \
      --create-bucket-configuration LocationConstraint="$REGION"
  fi
fi

aws s3api put-bucket-versioning \
  --bucket "$STATE_BUCKET" \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket "$STATE_BUCKET" \
  --server-side-encryption-configuration '{
    "Rules": [{ "ApplyServerSideEncryptionByDefault": { "SSEAlgorithm": "AES256" } }]
  }'

aws s3api put-public-access-block \
  --bucket "$STATE_BUCKET" \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
echo "✓ Versioning + encryption + public-access-block on $STATE_BUCKET"

# --- DynamoDB table for state locking ---
if aws dynamodb describe-table --table-name "$LOCK_TABLE" --region "$REGION" >/dev/null 2>&1; then
  echo "✓ DynamoDB table $LOCK_TABLE already exists"
else
  echo "→ Creating DynamoDB table $LOCK_TABLE"
  aws dynamodb create-table \
    --table-name "$LOCK_TABLE" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region "$REGION"
  echo "→ Waiting for table to become ACTIVE..."
  aws dynamodb wait table-exists --table-name "$LOCK_TABLE" --region "$REGION"
fi

cat <<DONE

✅ Bootstrap complete.

Next:
  1. Make sure your EC2 key-pair name in infra/variables.tf matches one that exists in AWS.
  2. Set the GitHub Actions secrets listed in DEPLOY.md.
  3. Run the 'Infrastructure Setup' workflow.
  4. Run the 'Deploy Application' workflow.
DONE
