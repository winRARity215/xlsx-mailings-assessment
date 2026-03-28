from __future__ import annotations

from celery import shared_task

from .emailer import send_email


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def send_email_task(self, external_id: str) -> None:
    send_email(external_id)
