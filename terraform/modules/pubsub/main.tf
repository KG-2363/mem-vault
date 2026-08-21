variable "project_id" { type = string }
variable "labels"     { type = map(string) }

locals {
  topics = {
    "photo-uploaded" = {}
    "photo-enhanced" = {}
    "photo-failed"   = {}
  }
}

resource "google_pubsub_topic" "topics" {
  for_each = local.topics

  name   = each.key
  labels = var.labels

  message_storage_policy {
    allowed_persistence_regions = ["asia-south1"]
  }

  message_retention_duration = "604800s" # 7 days
}

# Subscription: Enhancement Service pulls photo.uploaded
resource "google_pubsub_subscription" "enhancement_pull" {
  name  = "photo-uploaded-enhancement-sub"
  topic = google_pubsub_topic.topics["photo-uploaded"].id

  ack_deadline_seconds       = 300
  message_retention_duration = "604800s"
  retain_acked_messages      = false

  enable_exactly_once_delivery = true

  expiration_policy {
    ttl = ""
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.topics["photo-failed"].id
    max_delivery_attempts = 5
  }
}

# Subscription: BigQuery streaming sink for all events
resource "google_pubsub_subscription" "bq_sink_uploaded" {
  name  = "photo-uploaded-bq-sub"
  topic = google_pubsub_topic.topics["photo-uploaded"].id

  bigquery_config {
    table            = "${var.project_id}.analytics.events_raw"
    use_topic_schema = false
    write_metadata   = true
  }

  expiration_policy { ttl = "" }
}

resource "google_pubsub_subscription" "bq_sink_enhanced" {
  name  = "photo-enhanced-bq-sub"
  topic = google_pubsub_topic.topics["photo-enhanced"].id

  bigquery_config {
    table            = "${var.project_id}.analytics.events_raw"
    use_topic_schema = false
    write_metadata   = true
  }

  expiration_policy { ttl = "" }
}

output "upload_topic_id"  { value = google_pubsub_topic.topics["photo-uploaded"].id }
output "enhance_topic_id" { value = google_pubsub_topic.topics["photo-enhanced"].id }
output "failed_topic_id"  { value = google_pubsub_topic.topics["photo-failed"].id }
