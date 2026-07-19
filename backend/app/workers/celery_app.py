from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery("sentinelx", broker=settings.celery_broker_url, backend=settings.celery_result_backend)
celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "certificate-expiry-sweep": {
        "task": "app.workers.tasks.sweep_certificate_expiry",
        "schedule": crontab(minute="*/30"),
    },
}
celery_app.autodiscover_tasks(["app.workers"])
