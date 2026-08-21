import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    def __init__(self, uid: str, tenant_id: str, role: str):
        self.uid = uid
        self.tenant_id = tenant_id
        self.role = role


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthenticatedUser:
    # Local dev bypass — never enabled outside Docker Compose dev env
    if os.getenv("DEV_SKIP_AUTH", "").lower() == "true":
        return AuthenticatedUser(
            uid=os.getenv("DEV_USER_ID", "dev-uid"),
            tenant_id=os.getenv("DEV_TENANT_ID", "ten_dev"),
            role=os.getenv("DEV_ROLE", "STUDIO_OWNER"),
        )

    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    import firebase_admin
    from firebase_admin import auth as firebase_auth, credentials

    global _firebase_app
    try:
        _firebase_app
    except NameError:
        _firebase_app = None

    if _firebase_app is None:
        sdk_path = os.getenv("FIREBASE_ADMIN_SDK_JSON", "")
        cred = credentials.Certificate(sdk_path) if sdk_path else credentials.ApplicationDefault()
        _firebase_app = firebase_admin.initialize_app(cred)

    try:
        decoded = firebase_auth.verify_id_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    tenant_id = decoded.get("tenant_id")
    role = decoded.get("role", "CLIENT")
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tenant claim")

    return AuthenticatedUser(uid=decoded["uid"], tenant_id=tenant_id, role=role)
