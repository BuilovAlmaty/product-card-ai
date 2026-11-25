from celery import Celery

from app.core.config import Settings

settings = Settings()

celery_app = Celery(
    "card",
    broker=settings.rabbitmq_url,
    backend=None,
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue="card.generate",
    worker_prefetch_multiplier=1,
)

import app.workers.tasks