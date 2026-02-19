from celery import Celery
from app.config import settings

celery = Celery(
    "exam_ai_pipeline",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery.conf.update(
    task_routes={"app.workers.tasks.*": {"queue": "default"}},
    task_track_started=True,
)
