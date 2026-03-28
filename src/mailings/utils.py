from __future__ import annotations

from typing import Tuple, Dict
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
import time
import random


def validate_row(row: Dict[str, str]) -> Tuple[bool, str]:
    if not row.get("external_id", "").strip():
        return False, "external_id пустой."
    if not str(row.get("user_id", "")).isdigit():
        return False, "user_id должен быть числом."
    if not row.get("email", "").strip():
        return False, "email пустой."
    try:
        validate_email(row["email"])
    except Exception:
        return False, "email некорректен."
    if not row.get("subject", "").strip():
        return False, "subject пустой."
    if not row.get("message", "").strip():
        return False, "message пустой."
    return True, ""


def send_email(to_email: str, subject: str, message: str) -> None:
    time.sleep(random.randint(5, 20))
    print("Send EMAIL...")
