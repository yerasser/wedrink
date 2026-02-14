from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "wedrink",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.ocr_tasks"]
)

celery_app.conf.task_routes = {
    "app.tasks.ocr_tasks.ocr_process_receipt": {"queue": "ocr"},
}
celery_app.conf.task_default_queue = "default"
