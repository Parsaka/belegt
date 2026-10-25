#!/usr/bin/env bash
# One-time bootstrap, run by the project owner in Cloud Shell AFTER the free trial is active.
#
#   PROJECT_ID=belegt-xxxxxx BILLING_ACCOUNT_ID=XXXXXX-XXXXXX-XXXXXX bash scripts/bootstrap_gcp.sh
#
# Creates only what Terraform needs to run from GitHub Actions without stored keys:
#   1. the Terraform state bucket
#   2. a service account for CI
#   3. a Workload Identity pool + provider that trusts only this GitHub repository
# It prints the values to store as GitHub repository variables. Nothing here is secret.
set -euo pipefail

: "${PROJECT_ID:?set PROJECT_ID}"
: "${BILLING_ACCOUNT_ID:?set BILLING_ACCOUNT_ID}"
REPO="${GITHUB_REPOSITORY:-Parsaka/belegt}"
REGION="${REGION:-europe-west1}"
SA_NAME="terraform-ci"
SA="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
POOL="github"
PROVIDER="belegt"

gcloud config set project "$PROJECT_ID" >/dev/null
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"

echo "Enabling the APIs Terraform needs to start"
gcloud services enable \
  cloudresourcemanager.googleapis.com iam.googleapis.com iamcredentials.googleapis.com \
  sts.googleapis.com serviceusage.googleapis.com cloudbilling.googleapis.com \
  billingbudgets.googleapis.com storage.googleapis.com

echo "State bucket"
gcloud storage buckets describe "gs://${PROJECT_ID}-tfstate" >/dev/null 2>&1 || \
  gcloud storage buckets create "gs://${PROJECT_ID}-tfstate" --location="$REGION" \
    --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets update "gs://${PROJECT_ID}-tfstate" --versioning

echo "CI service account"
gcloud iam service-accounts describe "$SA" >/dev/null 2>&1 || \
  gcloud iam service-accounts create "$SA_NAME" --display-name="Terraform from GitHub Actions"
for role in roles/editor roles/resourcemanager.projectIamAdmin roles/iam.serviceAccountAdmin \
            roles/serviceusage.serviceUsageAdmin roles/run.admin roles/container.admin; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$SA" \
    --role="$role" --condition=None >/dev/null
done
# The budget and the kill switch's binding live on the billing account.
gcloud billing accounts add-iam-policy-binding "$BILLING_ACCOUNT_ID" \
  --member="serviceAccount:$SA" --role="roles/billing.admin" >/dev/null

echo "Workload Identity Federation (only ${REPO} may use it)"
gcloud iam workload-identity-pools describe "$POOL" --location=global >/dev/null 2>&1 || \
  gcloud iam workload-identity-pools create "$POOL" --location=global --display-name="GitHub"
gcloud iam workload-identity-pools providers describe "$PROVIDER" --location=global \
  --workload-identity-pool="$POOL" >/dev/null 2>&1 || \
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" --location=global \
    --workload-identity-pool="$POOL" --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition="assertion.repository == '${REPO}'"
gcloud iam service-accounts add-iam-policy-binding "$SA" --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${REPO}" >/dev/null

cat <<OUT

Done. Add these as GitHub repository VARIABLES (Settings -> Secrets and variables -> Actions -> Variables):

  GCP_PROJECT_ID          = ${PROJECT_ID}
  GCP_BILLING_ACCOUNT_ID  = ${BILLING_ACCOUNT_ID}
  GCP_WIF_PROVIDER        = projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}
  GCP_CI_SERVICE_ACCOUNT  = ${SA}
  TF_STATE_BUCKET         = ${PROJECT_ID}-tfstate

No keys were created. Nothing above is secret.
OUT
