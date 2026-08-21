variable "project_id"  { type = string }
variable "bucket_name" { type = string }

# ── Service Accounts ──────────────────────────────────────────────────────────

resource "google_service_account" "upload_service" {
  account_id   = "memvault-upload-svc"
  display_name = "MemVault Upload Service"
}

resource "google_service_account" "enhancement_service" {
  account_id   = "memvault-enhance-svc"
  display_name = "MemVault Enhancement Service"
}

resource "google_service_account" "delivery_service" {
  account_id   = "memvault-delivery-svc"
  display_name = "MemVault Delivery Service"
}

resource "google_service_account" "auth_service" {
  account_id   = "memvault-auth-svc"
  display_name = "MemVault Auth Service"
}

resource "google_service_account" "api_service" {
  account_id   = "memvault-api-svc"
  display_name = "MemVault B2B API Service"
}

# ── Upload Service Roles ──────────────────────────────────────────────────────

resource "google_storage_bucket_iam_member" "upload_write" {
  bucket = var.bucket_name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.upload_service.email}"
}

resource "google_project_iam_member" "upload_pubsub_publish" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.upload_service.email}"
}

resource "google_project_iam_member" "upload_firestore_write" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.upload_service.email}"
}

# ── Enhancement Service Roles ─────────────────────────────────────────────────

resource "google_storage_bucket_iam_member" "enhance_readwrite" {
  bucket = var.bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.enhancement_service.email}"
}

resource "google_project_iam_member" "enhance_pubsub_subscribe" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.enhancement_service.email}"
}

resource "google_project_iam_member" "enhance_pubsub_publish" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.enhancement_service.email}"
}

resource "google_project_iam_member" "enhance_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.enhancement_service.email}"
}

resource "google_project_iam_member" "enhance_vertex_ai" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.enhancement_service.email}"
}

# ── Delivery Service Roles ────────────────────────────────────────────────────

resource "google_storage_bucket_iam_member" "delivery_sign_urls" {
  bucket = var.bucket_name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.delivery_service.email}"
}

resource "google_project_iam_member" "delivery_sign_blobs" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:${google_service_account.delivery_service.email}"
}

resource "google_project_iam_member" "delivery_firestore" {
  project = var.project_id
  role    = "roles/datastore.viewer"
  member  = "serviceAccount:${google_service_account.delivery_service.email}"
}

# ── Auth Service Roles ────────────────────────────────────────────────────────

resource "google_project_iam_member" "auth_firebase_admin" {
  project = var.project_id
  role    = "roles/firebase.admin"
  member  = "serviceAccount:${google_service_account.auth_service.email}"
}

resource "google_project_iam_member" "auth_secret_access" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.auth_service.email}"
}

# ── Workload Identity Bindings ────────────────────────────────────────────────

locals {
  wi_bindings = {
    upload       = { sa = google_service_account.upload_service,      k8s_sa = "upload-service" }
    enhancement  = { sa = google_service_account.enhancement_service, k8s_sa = "enhancement-service" }
    delivery     = { sa = google_service_account.delivery_service,    k8s_sa = "delivery-service" }
    auth         = { sa = google_service_account.auth_service,        k8s_sa = "auth-service" }
    api          = { sa = google_service_account.api_service,         k8s_sa = "api-service" }
  }
}

resource "google_service_account_iam_member" "workload_identity" {
  for_each = local.wi_bindings

  service_account_id = each.value.sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[default/${each.value.k8s_sa}]"
}

output "upload_service_sa_email"      { value = google_service_account.upload_service.email }
output "enhancement_service_sa_email" { value = google_service_account.enhancement_service.email }
output "delivery_service_sa_email"    { value = google_service_account.delivery_service.email }
