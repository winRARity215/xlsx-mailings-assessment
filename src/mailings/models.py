from __future__ import annotations

from django.conf import settings
from django.db import models


class OutgoingEmail(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING"
        SENT = "SENT"
        ERROR = "ERROR"

    external_id = models.CharField(max_length=128, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="outgoing_emails")
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
