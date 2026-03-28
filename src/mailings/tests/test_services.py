from __future__ import annotations

from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model

from mailings.services import EmailImportService, EmailSendingService
from mailings.models import OutgoingEmail


class EmailImportServiceTest(TestCase):
    
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
    
    def test_process_valid_data(self) -> None:
        data = [
            {
                "external_id": "ext-1",
                "user_id": str(self.user.id),
                "email": "test@example.com",
                "subject": "Test Subject",
                "message": "Test Message"
            }
        ]
        
        stats = EmailImportService.process_xlsx_data(data)
        
        self.assertEqual(stats["total_rows"], 1)
        self.assertEqual(stats["processed_rows"], 1)
        self.assertEqual(stats["created_records"], 1)
        self.assertEqual(stats["skipped_records"], 0)
        self.assertEqual(stats["error_rows"], 0)
        self.assertEqual(len(stats["errors"]), 0)
        
        email = OutgoingEmail.objects.get(external_id="ext-1")
        self.assertEqual(email.user, self.user)
        self.assertEqual(email.email, "test@example.com")
        self.assertEqual(email.subject, "Test Subject")
        self.assertEqual(email.message, "Test Message")
    
    def test_process_empty_rows(self) -> None:
        data = [{"external_id": "", "user_id": "", "email": "", "subject": "", "message": ""}]
        
        stats = EmailImportService.process_xlsx_data(data)
        
        self.assertEqual(stats["skipped_records"], 1)
        self.assertEqual(stats["created_records"], 0)
    
    def test_process_invalid_data(self) -> None:
        data = [
            {
                "external_id": "ext-1",
                "user_id": "invalid",
                "email": "invalid-email",
                "subject": "",
                "message": "Test Message"
            }
        ]
        
        stats = EmailImportService.process_xlsx_data(data)
        
        self.assertEqual(stats["error_rows"], 1)
        self.assertEqual(stats["created_records"], 0)
        self.assertEqual(len(stats["errors"]), 1)
    
    def test_process_duplicate_external_id(self) -> None:
        OutgoingEmail.objects.create(
            external_id="ext-1",
            user=self.user,
            email="test@example.com",
            subject="Test Subject",
            message="Test Message"
        )
        
        data = [
            {
                "external_id": "ext-1",
                "user_id": str(self.user.id),
                "email": "test2@example.com",
                "subject": "Test Subject 2",
                "message": "Test Message 2"
            }
        ]
        
        stats = EmailImportService.process_xlsx_data(data)
        
        self.assertEqual(stats["skipped_records"], 1)
        self.assertEqual(stats["created_records"], 0)


class EmailSendingServiceTest(TestCase):
    
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.email = OutgoingEmail.objects.create(
            external_id="ext-1",
            user=self.user,
            email="test@example.com",
            subject="Test Subject",
            message="Test Message"
        )
    
    @patch('mailings.services.send_email')
    def test_send_pending_emails_success(self, mock_send) -> None:
        mock_send.return_value = None
        
        stats = EmailSendingService.send_pending_emails()
        
        self.assertEqual(stats["total_processed"], 1)
        self.assertEqual(stats["sent"], 1)
        self.assertEqual(stats["errors"], 0)
        
        self.email.refresh_from_db()
        self.assertEqual(self.email.status, OutgoingEmail.Status.SENT)
        mock_send.assert_called_once_with("test@example.com", "Test Subject", "Test Message")
    
    @patch('mailings.services.send_email')
    def test_send_pending_emails_error(self, mock_send) -> None:
        mock_send.side_effect = Exception("SMTP Error")
        
        stats = EmailSendingService.send_pending_emails()
        
        self.assertEqual(stats["total_processed"], 1)
        self.assertEqual(stats["sent"], 0)
        self.assertEqual(stats["errors"], 1)
        
        self.email.refresh_from_db()
        self.assertEqual(self.email.status, OutgoingEmail.Status.ERROR)
        self.assertEqual(self.email.last_error, "SMTP Error")


class EmailSimulationTest(TestCase):
    
    @patch('builtins.print')
    def test_send_email(self, mock_print) -> None:
        from mailings.utils import send_email
        
        send_email("test@example.com", "Test Subject", "Test Message")
        
        mock_print.assert_called()
        call_args = str(mock_print.call_args)
        self.assertIn("Send EMAIL...", call_args)
