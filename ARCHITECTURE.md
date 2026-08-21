# MemVault — System Architecture

## 1. High-Level Component Map

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        GCP Project  (asia-south1)                          │
│                                                                            │
│  ┌──────────┐   resumable    ┌─────────────────┐                          │
│  │  Mobile  │──────upload───▶│  Upload Service  │──▶ GCS bucket           │
│  │  Web     │               │  (GKE Autopilot) │    tenant/album/raw/     │
│  └──────────┘               └────────┬─────────┘                          │
│                                      │ Pub/Sub                             │
│                                      ▼ photo.uploaded                      │
│                             ┌─────────────────────┐                        │
│                             │ Enhancement Service  │                        │
│                             │   (Cloud Run)        │                        │
│                             │  ┌───────────────┐  │                        │
│                             │  │ Vertex AI      │  │  ← skin-tone model    │
│                             │  │ rembg (bg rm)  │  │                        │
│                             │  │ libvips thumbs │  │                        │
│                             │  └───────────────┘  │                        │
│                             └──────────┬──────────┘                        │
│                                        │ writes enhanced photo to GCS      │
│                                        │ publishes photo.enhanced           │
│                                        ▼                                   │
│                              ┌──────────────────┐                          │
│                              │    Firestore      │◀── Pub/Sub push sub     │
│                              │  (per-tenant DB)  │                          │
│                              └────────┬─────────┘                          │
│                                       │ real-time listener                 │
│                                       ▼                                    │
│                             ┌──────────────────────┐                       │
│                             │   Delivery Portal     │                       │
│                             │   (Next.js / CDN)     │                       │
│                             └──────────────────────┘                       │
│                                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                     Pub/Sub → BigQuery Streaming                      │ │
│  │   All events ──▶ analytics.events table ──▶ dbt models ──▶ Looker   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Service Responsibilities

### 2.1 Upload Service
- **Language / Runtime**: Python 3.11 + FastAPI on GKE Autopilot
- **Upload flow**: Initiates a GCS resumable upload session and returns the signed resumable URI to the client. The client streams bytes directly to GCS — the service never proxies the binary payload.
- **Storage layout**: `gs://{bucket}/{tenant_id}/{album_id}/raw/{photo_id}.{ext}`
- **On completion**: Writes a metadata record to Firestore and publishes `photo.uploaded` to Pub/Sub.
- **Auth**: Validates Firebase ID token; extracts `tenant_id` and `role` from custom claims.

### 2.2 Enhancement Service
- **Language / Runtime**: Python 3.11 on Cloud Run (GPU tier for Vertex AI calls)
- **Trigger**: Pub/Sub push subscription on `photo.uploaded` topic.
- **Pipeline** (sequential):
  1. Download raw photo from GCS.
  2. Call Vertex AI endpoint for India skin-tone correction (custom model).
  3. Run `rembg` for background removal (optional, per album config).
  4. Generate thumbnails (256px, 1024px) via `pyvips`.
  5. Upload all outputs to `gs://{bucket}/{tenant_id}/{album_id}/enhanced/` and `…/thumbs/`.
  6. Update Firestore document status → `ENHANCED`.
  7. Publish `photo.enhanced` event.
- **Idempotency**: Uses `photo_id` as deduplication key on the Pub/Sub subscription.

### 2.3 Delivery Service
- **Language / Runtime**: Python 3.11 + FastAPI on GKE Autopilot
- **Responsibility**: Issues short-lived GCS signed URLs (15 min TTL) for enhanced photos and thumbnails.
- **Access control**: Verifies that the requesting user's `tenant_id` matches the photo's tenant before signing.

### 2.4 Auth Service
- **Language / Runtime**: Python 3.11 + FastAPI on GKE Autopilot
- **Responsibility**: Firebase Admin SDK wrapper that sets custom JWT claims (`tenant_id`, `role`) after identity verification and tenant look-up.
- **Roles**: `STUDIO_OWNER`, `STUDIO_STAFF`, `INSTITUTION_ADMIN`, `CLIENT`, `B2B_API`

### 2.5 B2B API Service
- **Language / Runtime**: Python 3.11, FastAPI (REST) + `grpc` (gRPC) on GKE Autopilot
- **Surfaces**:
  - REST `POST /v1/enhance` — single photo enhancement, synchronous response with GCS URI.
  - gRPC `EnhancementService.EnhanceBatch` — batch streaming enhancement.
- **Rate limiting**: Per-API-key quotas enforced by GCP API Gateway (quota extension).
- **Auth**: API key via `x-api-key` header validated against Secret Manager entries.

---

## 3. Data Model

### Firestore Document: `tenants/{tenant_id}/albums/{album_id}/photos/{photo_id}`

```jsonc
{
  "photo_id": "ph_01J...",
  "album_id": "alb_01J...",
  "tenant_id": "ten_01J...",
  "original_filename": "IMG_1234.jpg",
  "status": "UPLOADED | PROCESSING | ENHANCED | FAILED",
  "gcs_raw_path": "gs://memvault-photos/ten_.../alb_.../raw/ph_....jpg",
  "gcs_enhanced_path": "gs://memvault-photos/ten_.../alb_.../enhanced/ph_....jpg",
  "gcs_thumb_256": "gs://memvault-photos/ten_.../alb_.../thumbs/ph_..._256.webp",
  "gcs_thumb_1024": "gs://memvault-photos/ten_.../alb_.../thumbs/ph_..._1024.webp",
  "uploaded_at": "2026-06-26T10:00:00Z",
  "enhanced_at": null,
  "face_tags": [],        // institution portal only
  "cohort_id": null       // institution portal only
}
```

### GCS Bucket Layout

```
memvault-photos-{project}/
  {tenant_id}/
    {album_id}/
      raw/          ← original uploads
      enhanced/     ← AI-processed output
      thumbs/       ← 256px and 1024px WebP thumbnails
```

### BigQuery Dataset: `analytics`

| Table | Source | Purpose |
|---|---|---|
| `events_raw` | Pub/Sub streaming | All application events (append-only) |
| `stg_uploads` | dbt staging | Cleaned upload events |
| `stg_enhancements` | dbt staging | Enhancement completion events |
| `fct_photo_events` | dbt mart | Fact table: photo lifecycle |
| `dim_tenants` | dbt mart | Tenant dimension |

---

## 4. Pub/Sub Topics & Subscriptions

| Topic | Publisher | Subscribers |
|---|---|---|
| `photo.uploaded` | Upload Service | Enhancement Service (push), BigQuery Sink (pull) |
| `photo.enhanced` | Enhancement Service | Firestore updater (push), BigQuery Sink (pull) |
| `photo.failed` | Enhancement Service | Alert sink, BigQuery Sink |

---

## 5. Infrastructure (Terraform)

| Resource | Config |
|---|---|
| GCS Bucket | `asia-south1`, uniform bucket-level access, versioning on, DPDP retention lock |
| GKE Autopilot | `asia-south1`, Workload Identity, private cluster |
| Firestore | Native mode, `(asia-south1)` multi-region |
| Cloud Run | `asia-south1`, min-instances=1, concurrency=8 |
| Cloud Armor | OWASP CRS v3, custom rate-limit rules |
| Istio (in-cluster) | mTLS STRICT between all pods |
| Secret Manager | One secret per service per environment |
| API Gateway | Per-key quota plans, OpenAPI 3.0 spec |
| BigQuery | Dataset in `asia-south1`, CMEK via Cloud KMS |

---

## 6. Security & Compliance

- **DPDP Act 2023**: Data residency enforced at org-policy level (`constraints/gcp.resourceLocations` → `asia-south1`).
- **Encryption**: All GCS objects and BigQuery tables use CMEK (`asia-south1` KMS key ring).
- **mTLS**: Istio enforces STRICT mTLS between all GKE services.
- **WAF**: Cloud Armor with OWASP CRS v3 in front of the GKE Ingress.
- **Secrets**: No secrets in environment variables — all read from Secret Manager at pod startup via Workload Identity.
- **Audit Logs**: `cloudaudit.googleapis.com/data_access` enabled for GCS, Firestore, and BigQuery.
- **Right to Erasure**: `DELETE /v1/tenants/{tenant_id}/photos/{photo_id}` triggers GCS object deletion and Firestore document deletion, logged to BigQuery.

---

## 7. Local Development

Uses Docker Compose to run the upload service, a GCS emulator (fake-gcs-server), a Pub/Sub emulator, and a Firestore emulator. The studio portal points at `localhost` service endpoints.

```
docker compose up
```
