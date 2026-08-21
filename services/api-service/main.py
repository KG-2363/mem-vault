"""
B2B API Service — REST surface.
The gRPC surface is compiled from proto/enhancement.proto and runs on port 50051.
API key validation reads from Secret Manager (key stored as secret named `b2b-api-key-{key_hash}`).
Rate limiting is enforced upstream by GCP API Gateway quota extension.
"""
import hashlib
import json
import os
import time
from concurrent import futures

import grpc
import ulid
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import pubsub_v1, secretmanager, storage
from pydantic import BaseModel
from pydantic_settings import BaseSettings

# gRPC generated stubs (generated from proto/enhancement.proto)
# Run: python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/enhancement.proto
try:
    import enhancement_pb2
    import enhancement_pb2_grpc
    _GRPC_AVAILABLE = True
except ImportError:
    _GRPC_AVAILABLE = False


class Settings(BaseSettings):
    gcp_project_id: str
    gcs_bucket_name: str
    pubsub_upload_topic: str = "photo.uploaded"
    secret_manager_project: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
app = FastAPI(title="MemVault B2B API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _validate_api_key(request: Request) -> str:
    api_key = request.headers.get("x-api-key", "")
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing x-api-key")

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
    secret_id = f"b2b-api-key-{key_hash}"
    project = settings.secret_manager_project or settings.gcp_project_id

    try:
        sm = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project}/secrets/{secret_id}/versions/latest"
        sm.access_secret_version(request={"name": name})
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    return api_key


class EnhanceRequest(BaseModel):
    source_url: str
    enhancements: list[str]


class EnhanceResponse(BaseModel):
    request_id: str
    job_id: str
    status: str = "QUEUED"


class BatchEnhanceRequest(BaseModel):
    photos: list[EnhanceRequest]


class BatchJobResponse(BaseModel):
    job_id: str
    photo_count: int
    status: str = "ACCEPTED"


@app.post("/v1/enhance", response_model=EnhanceResponse, status_code=status.HTTP_200_OK)
async def enhance_single(
    body: EnhanceRequest,
    _api_key: str = Depends(_validate_api_key),
) -> EnhanceResponse:
    request_id = f"req_{ulid.new()}"
    job_id = f"job_{ulid.new()}"

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(settings.gcp_project_id, settings.pubsub_upload_topic)

    event = {
        "event_type": "b2b.enhance.single",
        "request_id": request_id,
        "job_id": job_id,
        "source_url": body.source_url,
        "enhancements": body.enhancements,
        "tenant_id": "b2b",
    }
    publisher.publish(topic_path, json.dumps(event).encode())

    return EnhanceResponse(request_id=request_id, job_id=job_id)


@app.post("/v1/enhance/batch", response_model=BatchJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def enhance_batch(
    body: BatchEnhanceRequest,
    _api_key: str = Depends(_validate_api_key),
) -> BatchJobResponse:
    job_id = f"job_{ulid.new()}"
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(settings.gcp_project_id, settings.pubsub_upload_topic)

    for photo in body.photos:
        event = {
            "event_type": "b2b.enhance.batch",
            "job_id": job_id,
            "source_url": photo.source_url,
            "enhancements": photo.enhancements,
            "tenant_id": "b2b",
        }
        publisher.publish(topic_path, json.dumps(event).encode())

    return BatchJobResponse(job_id=job_id, photo_count=len(body.photos))


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "grpc_available": _GRPC_AVAILABLE}


# ── gRPC server (runs on port 50051 alongside FastAPI on 8000) ────────────────

if _GRPC_AVAILABLE:
    class EnhancementServicer(enhancement_pb2_grpc.EnhancementServiceServicer):
        def EnhanceSingle(self, request, context):
            start = time.monotonic()
            # Delegate to the same Pub/Sub pipeline as the REST endpoint
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(
                settings.gcp_project_id, settings.pubsub_upload_topic
            )
            event = {
                "event_type": "b2b.enhance.single",
                "request_id": request.request_id,
                "source_url": request.source_url,
                "enhancements": list(request.enhancements),
                "tenant_id": "b2b",
            }
            publisher.publish(topic_path, json.dumps(event).encode())

            return enhancement_pb2.EnhanceResponse(
                request_id=request.request_id,
                processing_time_ms=int((time.monotonic() - start) * 1000),
            )

        def EnhanceBatch(self, request_iterator, context):
            for req in request_iterator:
                yield self.EnhanceSingle(req, context)

    def start_grpc_server() -> None:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
        enhancement_pb2_grpc.add_EnhancementServiceServicer_to_server(
            EnhancementServicer(), server
        )
        server.add_insecure_port("[::]:50051")
        server.start()
        server.wait_for_termination()
