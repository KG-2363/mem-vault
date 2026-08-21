locals {
  bucket_name = var.gcs_bucket_name != "" ? var.gcs_bucket_name : "memvault-photos-${var.project_id}"
  labels = {
    env     = var.environment
    managed = "terraform"
    product = "memvault"
  }
}

# ── Enable required APIs ───────────────────────────────────────────────────────

resource "google_project_service" "apis" {
  for_each = toset([
    "storage.googleapis.com",
    "pubsub.googleapis.com",
    "firestore.googleapis.com",
    "run.googleapis.com",
    "container.googleapis.com",
    "aiplatform.googleapis.com",
    "bigquery.googleapis.com",
    "apigateway.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudkms.googleapis.com",
    "monitoring.googleapis.com",
    "cloudtrace.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "firebase.googleapis.com",
    "identitytoolkit.googleapis.com",
  ])

  service            = each.key
  disable_on_destroy = false
}

# ── Cloud KMS (CMEK for DPDP compliance) ──────────────────────────────────────

resource "google_kms_key_ring" "memvault" {
  name     = "memvault-keyring-${var.environment}"
  location = var.region
  depends_on = [google_project_service.apis]
}

resource "google_kms_crypto_key" "storage" {
  name            = "memvault-storage-key"
  key_ring        = google_kms_key_ring.memvault.id
  rotation_period = "7776000s" # 90 days

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_kms_crypto_key" "bigquery" {
  name            = "memvault-bq-key"
  key_ring        = google_kms_key_ring.memvault.id
  rotation_period = "7776000s"

  lifecycle {
    prevent_destroy = true
  }
}

# ── GCS module ────────────────────────────────────────────────────────────────

module "gcs" {
  source     = "./modules/gcs"
  project_id = var.project_id
  region     = var.region
  bucket_name = local.bucket_name
  kms_key_id  = google_kms_crypto_key.storage.id
  labels      = local.labels
  depends_on  = [google_project_service.apis, google_kms_crypto_key.storage]
}

# ── Pub/Sub module ────────────────────────────────────────────────────────────

module "pubsub" {
  source     = "./modules/pubsub"
  project_id = var.project_id
  labels     = local.labels
  depends_on = [google_project_service.apis]
}

# ── BigQuery module ───────────────────────────────────────────────────────────

module "bigquery" {
  source      = "./modules/bigquery"
  project_id  = var.project_id
  region      = var.region
  kms_key_id  = google_kms_crypto_key.bigquery.id
  labels      = local.labels
  depends_on  = [google_project_service.apis, google_kms_crypto_key.bigquery]
}

# ── IAM module ────────────────────────────────────────────────────────────────

module "iam" {
  source      = "./modules/iam"
  project_id  = var.project_id
  bucket_name = local.bucket_name
  depends_on  = [module.gcs, google_project_service.apis]
}

# ── GKE Autopilot module ──────────────────────────────────────────────────────

module "gke" {
  source      = "./modules/gke"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  labels      = local.labels
  depends_on  = [google_project_service.apis]
}

# ── API Gateway module ────────────────────────────────────────────────────────

module "api_gateway" {
  source     = "./modules/api-gateway"
  project_id = var.project_id
  region     = var.region
  depends_on = [google_project_service.apis]
}

# ── Artifact Registry ─────────────────────────────────────────────────────────

resource "google_artifact_registry_repository" "services" {
  repository_id = "memvault-services"
  location      = var.region
  format        = "DOCKER"
  labels        = local.labels
  depends_on    = [google_project_service.apis]
}

# ── Secret Manager — placeholder secrets ─────────────────────────────────────

resource "google_secret_manager_secret" "firebase_admin_sdk" {
  secret_id = "firebase-admin-sdk-${var.environment}"
  labels    = local.labels

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  depends_on = [google_project_service.apis]
}
