#!/usr/bin/env python3
"""
Seeds a local Firestore emulator with a test tenant, album, and sample photos
so the studio portal has data to display immediately.

Usage: python scripts/seed_data.py
"""

import os
import random
from datetime import datetime, timezone

os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8080")

from google.cloud import firestore  # noqa: E402

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "demo-project")
db = firestore.Client(project=PROJECT_ID)

TENANT_ID = "ten_01SEED000000000000000000"
ALBUM_ID = "alb_01SEED000000000000000001"

STATUSES = ["UPLOADED", "PROCESSING", "ENHANCED", "ENHANCED", "ENHANCED"]


def seed():
    # Tenant
    db.collection("tenants").document(TENANT_ID).set(
        {
            "tenant_id": TENANT_ID,
            "name": "Demo Studio",
            "plan": "starter",
            "owner_uid": "uid_seed_owner",
            "created_at": datetime.now(timezone.utc),
        }
    )
    print(f"Created tenant: {TENANT_ID}")

    # Album
    db.collection("tenants").document(TENANT_ID).collection("albums").document(ALBUM_ID).set(
        {
            "album_id": ALBUM_ID,
            "name": "Sample Wedding — 2026",
            "photo_count": 0,
            "created_at": datetime.now(timezone.utc),
        }
    )
    print(f"Created album: {ALBUM_ID}")

    # Photos
    for i in range(12):
        photo_id = f"ph_SEED{i:022d}"
        status = random.choice(STATUSES)
        doc = {
            "photo_id": photo_id,
            "album_id": ALBUM_ID,
            "tenant_id": TENANT_ID,
            "original_filename": f"photo_{i:04d}.jpg",
            "status": status,
            "gcs_raw_path": f"gs://memvault-local/{TENANT_ID}/{ALBUM_ID}/raw/{photo_id}.jpg",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        if status == "ENHANCED":
            doc["gcs_enhanced_path"] = (
                f"gs://memvault-local/{TENANT_ID}/{ALBUM_ID}/enhanced/{photo_id}.jpg"
            )
            doc["gcs_thumb_256"] = (
                f"gs://memvault-local/{TENANT_ID}/{ALBUM_ID}/thumbs/{photo_id}_256.webp"
            )
            doc["gcs_thumb_1024"] = (
                f"gs://memvault-local/{TENANT_ID}/{ALBUM_ID}/thumbs/{photo_id}_1024.webp"
            )
            doc["enhanced_at"] = datetime.now(timezone.utc).isoformat()

        (
            db.collection("tenants")
            .document(TENANT_ID)
            .collection("albums")
            .document(ALBUM_ID)
            .collection("photos")
            .document(photo_id)
            .set(doc)
        )

    print(f"Created 12 seed photos in album {ALBUM_ID}")
    print("")
    print("Seed complete. Use these IDs in the portal:")
    print(f"  tenant_id = {TENANT_ID}")
    print(f"  album_id  = {ALBUM_ID}")


if __name__ == "__main__":
    seed()
