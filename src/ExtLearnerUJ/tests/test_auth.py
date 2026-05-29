"""
Testy Sprintu 1 — moduł autentykacji.

Pokrywa: User.register, verifyEmail, authenticate, logout, deleteAccount,
Session (create/is_valid/refresh/invalidate), EmailVerificationToken,
middleware, dekoratory, pełny flow register→verify→login→dashboard.
"""
from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from ExtLearnerUJ.models import (
    User, Student, Session, EmailVerificationToken, Material,
)


# ============================================================
# User model
# ============================================================
class UserRegisterTests(TestCase):
    def test_register_creates_student(self):
        user = User.register('anna@uj.edu.pl', 'SilneHaslo123', 'Anna Nowak')
        self.assertIsNotNone(user)
        self.assertIsInstance(user, Student)
        self.assertEqual(user.email, 'anna@uj.edu.pl')
        self.assertFalse(user.emailVerified)
        self.assertEqual(user.status, User.STATUS_ACTIVE)

    def test_register_hashes_password(self):
        user = User.register('bob@uj.edu.pl', 'SilneHaslo123', 'Bob')
        self.assertNotEqual(user.password, 'SilneHaslo123')
        self.assertTrue(user.password.startswith('argon2'))

    def test_register_sends_verification_email(self):
        User.register('student@uj.edu.pl', 'SilneHaslo123', 'Student')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('student@uj.edu.pl', mail.outbox[0].to)
        self.assertIn('kod weryfikacyjny', mail.outbox[0].subject.lower())

    def test_register_creates_verification_token(self):
        User.register('token@uj.edu.pl', 'SilneHaslo123', 'X')
        self.assertEqual(
            EmailVerificationToken.objects.filter(userId='token@uj.edu.pl').count(), 1,
        )

    def test_register_rejects_duplicate_email(self):
        User.register('dup@uj.edu.pl', 'SilneHaslo123', 'A')
        duplicate = User.register('dup@uj.edu.pl', 'InneHaslo456', 'B')
        self.assertIsNone(duplicate)
        self.assertEqual(User.objects.filter(email='dup@uj.edu.pl').count(), 1)

    def test_tokens_are_unique_per_user(self):
        """Regression test dla buga z callable default —
        wcześniej wszyscy dostawali ten sam token."""
        User.register('a@uj.edu.pl', 'SilneHaslo123', 'A')
        User.register('b@uj.edu.pl', 'SilneHaslo123', 'B')
        tokens = set(EmailVerificationToken.objects.values_list('token', flat=True))
        self.assertEqual(len(tokens), 2)


class UserVerifyEmailTests(TestCase):
    def setUp(self):
        self.user = User.register('verify@uj.edu.pl', 'SilneHaslo123', 'V')
        self.token = EmailVerificationToken.objects.get(userId='verify@uj.edu.pl')

    def test_valid_token_activates_account(self):
        result = self.user.verifyEmail(self.token.token)
        self.assertTrue(result)
        self.user.refresh_from_db()
        self.assertTrue(self.user.emailVerified)

    def test_invalid_token_rejected(self):
        result = self.user.verifyEmail('000000')
        self.assertFalse(result)
        self.user.refresh_from_db()
        self.assertFalse(self.user.emailVerified)

    def test_expired_token_rejected(self):
        self.token.expiresAt = timezone.now() - timedelta(hours=1)
        self.token.save()
        result = self.user.verifyEmail(self.token.token)
        self.assertFalse(result)

    def test_token_deleted_after_successful_verification(self):
        self.user.verifyEmail(self.token.token)
        self.assertFalse(
            EmailVerificationToken.objects.filter(userId='verify@uj.edu.pl').exists()
        )


class UserAuthenticateTests(TestCase):
    def setUp(self):
        self.user = User.register('login@uj.edu.pl', 'SilneHaslo123', 'L')
        token = EmailVerificationToken.objects.get(userId='login@uj.edu.pl')
        self.user.verifyEmail(token.token)

    def test_authenticate_success_returns_session(self):
        session = User.authenticate('login@uj.edu.pl', 'SilneHaslo123')
        self.assertIsNotNone(session)
        self.assertIsInstance(session, Session)
        self.assertEqual(session.userId, 'login@uj.edu.pl')

    def test_authenticate_wrong_password(self):
        self.assertIsNone(User.authenticate('login@uj.edu.pl', 'zle'))

    def test_authenticate_nonexistent_user(self):
        self.assertIsNone(User.authenticate('nope@uj.edu.pl', 'cokolwiek'))

    def test_authenticate_blocks_unverified_user(self):
        u = User.register('unv@uj.edu.pl', 'SilneHaslo123', 'U')
        self.assertIsNone(User.authenticate('unv@uj.edu.pl', 'SilneHaslo123'))

    def test_authenticate_blocks_blocked_user(self):
        self.user.status = User.STATUS_BLOCKED
        self.user.save()
        self.assertIsNone(User.authenticate('login@uj.edu.pl', 'SilneHaslo123'))


class UserLogoutTests(TestCase):
    def test_logout_invalidates_all_sessions(self):
        user = User.register('logout@uj.edu.pl', 'SilneHaslo123', 'X')
        Session.create('logout@uj.edu.pl')
        Session.create('logout@uj.edu.pl')
        self.assertEqual(Session.objects.filter(userId='logout@uj.edu.pl').count(), 2)

        user.logout()
        self.assertEqual(Session.objects.filter(userId='logout@uj.edu.pl').count(), 0)


class UserDeleteAccountTests(TestCase):
    def test_delete_account_cascades(self):
        user = User.register('del@uj.edu.pl', 'SilneHaslo123', 'D')
        Session.create('del@uj.edu.pl')

        self.assertTrue(user.deleteAccount())
        self.assertFalse(User.objects.filter(email='del@uj.edu.pl').exists())
        self.assertFalse(Session.objects.filter(userId='del@uj.edu.pl').exists())
        self.assertFalse(
            EmailVerificationToken.objects.filter(userId='del@uj.edu.pl').exists()
        )


# ============================================================
# Session model
# ============================================================
class SessionTests(TestCase):
    def test_create_sets_token_and_expiry(self):
        s = Session.create('x@uj.edu.pl')
        self.assertTrue(s.token)
        self.assertGreater(s.expiresAt, timezone.now())

    def test_is_valid_returns_true_for_fresh(self):
        s = Session.create('x@uj.edu.pl')
        self.assertTrue(s.is_valid())

    def test_is_valid_returns_false_for_expired(self):
        s = Session.create('x@uj.edu.pl')
        s.expiresAt = timezone.now() - timedelta(minutes=1)
        s.save()
        self.assertFalse(s.is_valid())

    def test_refresh_extends_expiry_when_close(self):
        s = Session.create('x@uj.edu.pl')
        # Udawaj, że do wygaśnięcia zostało 30 min
        s.expiresAt = timezone.now() + timedelta(minutes=30)
        s.save()
        original = s.expiresAt

        s.refresh()
        self.assertGreater(s.expiresAt, original)

    def test_refresh_noop_when_far_from_expiry(self):
        s = Session.create('x@uj.edu.pl')
        original = s.expiresAt
        s.refresh()
        # Nie powinno się zmienić (bo zostało >1h)
        self.assertEqual(s.expiresAt, original)

    def test_invalidate_deletes_session(self):
        s = Session.create('x@uj.edu.pl')
        s.invalidate()
        self.assertFalse(Session.objects.filter(pk=s.pk).exists())

    def test_tokens_are_unique(self):
        s1 = Session.create('a@uj.edu.pl')
        s2 = Session.create('a@uj.edu.pl')
        self.assertNotEqual(s1.token, s2.token)


# ============================================================
# Middleware + dekoratory (flow end-to-end przez Client)
# ============================================================
class MiddlewareTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.register('mw@uj.edu.pl', 'SilneHaslo123', 'MW')
        token = EmailVerificationToken.objects.get(userId='mw@uj.edu.pl')
        self.user.verifyEmail(token.token)

    def test_dashboard_redirects_anonymous_to_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_authenticated_can_access_dashboard(self):
        session = User.authenticate('mw@uj.edu.pl', 'SilneHaslo123')
        self.client.cookies[settings.SESSION_COOKIE_NAME_APP] = session.token

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_invalid_token_cookie_treated_as_anonymous(self):
        self.client.cookies[settings.SESSION_COOKIE_NAME_APP] = 'nieistniejacy-token'
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_expired_session_cleaned_up(self):
        session = User.authenticate('mw@uj.edu.pl', 'SilneHaslo123')
        # Wymuś wygaśnięcie
        session.expiresAt = timezone.now() - timedelta(minutes=1)
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME_APP] = session.token

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Session.objects.filter(pk=session.pk).exists())


# ============================================================
# Pełny flow: rejestracja → weryfikacja → login → dashboard
# ============================================================
class RegistrationFlowTests(TestCase):
    def test_full_flow(self):
        client = Client()

        # Krok 1 — rejestracja
        response = client.post(reverse('register'), {
            'name': 'Anna Testowa',
            'email': 'flow@uj.edu.pl',
            'password': 'SilneHaslo123',
            'password_confirm': 'SilneHaslo123',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email='flow@uj.edu.pl').exists())
        self.assertEqual(len(mail.outbox), 1)

        # Krok 2 — weryfikacja kodu z maila
        token = EmailVerificationToken.objects.get(userId='flow@uj.edu.pl').token
        response = client.post(reverse('verify_email'), {'code': token}, follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email='flow@uj.edu.pl')
        self.assertTrue(user.emailVerified)

        # Krok 3 — logowanie
        response = client.post(reverse('login'), {
            'email': 'flow@uj.edu.pl',
            'password': 'SilneHaslo123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(settings.SESSION_COOKIE_NAME_APP, response.cookies)

        # Krok 4 — dashboard dostępny
        response = client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Anna Testowa')


class RegistrationValidationTests(TestCase):
    def test_password_mismatch_rejected(self):
        client = Client()
        response = client.post(reverse('register'), {
            'name': 'X',
            'email': 'x@uj.edu.pl',
            'password': 'SilneHaslo123',
            'password_confirm': 'Inne',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='x@uj.edu.pl').exists())

    def test_short_password_rejected(self):
        client = Client()
        response = client.post(reverse('register'), {
            'name': 'X',
            'email': 'x@uj.edu.pl',
            'password': 'krotkie',
            'password_confirm': 'krotkie',
        })
        self.assertFalse(User.objects.filter(email='x@uj.edu.pl').exists())


class LogoutTests(TestCase):
    def test_logout_removes_session_and_cookie(self):
        user = User.register('lo@uj.edu.pl', 'SilneHaslo123', 'LO')
        token = EmailVerificationToken.objects.get(userId='lo@uj.edu.pl').token
        user.verifyEmail(token)
        session = User.authenticate('lo@uj.edu.pl', 'SilneHaslo123')

        client = Client()
        client.cookies[settings.SESSION_COOKIE_NAME_APP] = session.token

        response = client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Session.objects.filter(pk=session.pk).exists())
