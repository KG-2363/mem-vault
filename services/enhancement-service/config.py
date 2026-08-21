from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gcp_project_id: str
    gcs_bucket_name: str
    pubsub_upload_topic: str = "photo.uploaded"
    pubsub_enhance_topic: str = "photo.enhanced"
    pubsub_failed_topic: str = "photo.failed"
    pubsub_subscription: str = "photo-uploaded-enhancement-sub"
    firestore_database: str = "(default)"
    vertex_ai_endpoint: str = ""
    vertex_ai_location: str = "asia-south1"
    enable_skin_tone_correction: bool = True
    enable_background_removal: bool = False
    thumb_sizes: str = "256,1024"
    pubsub_emulator_host: str = ""
    firestore_emulator_host: str = ""
    storage_emulator_host: str = ""

    @property
    def thumb_size_list(self) -> list[int]:
        return [int(s) for s in self.thumb_sizes.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
