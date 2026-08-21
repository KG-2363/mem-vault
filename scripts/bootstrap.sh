#!/usr/bin/env bash
# One-time GCP project bootstrap. Run before terraform apply.
# Usage: ./scripts/bootstrap.sh --project YOUR_PROJECT_ID --region asia-south1

set -euo pipefail

PROJECT_ID=""
REGION="asia-south1"

while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT_ID="$2"; shift 2;;
    --region)  REGION="$2";     shift 2;;
    *) echo "Unknown flag: $1"; exit 1;;
  esac
done

[[ -z "$PROJECT_ID" ]] && { echo "ERROR: --project is required"; exit 1; }

echo "Bootstrapping MemVault on project=$PROJECT_ID region=$REGION"

# 1. Set default project
gcloud config set project "$PROJECT_ID"

# 2. Enable billing check
BILLING=$(gcloud beta billing projects describe "$PROJECT_ID" --format="value(billingEnabled)")
[[ "$BILLING" != "True" ]] && { echo "ERROR: Billing not enabled on $PROJECT_ID"; exit 1; }

# 3. Enable only the APIs needed for Terraform to bootstrap the rest
gcloud services enable \
  cloudresourcemanager.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com \
  --project "$PROJECT_ID"

# 4. Create Terraform state bucket
TF_BUCKET="memvault-tf-state-$PROJECT_ID"
if ! gsutil ls "gs://$TF_BUCKET" &>/dev/null; then
  gsutil mb -p "$PROJECT_ID" -l "$REGION" -b on "gs://$TF_BUCKET"
  gsutil versioning set on "gs://$TF_BUCKET"
  echo "Created Terraform state bucket: gs://$TF_BUCKET"
else
  echo "Terraform state bucket already exists: gs://$TF_BUCKET"
fi

# 5. Create Terraform service account (CI/CD will impersonate this)
TF_SA="terraform-runner@$PROJECT_ID.iam.gserviceaccount.com"
if ! gcloud iam service-accounts describe "$TF_SA" --project "$PROJECT_ID" &>/dev/null; then
  gcloud iam service-accounts create terraform-runner \
    --display-name "Terraform Runner" \
    --project "$PROJECT_ID"
fi

# Grant Terraform SA the minimal roles it needs
for ROLE in \
  "roles/owner"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member "serviceAccount:$TF_SA" \
    --role "$ROLE" \
    --quiet
done

gsutil iam ch "serviceAccount:$TF_SA:roles/storage.admin" "gs://$TF_BUCKET"

echo ""
echo "Bootstrap complete."
echo ""
echo "Next steps:"
echo "  cd terraform"
echo "  terraform init"
echo "  terraform plan -var='project_id=$PROJECT_ID' -var='region=$REGION'"
echo "  terraform apply -var='project_id=$PROJECT_ID' -var='region=$REGION'"
