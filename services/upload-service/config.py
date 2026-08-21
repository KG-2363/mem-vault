from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gcp_project_id: str
    gcs_bucket_name: str
    gcs_signed_url_ttl_seconds: int = 900
    pubsub_upload_topic: str = "photo.uploaded"
    firestore_database: str = "(default)"
    storage_emulator_host: str = ""
    pubsub_emulator_host: str = ""
    firestore_emulator_host: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
