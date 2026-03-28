from __future__ import annotations

from random import randint
import time

from django.db import close_old_connections


def send_email(external_id: str) -> None:
    close_old_connections()
    delay = randint(5, 20)
    time.sleep(delay)
    print("Send EMAIL...")
