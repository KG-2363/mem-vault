from enum import Enum
from pydantic import BaseModel


class PhotoStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    ENHANCED = "ENHANCED"
    FAILED = "FAILED"


class InitiateUploadRequest(BaseModel):
    album_id: str
    filename: str
    content_type: str
    file_size_bytes: int


class InitiateUploadResponse(BaseModel):
    photo_id: str
    resumable_uri: str
    gcs_path: str


class UploadCompleteRequest(BaseModel):
    photo_id: str
    album_id: str


class PhotoMetadata(BaseModel):
    photo_id: str
    album_id: str
    tenant_id: str
    original_filename: str
    status: PhotoStatus
    gcs_raw_path: str
    gcs_enhanced_path: str | None = None
    gcs_thumb_256: str | None = None
    gcs_thumb_1024: str | None = None
