"""
Enhancement service entry point.
Pulls messages from Pub/Sub and runs the photo enhancement pipeline.
Runs as a long-lived process in Cloud Run (min-instances=1).
"""
import json
import logging
import os
import signal
import sys

from google.cloud import pubsub_v1

from config import settings
from pipeline import process_photo_safe

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

_running = True


def _shutdown(signum, frame):
    global _running
    logger.info("Received shutdown signal, draining...")
    _running = False


signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)


def main() -> None:
    if settings.pubsub_emulator_host:
        os.environ["PUBSUB_EMULATOR_HOST"] = settings.pubsub_emulator_host

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        settings.gcp_project_id, settings.pubsub_subscription
    )

    logger.info("Listening on subscription: %s", subscription_path)

    def callback(message: pubsub_v1.subscriber.message.Message) -> None:
        try:
            event = json.loads(message.data.decode())
            process_photo_safe(event)
            message.ack()
        except Exception as exc:
            logger.error("Nacking message due to error: %s", exc)
            message.nack()

    streaming_pull = subscriber.subscribe(subscription_path, callback=callback)

    try:
        streaming_pull.result()
    except Exception as exc:
        logger.error("Streaming pull error: %s", exc)
        streaming_pull.cancel()
        sys.exit(1)


if __name__ == "__main__":
    main()
