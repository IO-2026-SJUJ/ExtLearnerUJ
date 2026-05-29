"""
Testy Sprintu 2 (tydzień 1) — dodawanie materiałów, głosowanie,
zgłoszenia, weryfikacja moderatorska, notyfikacje.

Pokrywa: FR-08, FR-09, FR-11 (częściowo), FR-13, UC16, UC25,
UC31, UC32, UC33, UC36.
"""
import json

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from ExtLearnerUJ.models import (
    User, Student, Moderator, Admin, EmailVerificationToken,
    Material, Vote, MaterialVerification, Notification, Report, Comment,
)


# ============================================================
# Helpery
# ============================================================
def _verified_student(email='stud@uj.edu.pl', password='SilneHaslo123'):
    user = User.register(email, password, 'Test Student')
    token = EmailVerificationToken.objects.get(userId=email).token
    user.verifyEmail(token)
    return user


def _verified_moderator(email='mod@uj.edu.pl', password='SilneHaslo123'):
    """Tworzy usera jako Moderator (bezpośrednio w bazie — rejestracja
    studencka nie pozwala na wybór roli, to flow Sprintu 3)."""
    from django.contrib.auth.hashers import make_password
    mod = Moderator.objects.create(
        email=email,
        password=make_password(password),
        name='Test Moderator',
        status=User.STATUS_ACTIVE,
        emailVerified=True,
    )
    return mod


def _login_client(user, password='SilneHaslo123'):
    session = User.authenticate(user.email, password)
    client = Client()
    client.cookies[settings.SESSION_COOKIE_NAME_APP] = session.token
    return client


# ============================================================
# FR-08: Dodawanie materiału
# ============================================================
class MaterialCreateTests(TestCase):
    def setUp(self):
        self.student = _verified_student()
        self.client = _login_client(self.student)

    def test_form_page_accessible(self):
        response = self.client.get(reverse('material_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dodaj materiał')

    def test_create_material_without_file(self):
        response = self.client.post(reverse('material_create'), {
            'title': 'Present Perfect — szybki przewodnik',
            'category': 'grammar',
            'content': 'Present Perfect używamy gdy... ' * 3,
        })
        self.assertEqual(response.status_code, 302)
        m = Material.objects.get(title='Present Perfect — szybki przewodnik')
        self.assertEqual(m.status, Material.STATUS_PENDING)
        self.assertFalse(m.isVerified)
        self.assertEqual(m.authorId, self.student.email)

    def test_create_material_with_file(self):
        pdf = SimpleUploadedFile(
            'notatki.pdf', b'Fake PDF content', content_type='application/pdf',
        )
        response = self.client.post(reverse('material_create'), {
            'title': 'Phrasal verbs',
            'category': 'vocabulary',
            'content': 'Lista najczęstszych phrasal verbs z get, take, put...',
            'attachment': pdf,
        })
        self.assertEqual(response.status_code, 302)
        m = Material.objects.get(title='Phrasal verbs')
        self.assertEqual(m.attachments.count(), 1)
        self.assertEqual(m.attachments.first().fileName, 'notatki.pdf')

    def test_rejects_too_large_file(self):
        big = SimpleUploadedFile(
            'big.pdf', b'x' * (11 * 1024 * 1024),
            content_type='application/pdf',
        )
        response = self.client.post(reverse('material_create'), {
            'title': 'X', 'category': 'grammar',
            'content': 'opis opis opis opis opis',
            'attachment': big,
        })
        # Formularz powinien nie przejść walidacji
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Material.objects.filter(title='X').exists())

    def test_rejects_disallowed_file_type(self):
        exe = SimpleUploadedFile(
            'virus.exe', b'MZ', content_type='application/x-msdownload',
        )
        response = self.client.post(reverse('material_create'), {
            'title': 'Y', 'category': 'grammar',
            'content': 'opis opis opis opis opis',
            'attachment': exe,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Material.objects.filter(title='Y').exists())

    def test_requires_login(self):
        anon = Client()
        response = anon.get(reverse('material_create'))
        self.assertEqual(response.status_code, 302)


# ============================================================
# FR-09: Głosowanie na materiał
# ============================================================
class VotingTests(TestCase):
    def setUp(self):
        self.student = _verified_student()
        self.client = _login_client(self.student)
        self.material = Material.objects.create(
            title='M', content='c', authorId='other@uj.edu.pl',
            status=Material.STATUS_PENDING, priority=0,
        )

    def test_vote_creates_vote_and_increments_priority(self):
        response = self.client.post(reverse('material_vote', args=[self.material.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['priority'], 1)
        self.assertEqual(data['voteCount'], 1)
        self.assertTrue(data['userVoted'])
        self.assertTrue(
            Vote.objects.filter(userId=self.student.email, materialId=str(self.material.id)).exists()
        )

    def test_vote_is_idempotent(self):
        """Drugi głos tego samego usera nie zwiększa priorytetu."""
        self.client.post(reverse('material_vote', args=[self.material.id]))
        self.client.post(reverse('material_vote', args=[self.material.id]))

        self.material.refresh_from_db()
        self.assertEqual(self.material.priority, 1)
        self.assertEqual(Vote.objects.filter(materialId=str(self.material.id)).count(), 1)

    def test_different_users_each_add_one(self):
        other = _verified_student('inny@uj.edu.pl')
        other_client = _login_client(other)

        self.client.post(reverse('material_vote', args=[self.material.id]))
        other_client.post(reverse('material_vote', args=[self.material.id]))

        self.material.refresh_from_db()
        self.assertEqual(self.material.priority, 2)
        self.assertEqual(Vote.objects.filter(materialId=str(self.material.id)).count(), 2)

    def test_vote_nonexistent_material_returns_404(self):
        response = self.client.post(reverse('material_vote', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_vote_requires_login(self):
        anon = Client()
        response = anon.post(reverse('material_vote', args=[self.material.id]))
        # @session_login_required przekierowuje (302), nie 403
        self.assertEqual(response.status_code, 302)


# ============================================================
# FR-13: Zgłaszanie
# ============================================================
class ReportTests(TestCase):
    def setUp(self):
        self.student = _verified_student()
        self.client = _login_client(self.student)
        self.material = Material.objects.create(
            title='Sporny materiał', content='tekst', authorId='spam@uj.edu.pl',
            status=Material.STATUS_VERIFIED, isVerified=True,
        )

    def test_form_page_accessible(self):
        response = self.client.get(reverse('report_material', args=[self.material.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sporny materiał')

    def test_submit_report_creates_record(self):
        response = self.client.post(
            reverse('report_material', args=[self.material.id]),
            {'reason': 'W tym materiale są rażące błędy gramatyczne.'},
        )
        self.assertEqual(response.status_code, 302)
        r = Report.objects.get(reporterId=self.student.email)
        self.assertEqual(r.targetType, Report.TARGET_MATERIAL)
        self.assertEqual(r.targetId, str(self.material.id))
        self.assertEqual(r.status, Report.STATUS_PENDING)

    def test_report_too_short_rejected(self):
        response = self.client.post(
            reverse('report_material', args=[self.material.id]),
            {'reason': 'bad'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Report.objects.count(), 0)


# ============================================================
# UC31, UC32, UC33, UC36: Panel moderatora — weryfikacja materiałów
# ============================================================
class ModeratorQueueTests(TestCase):
    def setUp(self):
        self.mod = _verified_moderator()
        self.client = _login_client(self.mod)

        # Trzy materiały w kolejce z różnym priorytetem
        self.m_high = Material.objects.create(
            title='HIGH', authorId='a@uj.edu.pl', category='grammar',
            status=Material.STATUS_PENDING, priority=25,
        )
        self.m_mid = Material.objects.create(
            title='MID', authorId='a@uj.edu.pl', category='reading',
            status=Material.STATUS_PENDING, priority=10,
        )
        self.m_low = Material.objects.create(
            title='LOW', authorId='a@uj.edu.pl', category='grammar',
            status=Material.STATUS_PENDING, priority=0,
        )
        # Jeden już zweryfikowany — nie powinien być w kolejce
        self.m_done = Material.objects.create(
            title='DONE', authorId='a@uj.edu.pl',
            status=Material.STATUS_VERIFIED, isVerified=True,
        )

    def test_dashboard_shows_pending_count(self):
        response = self.client.get(reverse('moderator_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '3')  # 3 pending (high, mid, low)

    def test_queue_shows_only_pending(self):
        response = self.client.get(reverse('moderator_materials_queue'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'HIGH')
        self.assertContains(response, 'MID')
        self.assertContains(response, 'LOW')
        self.assertNotContains(response, 'DONE')

    def test_queue_sorted_by_priority_desc(self):
        response = self.client.get(reverse('moderator_materials_queue'))
        content = response.content.decode('utf-8')
        self.assertLess(content.index('HIGH'), content.index('MID'))
        self.assertLess(content.index('MID'), content.index('LOW'))

    def test_queue_requires_moderator_role(self):
        student = _verified_student('zwykly@uj.edu.pl')
        student_client = _login_client(student)
        response = student_client.get(reverse('moderator_materials_queue'))
        self.assertEqual(response.status_code, 403)

    def test_queue_anonymous_redirects_to_login(self):
        anon = Client()
        response = anon.get(reverse('moderator_materials_queue'))
        self.assertEqual(response.status_code, 302)


class ModeratorVerifyTests(TestCase):
    def setUp(self):
        self.mod = _verified_moderator()
        self.client = _login_client(self.mod)
        self.author_email = 'autor@uj.edu.pl'
        self.material = Material.objects.create(
            title='Do weryfikacji', content='treść',
            authorId=self.author_email, category='grammar',
            status=Material.STATUS_PENDING,
        )

    def test_accept_marks_as_verified(self):
        response = self.client.post(
            reverse('moderator_verify_material', args=[self.material.id]),
            {'decision': 'ACCEPTED', 'comment': ''},
        )
        self.assertEqual(response.status_code, 302)
        self.material.refresh_from_db()
        self.assertEqual(self.material.status, Material.STATUS_VERIFIED)
        self.assertTrue(self.material.isVerified)

    def test_reject_marks_as_rejected(self):
        response = self.client.post(
            reverse('moderator_verify_material', args=[self.material.id]),
            {'decision': 'REJECTED', 'comment': 'Błędy gramatyczne w drugim akapicie.'},
        )
        self.assertEqual(response.status_code, 302)
        self.material.refresh_from_db()
        self.assertEqual(self.material.status, Material.STATUS_REJECTED)
        self.assertFalse(self.material.isVerified)

    def test_needs_revision_keeps_pending(self):
        response = self.client.post(
            reverse('moderator_verify_material', args=[self.material.id]),
            {'decision': 'NEEDS_REVISION', 'comment': 'Dodaj więcej przykładów.'},
        )
        self.assertEqual(response.status_code, 302)
        self.material.refresh_from_db()
        self.assertEqual(self.material.status, Material.STATUS_PENDING)

    def test_reject_without_comment_rejected_by_form(self):
        response = self.client.post(
            reverse('moderator_verify_material', args=[self.material.id]),
            {'decision': 'REJECTED', 'comment': ''},
        )
        # Formularz powinien nie przejść walidacji
        self.assertEqual(response.status_code, 200)
        self.material.refresh_from_db()
        self.assertEqual(self.material.status, Material.STATUS_PENDING)

    def test_verification_creates_notification_for_author(self):
        self.client.post(
            reverse('moderator_verify_material', args=[self.material.id]),
            {'decision': 'ACCEPTED', 'comment': ''},
        )
        notifs = Notification.objects.filter(userId=self.author_email)
        self.assertEqual(notifs.count(), 1)
        self.assertIn('zaakceptowany', notifs.first().message)

    def test_verification_stores_record(self):
        self.client.post(
            reverse('moderator_verify_material', args=[self.material.id]),
            {'decision': 'ACCEPTED', 'comment': ''},
        )
        self.assertEqual(
            MaterialVerification.objects.filter(
                materialId=str(self.material.id),
                moderatorId=self.mod.email,
            ).count(),
            1,
        )

    def test_comment_saved(self):
        self.client.post(
            reverse('moderator_verify_material', args=[self.material.id]),
            {'decision': 'REJECTED', 'comment': 'Drobne literówki w treści.'},
        )
        self.assertTrue(
            Comment.objects.filter(
                targetType='MATERIAL', targetId=str(self.material.id),
            ).exists()
        )


# ============================================================
# UC32: Notyfikacje
# ============================================================
class NotificationsTests(TestCase):
    def setUp(self):
        self.student = _verified_student()
        self.client = _login_client(self.student)

        Notification.objects.create(
            userId=self.student.email,
            message='Test 1',
            isRead=False,
        )
        Notification.objects.create(
            userId=self.student.email,
            message='Test 2',
            isRead=True,
        )
        Notification.objects.create(
            userId='ktos-inny@uj.edu.pl',
            message='Cudza notyfikacja',
            isRead=False,
        )

    def test_list_shows_only_own(self):
        response = self.client.get(reverse('notifications_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test 1')
        self.assertContains(response, 'Test 2')
        self.assertNotContains(response, 'Cudza notyfikacja')

    def test_mark_as_read(self):
        n = Notification.objects.get(message='Test 1')
        response = self.client.post(
            reverse('notification_mark_read', args=[n.id])
        )
        self.assertEqual(response.status_code, 200)
        n.refresh_from_db()
        self.assertTrue(n.isRead)

    def test_cant_mark_others_notification(self):
        cudza = Notification.objects.get(message='Cudza notyfikacja')
        response = self.client.post(
            reverse('notification_mark_read', args=[cudza.id])
        )
        self.assertEqual(response.status_code, 404)
        cudza.refresh_from_db()
        self.assertFalse(cudza.isRead)


# ============================================================
# Model tests
# ============================================================
class ModelLogicTests(TestCase):
    """Czysto jednostkowe testy nowej logiki w modelach."""

    def test_student_vote_material_idempotent(self):
        student = _verified_student('vote-unit@uj.edu.pl')
        material = Material.objects.create(
            title='X', authorId='a@uj.edu.pl', priority=5,
        )
        v1 = student.voteMaterial(material.id)
        v2 = student.voteMaterial(material.id)
        self.assertIsNotNone(v1)
        self.assertEqual(v1.pk, v2.pk)

        material.refresh_from_db()
        self.assertEqual(material.priority, 6)  # +1, nie +2

    def test_moderator_view_materials_to_verify_empty(self):
        mod = _verified_moderator('empty@uj.edu.pl')
        self.assertEqual(mod.viewMaterialsToVerify(), [])

    def test_moderator_verify_nonexistent_returns_none(self):
        mod = _verified_moderator('null@uj.edu.pl')
        result = mod.verifyMaterial(99999, 'ACCEPTED', '')
        self.assertIsNone(result)

    def test_user_submit_report_persists(self):
        student = _verified_student('reporter@uj.edu.pl')
        report = student.submitReport('MATERIAL', '42', 'Dużo błędów')
        self.assertIsNotNone(report)
        self.assertEqual(report.reporterId, 'reporter@uj.edu.pl')
        self.assertEqual(report.status, Report.STATUS_PENDING)

    def test_notification_mark_as_read(self):
        n = Notification.objects.create(
            userId='a@uj.edu.pl', message='x', isRead=False,
        )
        n.markAsRead()
        n.refresh_from_db()
        self.assertTrue(n.isRead)
