from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from mailings.models import OutgoingEmail


class OutgoingEmailTest(TestCase):
    
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.email = OutgoingEmail.objects.create(
            external_id="123",
            user=self.user,
            email="test@example.com",
            subject="Test Subject",
            message="Test Message"
        )
    
    def test_outgoing_email_creation(self) -> None:
        self.assertEqual(self.email.external_id, "123")
        self.assertEqual(self.email.user, self.user)
        self.assertEqual(self.email.email, "test@example.com")
        self.assertEqual(self.email.subject, "Test Subject")
        self.assertEqual(self.email.message, "Test Message")
        self.assertEqual(self.email.status, OutgoingEmail.Status.PENDING)
        self.assertIsNotNone(self.email.created_at)
    
    def test_outgoing_email_str(self) -> None:
        expected = f"OutgoingEmail object ({self.email.id})"
        self.assertEqual(str(self.email), expected)
    
    def test_unique_external_id(self) -> None:
        with self.assertRaises(Exception):
            OutgoingEmail.objects.create(
                external_id="123",
                user=self.user,
                email="test2@example.com",
                subject="Test Subject 2",
                message="Test Message 2"
            )
    
    def test_meta_ordering(self) -> None:
        import time
        time.sleep(0.01)
        
        email2 = OutgoingEmail.objects.create(
            external_id="789",
            user=self.user,
            email="test3@example.com",
            subject="Test Subject 3",
            message="Test Message 3"
        )
        
        emails = list(OutgoingEmail.objects.order_by('-created_at'))
        self.assertEqual(emails[0], email2)
        self.assertEqual(emails[1], self.email)
