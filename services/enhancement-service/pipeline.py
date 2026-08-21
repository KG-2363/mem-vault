"""
Core enhancement pipeline: download → skin-tone → bg-removal → thumbnails → upload → notify.
"""
import json
import logging
import os
from datetime import datetime, timezone

from google.cloud import firestore, pubsub_v1, storage

from config import settings
from processors.background_removal import remove_background
from processors.skin_tone import correct_skin_tone
from processors.thumbnail import generate_thumbnails

logger = logging.getLogger(__name__)


def _gcs() -> storage.Client:
    if settings.storage_emulator_host:
        os.environ["STORAGE_EMULATOR_HOST"] = settings.storage_emulator_host
    return storage.Client(project=settings.gcp_project_id)


def _db() -> firestore.Client:
    return firestore.Client(
        project=settings.gcp_project_id,
        database=settings.firestore_database,
    )


def _publisher() -> pubsub_v1.PublisherClient:
    if settings.pubsub_emulator_host:
        os.environ["PUBSUB_EMULATOR_HOST"] = settings.pubsub_emulator_host
    return pubsub_v1.PublisherClient()


def _gcs_path_to_bucket_blob(gcs_uri: str) -> tuple[str, str]:
    """Parses gs://bucket/path → (bucket, path)."""
    without_scheme = gcs_uri[5:]
    bucket, _, blob_path = without_scheme.partition("/")
    return bucket, blob_path


def process_photo(event: dict) -> None:
    photo_id = event["photo_id"]
    album_id = event["album_id"]
    tenant_id = event["tenant_id"]
    gcs_raw_path = event["gcs_raw_path"]

    logger.info("Starting enhancement for photo_id=%s", photo_id)

    db = _db()
    photo_ref = (
        db.collection("tenants")
        .document(tenant_id)
        .collection("albums")
        .document(album_id)
        .collection("photos")
        .document(photo_id)
    )
    photo_ref.update({"status": "PROCESSING"})

    gcs = _gcs()
    src_bucket_name, src_blob_path = _gcs_path_to_bucket_blob(gcs_raw_path)
    image_bytes = gcs.bucket(src_bucket_name).blob(src_blob_path).download_as_bytes()

    # Step 1: Skin-tone correction
    if settings.enable_skin_tone_correction:
        image_bytes = correct_skin_tone(image_bytes)

    # Step 2: Background removal
    if settings.enable_background_removal:
        image_bytes = remove_background(image_bytes)

    # Step 3: Upload enhanced photo
    enhanced_path = f"{tenant_id}/{album_id}/enhanced/{photo_id}.jpg"
    bucket = gcs.bucket(settings.gcs_bucket_name)
    bucket.blob(enhanced_path).upload_from_string(image_bytes, content_type="image/jpeg")
    gcs_enhanced_uri = f"gs://{settings.gcs_bucket_name}/{enhanced_path}"

    # Step 4: Generate and upload thumbnails
    thumb_uris: dict[str, str] = {}
    for size_px, webp_bytes in generate_thumbnails(image_bytes, settings.thumb_size_list):
        thumb_path = f"{tenant_id}/{album_id}/thumbs/{photo_id}_{size_px}.webp"
        bucket.blob(thumb_path).upload_from_string(webp_bytes, content_type="image/webp")
        thumb_uris[f"gcs_thumb_{size_px}"] = f"gs://{settings.gcs_bucket_name}/{thumb_path}"

    # Step 5: Update Firestore
    now = datetime.now(timezone.utc).isoformat()
    photo_ref.update(
        {
            "status": "ENHANCED",
            "gcs_enhanced_path": gcs_enhanced_uri,
            "enhanced_at": now,
            **thumb_uris,
        }
    )

    # Step 6: Publish photo.enhanced event
    publisher = _publisher()
    topic_path = publisher.topic_path(settings.gcp_project_id, settings.pubsub_enhance_topic)
    publisher.publish(
        topic_path,
        json.dumps(
            {
                "event_type": "photo.enhanced",
                "photo_id": photo_id,
                "album_id": album_id,
                "tenant_id": tenant_id,
                "gcs_enhanced_path": gcs_enhanced_uri,
                **thumb_uris,
                "enhanced_at": now,
            }
        ).encode(),
    )
    logger.info("Enhancement complete for photo_id=%s", photo_id)


def process_photo_safe(event: dict) -> None:
    """Wraps process_photo and updates Firestore status to FAILED on any exception."""
    try:
        process_photo(event)
    except Exception as exc:
        logger.exception("Enhancement failed for photo_id=%s: %s", event.get("photo_id"), exc)
        try:
            db = _db()
            photo_ref = (
                db.collection("tenants")
                .document(event["tenant_id"])
                .collection("albums")
                .document(event["album_id"])
                .collection("photos")
                .document(event["photo_id"])
            )
            photo_ref.update({"status": "FAILED"})
        except Exception:
            pass
        raise
