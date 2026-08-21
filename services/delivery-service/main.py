import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.cloud import firestore, storage
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials


class Settings(BaseSettings):
    gcp_project_id: str
    gcs_bucket_name: str
    gcs_signed_url_ttl_seconds: int = 900
    firestore_database: str = "(default)"
    storage_emulator_host: str = ""
    firestore_emulator_host: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
app = FastAPI(title="MemVault Delivery Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_firebase_app = None


def _init_firebase():
    global _firebase_app
    if _firebase_app is None:
        sdk_path = os.getenv("FIREBASE_ADMIN_SDK_JSON", "")
        cred = credentials.Certificate(sdk_path) if sdk_path else credentials.ApplicationDefault()
        _firebase_app = firebase_admin.initialize_app(cred)


_bearer = HTTPBearer()


class _User:
    def __init__(self, uid: str, tenant_id: str):
        self.uid = uid
        self.tenant_id = tenant_id


async def get_user(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> _User:
    _init_firebase()
    try:
        decoded = firebase_auth.verify_id_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    tenant_id = decoded.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return _User(uid=decoded["uid"], tenant_id=tenant_id)


class DeliveryURLs(BaseModel):
    photo_id: str
    enhanced_url: str | None
    thumb_256_url: str | None
    thumb_1024_url: str | None
    expires_at: str


def _sign(gcs_uri: str | None, ttl: int) -> str | None:
    if not gcs_uri:
        return None
    if settings.storage_emulator_host:
        return gcs_uri.replace("gs://", f"{settings.storage_emulator_host}/")

    without_scheme = gcs_uri[5:]
    bucket_name, _, blob_path = without_scheme.partition("/")
    gcs = storage.Client(project=settings.gcp_project_id)
    blob = gcs.bucket(bucket_name).blob(blob_path)
    return blob.generate_signed_url(
        expiration=timedelta(seconds=ttl),
        method="GET",
        version="v4",
    )


@app.get("/v1/photos/{tenant_id}/{album_id}/{photo_id}/urls", response_model=DeliveryURLs)
async def get_delivery_urls(
    tenant_id: str,
    album_id: str,
    photo_id: str,
    user: _User = Depends(get_user),
) -> DeliveryURLs:
    if user.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    db = firestore.Client(project=settings.gcp_project_id, database=settings.firestore_database)
    doc = (
        db.collection("tenants")
        .document(tenant_id)
        .collection("albums")
        .document(album_id)
        .collection("photos")
        .document(photo_id)
        .get()
    )
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    photo = doc.to_dict()
    ttl = settings.gcs_signed_url_ttl_seconds
    expires = (datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat()

    return DeliveryURLs(
        photo_id=photo_id,
        enhanced_url=_sign(photo.get("gcs_enhanced_path"), ttl),
        thumb_256_url=_sign(photo.get("gcs_thumb_256"), ttl),
        thumb_1024_url=_sign(photo.get("gcs_thumb_1024"), ttl),
        expires_at=expires,
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
