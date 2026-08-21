# MemVault

Multi-tenant photo storage, AI-enhancement, and delivery SaaS built on Google Cloud Platform.

---

## Overview

MemVault lets studios, schools, and enterprises upload photos, run AI enhancements (skin-tone correction, background removal, thumbnail generation), and deliver processed images to clients in real time — all within India's data-residency boundary (`asia-south1`).

### Tenancy Model

| Portal | Who Uses It | Key Capability |
|---|---|---|
| Studio Portal | Photographers, studios | Upload, manage albums, deliver to clients |
| Institution Portal | Schools, colleges | Face-tagging, cohort album search |
| B2B API | Vehicle & real-estate companies | REST + gRPC batch enhancement |

---

## Architecture at a Glance

```
Mobile/Web
    │
    ▼
[Upload Service] ──GCS──▶ {tenant/album/raw/photo.jpg}
    │
    └── Pub/Sub (photo.uploaded) ──▶ [Enhancement Service (Cloud Run)]
                                          ├── Vertex AI skin-tone
                                          ├── rembg background removal
                                          └── libvips thumbnails
                                          │
                                          └── Pub/Sub (photo.enhanced) ──▶ Firestore
                                                                               │
                                                                          [Delivery Portal]
                                                                           (Next.js + Firestore listener)
```

Full design: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Phase Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Upload → Store → Deliver loop | 🔨 Active |
| 2 | AI Enhancement Pipeline (Vertex AI, rembg, libvips) | Planned |
| 3 | Firebase Auth + custom JWT claims | Planned |
| 4 | Studio Portal (white-label) | Planned |
| 5 | Institution Portal (face-tagging, cohort search) | Planned |
| 6 | B2B REST + gRPC API with rate limiting | Planned |
| 7 | BigQuery + dbt analytics pipeline | Planned |
| 8 | Full Terraform (GKE Autopilot, Istio, Cloud Armor) | Planned |

---

## Repository Layout

```
mem-vault/
├── services/
│   ├── upload-service/       # FastAPI — resumable GCS uploads
│   ├── enhancement-service/  # Cloud Run — AI pipeline consumer
│   ├── delivery-service/     # FastAPI — signed-URL delivery
│   ├── auth-service/         # Firebase custom claims
│   └── api-service/          # B2B REST + gRPC
├── portals/
│   ├── studio-portal/        # Next.js 14 — white-label studio
│   └── institution-portal/   # Next.js 14 — schools/colleges
├── pipelines/
│   ├── dbt/                  # BigQuery transformation models
│   └── pubsub/               # Event schemas
├── terraform/                # All GCP infrastructure
├── k8s/                      # Kustomize overlays for GKE
└── scripts/                  # Bootstrap, deploy, seed
```

---

## Prerequisites

| Tool | Minimum Version |
|---|---|
| Google Cloud SDK (`gcloud`) | 460+ |
| Terraform | 1.7+ |
| Docker | 24+ |
| Node.js | 20 LTS |
| Python | 3.11+ |
| `kubectl` | 1.28+ |
| `skaffold` | 2.9+ |

---

## Quick Start (Local Development)

```bash
# 1. Clone and configure
cp .env.example .env
# Fill in GCP_PROJECT_ID, TENANT_ID, etc.

# 2. Start all services locally (Docker Compose)
make dev

# 3. Seed a test tenant and album
make seed

# 4. Open the studio portal
open http://localhost:3000
```

---

## Bootstrap a New GCP Project

```bash
# Authenticate
gcloud auth login
gcloud auth application-default login

# Run one-time project bootstrap (creates APIs, SA, initial buckets)
./scripts/bootstrap.sh --project YOUR_PROJECT_ID --region asia-south1

# Deploy infrastructure via Terraform
cd terraform
terraform init
terraform plan -var="project_id=YOUR_PROJECT_ID"
terraform apply
```

---

## Environment Variables

See [.env.example](.env.example) for the full list. Critical variables:

| Variable | Description |
|---|---|
| `GCP_PROJECT_ID` | GCP project ID |
| `GCS_BUCKET_NAME` | Primary photo storage bucket |
| `PUBSUB_UPLOAD_TOPIC` | Topic for upload events |
| `PUBSUB_ENHANCE_TOPIC` | Topic for enhancement events |
| `FIREBASE_PROJECT_ID` | Firebase project (usually same as GCP) |
| `VERTEX_AI_ENDPOINT` | Vertex AI model endpoint ID |

---

## DPDP Act 2023 Compliance

- All GCS buckets, Firestore databases, BigQuery datasets, and GKE clusters are pinned to `asia-south1`.
- No photo data is written outside India.
- PII fields in BigQuery are column-level encrypted with Cloud KMS keys in `asia-south1`.
- Data-deletion webhooks are provided for the right-to-erasure workflow.

---

## Contributing

1. Branch from `main`: `git checkout -b feat/your-feature`
2. Run `make lint` and `make test` before pushing.
3. PR title must follow: `feat:`, `fix:`, `chore:`, `docs:`.
