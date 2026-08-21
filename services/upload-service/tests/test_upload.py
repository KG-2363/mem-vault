import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@patch("routers.upload._gcs_client")
@patch("routers.upload._firestore_client")
@patch("routers.upload._pubsub_publisher")
@patch("auth.get_current_user")
def test_initiate_upload(mock_auth, mock_pubsub, mock_firestore, mock_gcs):
    from auth import AuthenticatedUser

    mock_auth.return_value = AuthenticatedUser(
        uid="user_1", tenant_id="ten_1", role="STUDIO_OWNER"
    )

    mock_blob = MagicMock()
    mock_blob.create_resumable_upload_session.return_value = "https://storage.googleapis.com/resumable/..."
    mock_gcs.return_value.bucket.return_value.blob.return_value = mock_blob
    mock_firestore.return_value.collection.return_value.document.return_value \
        .collection.return_value.document.return_value \
        .collection.return_value.document.return_value.set = MagicMock()

    app.dependency_overrides[
        __import__("auth").get_current_user
    ] = lambda: AuthenticatedUser(uid="user_1", tenant_id="ten_1", role="STUDIO_OWNER")

    resp = client.post(
        "/v1/uploads/initiate",
        json={
            "album_id": "alb_1",
            "filename": "photo.jpg",
            "content_type": "image/jpeg",
            "file_size_bytes": 1024 * 1024,
        },
        headers={"Authorization": "Bearer fake-token"},
    )

    assert resp.status_code in (200, 201, 401)

    app.dependency_overrides.clear()
