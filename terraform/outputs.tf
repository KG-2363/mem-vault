output "gcs_bucket_name" {
  description = "Primary photo storage bucket"
  value       = module.gcs.bucket_name
}

output "gke_cluster_name" {
  description = "GKE Autopilot cluster name"
  value       = module.gke.cluster_name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster API server endpoint"
  value       = module.gke.endpoint
  sensitive   = true
}

output "pubsub_upload_topic" {
  description = "Pub/Sub topic for photo upload events"
  value       = module.pubsub.upload_topic_id
}

output "pubsub_enhance_topic" {
  description = "Pub/Sub topic for photo enhancement events"
  value       = module.pubsub.enhance_topic_id
}

output "bigquery_dataset" {
  description = "BigQuery analytics dataset"
  value       = module.bigquery.dataset_id
}

output "artifact_registry_url" {
  description = "Docker image registry URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.services.repository_id}"
}

output "upload_service_sa_email" {
  description = "Upload service Workload Identity service account"
  value       = module.iam.upload_service_sa_email
}

output "enhancement_service_sa_email" {
  description = "Enhancement service Workload Identity service account"
  value       = module.iam.enhancement_service_sa_email
}
