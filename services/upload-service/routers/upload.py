import json
import os
from datetime import datetime, timezone

import ulid as _ulid

def _new_id() -> str:
    return str(_ulid.new())
from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud import firestore, pubsub_v1, storage

from auth import AuthenticatedUser, get_current_user
from config import settings
from models import (
    InitiateUploadRequest,
    InitiateUploadResponse,
    PhotoMetadata,
    PhotoStatus,
    UploadCompleteRequest,
)

router = APIRouter(prefix="/v1/uploads", tags=["uploads"])


def _gcs_client() -> storage.Client:
    if settings.storage_emulator_host:
        os.environ["STORAGE_EMULATOR_HOST"] = settings.storage_emulator_host
    return storage.Client(project=settings.gcp_project_id)


def _firestore_client() -> firestore.Client:
    return firestore.Client(
        project=settings.gcp_project_id,
        database=settings.firestore_database,
    )


def _pubsub_publisher() -> pubsub_v1.PublisherClient:
    if settings.pubsub_emulator_host:
        os.environ["PUBSUB_EMULATOR_HOST"] = settings.pubsub_emulator_host
    return pubsub_v1.PublisherClient()


@router.post("/initiate", response_model=InitiateUploadResponse, status_code=status.HTTP_201_CREATED)
async def initiate_upload(
    body: InitiateUploadRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> InitiateUploadResponse:
    """
    Returns a GCS resumable upload URI. The client streams bytes directly
    to GCS — this service never proxies the binary payload.
    """
    photo_id = f"ph_{_new_id()}"
    ext = body.filename.rsplit(".", 1)[-1].lower() if "." in body.filename else "jpg"
    gcs_path = f"{user.tenant_id}/{body.album_id}/raw/{photo_id}.{ext}"

    gcs = _gcs_client()
    bucket = gcs.bucket(settings.gcs_bucket_name)
    blob = bucket.blob(gcs_path)

    resumable_uri = blob.create_resumable_upload_session(
        content_type=body.content_type,
        size=body.file_size_bytes,
        origin="*",
    )

    db = _firestore_client()
    doc_ref = (
        db.collection("tenants")
        .document(user.tenant_id)
        .collection("albums")
        .document(body.album_id)
        .collection("photos")
        .document(photo_id)
    )
    doc_ref.set(
        PhotoMetadata(
            photo_id=photo_id,
            album_id=body.album_id,
            tenant_id=user.tenant_id,
            original_filename=body.filename,
            status=PhotoStatus.UPLOADED,
            gcs_raw_path=f"gs://{settings.gcs_bucket_name}/{gcs_path}",
        ).model_dump()
    )

    return InitiateUploadResponse(
        photo_id=photo_id,
        resumable_uri=resumable_uri,
        gcs_path=f"gs://{settings.gcs_bucket_name}/{gcs_path}",
    )


@router.post("/complete", status_code=status.HTTP_200_OK)
async def complete_upload(
    body: UploadCompleteRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """
    Called by the client after the resumable upload to GCS finishes.
    Publishes the photo.uploaded Pub/Sub event to trigger the enhancement pipeline.
    """
    db = _firestore_client()
    doc_ref = (
        db.collection("tenants")
        .document(user.tenant_id)
        .collection("albums")
        .document(body.album_id)
        .collection("photos")
        .document(body.photo_id)
    )
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    photo = doc.to_dict()

    publisher = _pubsub_publisher()
    topic_path = publisher.topic_path(settings.gcp_project_id, settings.pubsub_upload_topic)

    event = {
        "event_type": "photo.uploaded",
        "photo_id": body.photo_id,
        "album_id": body.album_id,
        "tenant_id": user.tenant_id,
        "gcs_raw_path": photo["gcs_raw_path"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    publisher.publish(topic_path, json.dumps(event).encode())

    return {"status": "queued", "photo_id": body.photo_id}


@router.get("/{album_id}/photos", response_model=list[PhotoMetadata])
async def list_album_photos(
    album_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> list[PhotoMetadata]:
    db = _firestore_client()
    docs = (
        db.collection("tenants")
        .document(user.tenant_id)
        .collection("albums")
        .document(album_id)
        .collection("photos")
        .stream()
    )
    return [PhotoMetadata(**doc.to_dict()) for doc in docs]
