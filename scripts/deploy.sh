#!/usr/bin/env bash
# Deploy all services to GKE.
# Usage: ./scripts/deploy.sh --project YOUR_PROJECT_ID --env staging|production --tag IMAGE_TAG

set -euo pipefail

PROJECT_ID=""
ENV="staging"
TAG="latest"
REGION="asia-south1"

while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT_ID="$2"; shift 2;;
    --env)     ENV="$2";         shift 2;;
    --tag)     TAG="$2";         shift 2;;
    --region)  REGION="$2";      shift 2;;
    *) echo "Unknown flag: $1"; exit 1;;
  esac
done

[[ -z "$PROJECT_ID" ]] && { echo "ERROR: --project required"; exit 1; }

REGISTRY="$REGION-docker.pkg.dev/$PROJECT_ID/memvault-services"
CLUSTER="memvault-$ENV"
NAMESPACE="memvault-$ENV"

echo "Deploying to cluster=$CLUSTER namespace=$NAMESPACE tag=$TAG"

# 1. Authenticate to GKE
gcloud container clusters get-credentials "$CLUSTER" \
  --region "$REGION" --project "$PROJECT_ID"

# 2. Build and push all service images
SERVICES=(upload-service enhancement-service delivery-service auth-service api-service)
for SVC in "${SERVICES[@]}"; do
  echo "Building $SVC..."
  docker build -t "$REGISTRY/$SVC:$TAG" "services/$SVC"
  docker push "$REGISTRY/$SVC:$TAG"
done

# 3. Apply Kustomize overlay
kubectl apply -k "k8s/overlays/$ENV"

# 4. Wait for rollouts
for SVC in upload-service delivery-service auth-service api-service; do
  kubectl rollout status deployment/"$SVC" -n "$NAMESPACE" --timeout=120s
done

echo ""
echo "Deployment to $ENV complete."
