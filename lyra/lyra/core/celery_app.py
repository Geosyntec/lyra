import os

from celery import Celery
from celery.schedules import crontab

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery("tasks", backend=CELERY_RESULT_BACKEND, broker=CELERY_BROKER_URL)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],  # Ignore other content
    result_serializer="json",
)

celery_app.conf.beat_schedule = {
    "add-every-3-mins": {
        "task": "lyra.bg_worker.add",
        "schedule": 3 * 60,
        "args": (16, 16),
    },
    "update-static-references": {
        "task": "lyra.bg_worker.background_build_static_references",
        "schedule": crontab(minute="*/5"),
    },
}
celery_app.conf.timezone = "UTC"
