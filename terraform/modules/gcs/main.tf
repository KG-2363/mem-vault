variable "project_id"  { type = string }
variable "region"      { type = string }
variable "bucket_name" { type = string }
variable "kms_key_id"  { type = string }
variable "labels"      { type = map(string) }

resource "google_storage_bucket" "photos" {
  name          = var.bucket_name
  location      = var.region
  storage_class = "STANDARD"
  labels        = var.labels

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  encryption {
    default_kms_key_name = var.kms_key_id
  }

  # DPDP Act 2023: minimum 3-year retention for photo data
  retention_policy {
    retention_period = 94608000 # 3 years in seconds
  }

  lifecycle_rule {
    condition { age = 30 }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition { age = 365 }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST"]
    response_header = ["Content-Type", "x-goog-resumable"]
    max_age_seconds = 3600
  }
}

# Separate bucket for Terraform state — bootstrap only
resource "google_storage_bucket" "tf_state" {
  name          = "memvault-tf-state-${var.project_id}"
  location      = var.region
  storage_class = "STANDARD"

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  versioning { enabled = true }
}

output "bucket_name" { value = google_storage_bucket.photos.name }
output "bucket_url"  { value = google_storage_bucket.photos.url }
