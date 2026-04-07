from django.test import TestCase
from unittest.mock import patch, MagicMock
from datetime import datetime

class TestSystemEntities(TestCase):
    
    @patch('ExtLearnerUJ.models.Session.objects.create')
    def test_session_create(self, mock_create):
        mock_create.return_value = MagicMock(id="sess_1")
        from ExtLearnerUJ.models import Session
        session = Session.create("user_1")
        self.assertIsNotNone(session)

    @patch('ExtLearnerUJ.models.Session.save')
    def test_session_invalidate(self, mock_save):
        from ExtLearnerUJ.models import Session
        session = Session(id="sess_1", expiresAt=datetime.now())
        session.invalidate()
        mock_save.assert_called_once()
        
    @patch('ExtLearnerUJ.models.User.objects.get')
    def test_email_verification_token_verify(self, mock_get):
        from ExtLearnerUJ.models import EmailVerificationToken
        token = EmailVerificationToken(token="123", expiresAt=datetime(2099, 1, 1))
        result = token.verify()
        self.assertTrue(result)

    @patch('ExtLearnerUJ.models.Notification.save')
    def test_notification_send(self, mock_save):
        from ExtLearnerUJ.models import Notification
        notif = Notification(userId="1", message="Test")
        notif.send()
        mock_save.assert_called_once()

    @patch('ExtLearnerUJ.models.Notification.save')
    def test_notification_markAsRead(self, mock_save):
        from ExtLearnerUJ.models import Notification
        notif = Notification(userId="1", message="Test", isRead=False)
        notif.markAsRead()
        self.assertTrue(notif.isRead)
        mock_save.assert_called_once()
