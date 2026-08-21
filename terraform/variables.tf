variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Primary GCP region — must be an India region for DPDP compliance"
  type        = string
  default     = "asia-south1"

  validation {
    condition     = startswith(var.region, "asia-south")
    error_message = "Region must be asia-south1 or asia-south2 for DPDP data-residency compliance."
  }
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Must be staging or production."
  }
}

variable "gcs_bucket_name" {
  description = "Name of the primary photo storage bucket"
  type        = string
  default     = ""
}

variable "gke_node_count" {
  description = "Initial node count per zone for GKE (Autopilot ignores this — kept for documentation)"
  type        = number
  default     = 1
}

variable "cloud_run_min_instances" {
  description = "Minimum Cloud Run instances for the enhancement service"
  type        = number
  default     = 1
}

variable "alert_email" {
  description = "Email address for operational alerts"
  type        = string
  default     = ""
}
