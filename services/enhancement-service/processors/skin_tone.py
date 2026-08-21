"""
Calls a Vertex AI custom endpoint trained for India skin-tone correction.
The model accepts a base64-encoded JPEG and returns a corrected JPEG.
"""
import base64
import os

from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

from config import settings


def correct_skin_tone(image_bytes: bytes) -> bytes:
    if not settings.vertex_ai_endpoint:
        return image_bytes

    aiplatform.init(project=settings.gcp_project_id, location=settings.vertex_ai_location)

    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    instance = json_format.ParseDict({"image_bytes": {"b64": b64_image}}, Value())

    endpoint = aiplatform.Endpoint(settings.vertex_ai_endpoint)
    response = endpoint.predict(instances=[instance])

    corrected_b64 = response.predictions[0]["image_bytes"]["b64"]
    return base64.b64decode(corrected_b64)
