variable "project_id"  { type = string }
variable "region"      { type = string }
variable "environment" { type = string }
variable "labels"      { type = map(string) }

resource "google_container_cluster" "autopilot" {
  provider = google-beta
  name     = "memvault-${var.environment}"
  location = var.region

  enable_autopilot = true

  resource_labels = var.labels

  # Private cluster
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  ip_allocation_policy {}

  release_channel {
    channel = "REGULAR"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Istio / ASM (Autopilot managed)
  addons_config {
    http_load_balancing {
      disabled = false
    }
  }

  notification_config {
    pubsub {
      enabled = true
      topic   = "projects/${var.project_id}/topics/gke-cluster-notifications"
    }
  }

  deletion_protection = var.environment == "production"
}

output "cluster_name" { value = google_container_cluster.autopilot.name }
output "endpoint"     { value = google_container_cluster.autopilot.endpoint }
