variable "project_id" { type = string }
variable "region"     { type = string }

resource "google_api_gateway_api" "b2b" {
  provider = google-beta
  api_id   = "memvault-b2b-api"
}

resource "google_api_gateway_api_config" "b2b" {
  provider      = google-beta
  api           = google_api_gateway_api.b2b.api_id
  api_config_id = "memvault-b2b-config-v1"

  openapi_documents {
    document {
      path     = "spec.yaml"
      contents = base64encode(file("${path.module}/openapi.yaml"))
    }
  }

  gateway_config {
    backend_config {
      google_service_account = ""
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_api_gateway_gateway" "b2b" {
  provider   = google-beta
  api_config = google_api_gateway_api_config.b2b.id
  gateway_id = "memvault-b2b-gateway"
  region     = var.region
}

output "gateway_default_hostname" {
  value = google_api_gateway_gateway.b2b.default_hostname
}
