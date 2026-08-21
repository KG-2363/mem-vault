"""
Auth Service — sets custom JWT claims (tenant_id, role) on Firebase users.
Called once after registration/invitation before the user's first token refresh.
"""
import os
from enum import Enum

import firebase_admin
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth, credentials
from google.cloud import firestore
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gcp_project_id: str
    firestore_database: str = "(default)"
    firebase_admin_sdk_json: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
app = FastAPI(title="MemVault Auth Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_firebase_app = None


def _init():
    global _firebase_app
    if _firebase_app is None:
        cred = (
            credentials.Certificate(settings.firebase_admin_sdk_json)
            if settings.firebase_admin_sdk_json
            else credentials.ApplicationDefault()
        )
        _firebase_app = firebase_admin.initialize_app(cred)


class Role(str, Enum):
    STUDIO_OWNER = "STUDIO_OWNER"
    STUDIO_STAFF = "STUDIO_STAFF"
    INSTITUTION_ADMIN = "INSTITUTION_ADMIN"
    CLIENT = "CLIENT"
    B2B_API = "B2B_API"


class SetClaimsRequest(BaseModel):
    uid: str
    tenant_id: str
    role: Role


class TenantProvisionRequest(BaseModel):
    tenant_name: str
    owner_uid: str
    plan: str = "starter"


_bearer = HTTPBearer()


async def require_service_token(creds: HTTPAuthorizationCredentials = Depends(_bearer)):
    """Only internal services or a super-admin can call this endpoint."""
    _init()
    try:
        decoded = firebase_auth.verify_id_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if decoded.get("role") not in ("SUPER_ADMIN", "SERVICE"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return decoded


@app.post("/v1/auth/set-claims", status_code=status.HTTP_200_OK)
async def set_claims(
    body: SetClaimsRequest,
    _: dict = Depends(require_service_token),
) -> dict:
    _init()
    firebase_auth.set_custom_user_claims(
        body.uid,
        {"tenant_id": body.tenant_id, "role": body.role.value},
    )
    return {"uid": body.uid, "tenant_id": body.tenant_id, "role": body.role}


@app.post("/v1/tenants", status_code=status.HTTP_201_CREATED)
async def provision_tenant(
    body: TenantProvisionRequest,
    _: dict = Depends(require_service_token),
) -> dict:
    """Creates a tenant document in Firestore and sets STUDIO_OWNER claims on the owner."""
    _init()
    import ulid

    tenant_id = f"ten_{ulid.new()}"

    db = firestore.Client(project=settings.gcp_project_id, database=settings.firestore_database)
    db.collection("tenants").document(tenant_id).set(
        {
            "tenant_id": tenant_id,
            "name": body.tenant_name,
            "plan": body.plan,
            "owner_uid": body.owner_uid,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )

    firebase_auth.set_custom_user_claims(
        body.owner_uid,
        {"tenant_id": tenant_id, "role": Role.STUDIO_OWNER.value},
    )

    return {"tenant_id": tenant_id}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
