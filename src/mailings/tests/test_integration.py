from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from django.contrib.auth import get_user_model

from mailings.models import OutgoingEmail
from mailings.services import EmailImportService, EmailSendingService

try:
    import openpyxl
except ImportError:
    openpyxl = None

User = get_user_model()


class EmailIntegrationTests(TestCase):
    
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", password="testpass")
    
    @patch("mailings.services.send_email")
    def test_full_import_and_send_workflow(self, mock_send_email: MagicMock) -> None:
        
        if not openpyxl:
            self.skipTest("openpyxl не установлен")
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["external_id", "user_id", "email", "subject", "message"])
        ws.append(["ext-1", str(self.user.id), "test1@example.com", "Subject 1", "Message 1"])
        ws.append(["ext-2", str(self.user.id), "test2@example.com", "Subject 2", "Message 2"])
        ws.append(["ext-3", str(self.user.id), "invalid-email", "Subject 3", "Message 3"])
        
        with tempfile.TemporaryDirectory() as td:
            xlsx_path = Path(td) / "test.xlsx"
            wb.save(xlsx_path)
            
            stats = EmailImportService.process_xlsx_data([
                {"external_id": "ext-1", "user_id": str(self.user.id), "email": "test1@example.com", "subject": "Subject 1", "message": "Message 1"},
                {"external_id": "ext-2", "user_id": str(self.user.id), "email": "test2@example.com", "subject": "Subject 2", "message": "Message 2"},
                {"external_id": "ext-3", "user_id": str(self.user.id), "email": "invalid-email", "subject": "Subject 3", "message": "Message 3"},
            ])
            
            self.assertEqual(stats["created_records"], 2)
            self.assertEqual(stats["error_rows"], 1)
            
            self.assertEqual(OutgoingEmail.objects.count(), 2)
            self.assertEqual(OutgoingEmail.objects.filter(status=OutgoingEmail.Status.PENDING).count(), 2)
            
            send_stats = EmailSendingService.send_pending_emails()
            
            self.assertEqual(send_stats["sent"], 2)
            self.assertEqual(send_stats["errors"], 0)
            
            self.assertEqual(OutgoingEmail.objects.filter(status=OutgoingEmail.Status.SENT).count(), 2)
            
            self.assertEqual(mock_send_email.call_count, 2)
    
    def test_duplicate_external_id_handling(self) -> None:
        
        OutgoingEmail.objects.create(
            external_id="dup-1",
            user=self.user,
            email="existing@example.com",
            subject="Existing",
            message="Existing message"
        )
        
        stats = EmailImportService.process_xlsx_data([
            {"external_id": "dup-1", "user_id": str(self.user.id), "email": "new@example.com", "subject": "New", "message": "New message"},
            {"external_id": "new-1", "user_id": str(self.user.id), "email": "new@example.com", "subject": "New", "message": "New message"},
        ])
        
        self.assertEqual(stats["created_records"], 1)
        self.assertEqual(stats["skipped_records"], 1)
        
        self.assertEqual(OutgoingEmail.objects.count(), 2)
        
        original = OutgoingEmail.objects.get(external_id="dup-1")
        self.assertEqual(original.email, "existing@example.com")
    
    @patch("mailings.services.send_email")
    def test_email_sending_with_errors(self, mock_send_email: MagicMock) -> None:
        
        email1 = OutgoingEmail.objects.create(
            external_id="test-1",
            user=self.user,
            email="success@example.com",
            subject="Success",
            message="Success message"
        )
        
        email2 = OutgoingEmail.objects.create(
            external_id="test-2",
            user=self.user,
            email="error@example.com",
            subject="Error",
            message="Error message"
        )
        
        mock_send_email.side_effect = [None, Exception("SMTP error")]
        
        send_stats = EmailSendingService.send_pending_emails()
        
        self.assertEqual(send_stats["sent"], 1)
        self.assertEqual(send_stats["errors"], 1)
        
        email1.refresh_from_db()
        email2.refresh_from_db()
        
        self.assertEqual(email1.status, OutgoingEmail.Status.SENT)
        self.assertEqual(email2.status, OutgoingEmail.Status.ERROR)
        self.assertIn("SMTP error", email2.last_error)
    
    def test_command_integration(self) -> None:
        
        if not openpyxl:
            self.skipTest("openpyxl не установлен")
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["external_id", "user_id", "email", "subject", "message"])
        ws.append(["cmd-1", str(self.user.id), "cmd@example.com", "Command Test", "Command message"])
        
        with tempfile.TemporaryDirectory() as td:
            xlsx_path = Path(td) / "command_test.xlsx"
            wb.save(xlsx_path)
            
            out = StringIO()
            call_command("import_mailings", str(xlsx_path), stdout=out)
            
            output = out.getvalue()
            self.assertIn("обработано строк: 1", output)
            self.assertIn("создано записей: 1", output)
            
            self.assertEqual(OutgoingEmail.objects.filter(external_id="cmd-1").count(), 1)
