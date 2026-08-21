variable "project_id" { type = string }
variable "region"     { type = string }
variable "kms_key_id" { type = string }
variable "labels"     { type = map(string) }

resource "google_bigquery_dataset" "analytics" {
  dataset_id  = "analytics"
  location    = var.region
  description = "MemVault application analytics — all events and derived marts"
  labels      = var.labels

  default_encryption_configuration {
    kms_key_name = var.kms_key_id
  }

  delete_contents_on_destroy = false
}

resource "google_bigquery_table" "events_raw" {
  dataset_id          = google_bigquery_dataset.analytics.dataset_id
  table_id            = "events_raw"
  deletion_protection = true

  time_partitioning {
    type  = "DAY"
    field = "event_timestamp"
  }

  clustering = ["tenant_id", "event_type"]

  schema = jsonencode([
    { name = "event_id",        type = "STRING",    mode = "REQUIRED" },
    { name = "event_type",      type = "STRING",    mode = "REQUIRED" },
    { name = "tenant_id",       type = "STRING",    mode = "REQUIRED" },
    { name = "album_id",        type = "STRING",    mode = "NULLABLE" },
    { name = "photo_id",        type = "STRING",    mode = "NULLABLE" },
    { name = "user_id",         type = "STRING",    mode = "NULLABLE" },
    { name = "payload",         type = "JSON",      mode = "NULLABLE" },
    { name = "event_timestamp", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "ingested_at",     type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "pubsub_message_id", type = "STRING",  mode = "NULLABLE" },
  ])

  encryption_configuration {
    kms_key_name = var.kms_key_id
  }
}

output "dataset_id"      { value = google_bigquery_dataset.analytics.dataset_id }
output "events_table_id" { value = google_bigquery_table.events_raw.table_id }
