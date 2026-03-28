from __future__ import annotations

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from mailings.models import OutgoingEmail


class ImportMailingsCommandTests(TestCase):
    
    def test_import_creates_and_skips_by_external_id(self) -> None:
        try:
            import openpyxl
        except ImportError:
            self.skipTest("Не установлен openpyxl.")

        User = get_user_model()
        user = User.objects.create_user(username="u1", password="x")

        OutgoingEmail.objects.create(
            external_id="ext-1",
            user=user,
            email="a@example.com",
            subject="S",
            message="M",
        )

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["external_id", "user_id", "email", "subject", "message"])
        ws.append(["ext-1", str(user.id), "a@example.com", "S", "M"])
        ws.append(["ext-2", str(user.id), "b@example.com", "S2", "M2"])
        ws.append(["ext-3", str(user.id), "c@example.com", "S3", "M3"])

        with TemporaryDirectory() as td:
            xlsx_path = Path(td) / "mailings.xlsx"
            wb.save(xlsx_path)

            out = StringIO()
            call_command("import_mailings", str(xlsx_path), stdout=out)

            text = out.getvalue()
            self.assertIn("обработано строк: 2", text)
            self.assertIn("создано записей: 2", text)
            self.assertIn("пропущено записей: 1", text)
            self.assertIn("ошибочных строк: 0", text)
