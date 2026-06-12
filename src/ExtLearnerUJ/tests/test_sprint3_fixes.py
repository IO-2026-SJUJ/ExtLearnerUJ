"""
Testy poprawek/rozszerzeń Sprintu 3:
- reset hasła („Zapomniałem hasła")
- logowanie e-mailem bez względu na wielkość liter
- moderator/admin mają funkcje studenta (diagnostyka, egzamin, materiały)
- powiadomienie o złożeniu wniosku moderatorskiego + licznik u admina
- usunięcie materiału po uznaniu zgłoszenia + link do autora
- usuwanie materiałów (admin / właściciel) + filtr „moje"
- komunikat o blokadzie z datą + auto-odblokowanie
- filtr moderatorów u admina + zabranie roli
"""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from ExtLearnerUJ.models import (
    User, Student, Moderator, Admin, EmailVerificationToken,
    Material, DiagnosticTest, Question, Test,
    Report, Notification, ModeratorApplication, PasswordResetToken,
)


def _verified_student(email='stud@uj.edu.pl', password='SilneHaslo123', name='Stud'):
    user = User.register(email, password, name)
    token = EmailVerificationToken.objects.get(userId=email).token
    user.verifyEmail(token)
    return user


def _verified_moderator(email='mod@uj.edu.pl', password='SilneHaslo123'):
    return Moderator.objects.create(
        email=email, password=make_password(password), name='Mod',
        status=User.STATUS_ACTIVE, emailVerified=True)


def _verified_admin(email='admin@uj.edu.pl', password='SilneHaslo123'):
    return Admin.objects.create(
        email=email, password=make_password(password), name='Adm',
        status=User.STATUS_ACTIVE, emailVerified=True)


def _login(user, password='SilneHaslo123'):
    session = User.authenticate(user.email, password)
    c = Client()
    c.cookies[settings.SESSION_COOKIE_NAME_APP] = session.token
    return c


# ============================================================
# Logowanie — wielkość liter w e-mailu bez znaczenia
# ============================================================
class CaseInsensitiveLoginTests(TestCase):
    def test_login_uppercase_email(self):
        _verified_student(email='kowalski@uj.edu.pl')
        session = User.authenticate('KOWALSKI@UJ.EDU.PL', 'SilneHaslo123')
        self.assertIsNotNone(session)

    def test_login_mixed_case_email(self):
        _verified_student(email='nowak@uj.edu.pl')
        session = User.authenticate('  Nowak@Uj.Edu.PL ', 'SilneHaslo123')
        self.assertIsNotNone(session)


# ============================================================
# Reset hasła
# ============================================================
class PasswordResetTests(TestCase):
    def setUp(self):
        self.student = _verified_student()

    def test_forgot_sends_email_and_token(self):
        mail.outbox.clear()
        client = Client()
        resp = client.post(reverse('forgot_password'), {'email': self.student.email})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(PasswordResetToken.objects.filter(userId=self.student.email).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('reset', mail.outbox[0].subject.lower())

    def test_forgot_unknown_email_no_token_no_leak(self):
        client = Client()
        resp = client.post(reverse('forgot_password'), {'email': 'niema@uj.edu.pl'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(PasswordResetToken.objects.count(), 0)

    def test_reset_changes_password(self):
        token = PasswordResetToken.issue(self.student.email)
        client = Client()
        resp = client.post(reverse('reset_password', args=[token.token]), {
            'password': 'ZupelnieNoweHaslo9', 'password_confirm': 'ZupelnieNoweHaslo9',
        })
        self.assertEqual(resp.status_code, 302)
        # Stare hasło nie działa, nowe działa.
        self.assertIsNone(User.authenticate(self.student.email, 'SilneHaslo123'))
        self.assertIsNotNone(User.authenticate(self.student.email, 'ZupelnieNoweHaslo9'))
        token.refresh_from_db()
        self.assertTrue(token.used)

    def test_used_token_rejected(self):
        token = PasswordResetToken.issue(self.student.email)
        token.used = True
        token.save(update_fields=['used'])
        client = Client()
        resp = client.get(reverse('reset_password', args=[token.token]))
        self.assertEqual(resp.status_code, 302)  # redirect do forgot


# ============================================================
# Moderator/Admin mają funkcje studenta
# ============================================================
class RoleAccessTests(TestCase):
    def setUp(self):
        DiagnosticTest.objects.create(title='Diag', type='DIAGNOSTIC')
        Test.objects.create(title='Egzamin', type=Test.TYPE_EXAM, durationMinutes=30)

    def test_moderator_can_open_diagnostic(self):
        client = _login(_verified_moderator())
        self.assertEqual(client.get(reverse('diagnostic_start')).status_code, 200)

    def test_moderator_can_open_exam(self):
        client = _login(_verified_moderator())
        self.assertEqual(client.get(reverse('exam_start')).status_code, 200)

    def test_admin_can_open_material_create(self):
        client = _login(_verified_admin())
        self.assertEqual(client.get(reverse('material_create')).status_code, 200)

    def test_moderator_can_view_my_works(self):
        client = _login(_verified_moderator())
        self.assertEqual(client.get(reverse('my_works')).status_code, 200)

    def test_moderator_can_vote(self):
        mod = _verified_moderator()
        mat = Material.objects.create(title='M', authorId='x@uj.edu.pl',
                                      category='grammar', status='PENDING')
        client = _login(mod)
        resp = client.post(reverse('material_vote', args=[mat.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['ok'])


# ============================================================
# Wniosek moderatorski — powiadomienie + licznik u admina
# ============================================================
class ApplicationNotificationTests(TestCase):
    def test_apply_creates_notification(self):
        student = _verified_student()
        student.applyForModerator(motivation='x' * 40)
        self.assertTrue(
            Notification.objects.filter(
                userId=student.email, message__icontains='wniosek'
            ).exists()
        )

    def test_admin_stats_counts_applications(self):
        s1 = _verified_student(email='a1@uj.edu.pl')
        s2 = _verified_student(email='a2@uj.edu.pl')
        s1.applyForModerator(motivation='x' * 40)
        s2.applyForModerator(motivation='y' * 40)
        admin = _verified_admin()
        stats = admin.viewSystemStats()
        self.assertEqual(stats['applications_pending'], 2)

    def test_dashboard_shows_application_count(self):
        _verified_student(email='a3@uj.edu.pl').applyForModerator(motivation='z' * 40)
        client = _login(_verified_admin())
        resp = client.get(reverse('admin_dashboard'))
        self.assertContains(resp, 'Wnioski moderatorskie')


# ============================================================
# Zgłoszenie materiału — usunięcie po uznaniu za zasadne
# ============================================================
class ReportResolutionTests(TestCase):
    def setUp(self):
        self.admin = _verified_admin()
        self.author = _verified_student(email='author@uj.edu.pl')
        self.material = Material.objects.create(
            title='Spam', authorId=self.author.email, category='grammar',
            status=Material.STATUS_VERIFIED, isVerified=True)
        self.reporter = _verified_student(email='reporter@uj.edu.pl')
        self.report = self.reporter.submitReport(
            Report.TARGET_MATERIAL, self.material.id, 'To jest spam i błędy.')

    def test_resolve_deletes_material(self):
        self.admin.reviewReport(self.report.id, Report.STATUS_RESOLVED)
        self.assertFalse(Material.objects.filter(pk=self.material.id).exists())
        # autor i zgłaszający dostają powiadomienia
        self.assertTrue(Notification.objects.filter(userId=self.author.email).exists())
        self.assertTrue(Notification.objects.filter(userId=self.reporter.email).exists())

    def test_dismiss_keeps_material(self):
        self.admin.reviewReport(self.report.id, Report.STATUS_DISMISSED)
        self.assertTrue(Material.objects.filter(pk=self.material.id).exists())

    def test_review_page_shows_author_link(self):
        client = _login(self.admin)
        resp = client.get(reverse('admin_review_report', args=[self.report.id]))
        self.assertContains(resp, self.author.email)


# ============================================================
# Usuwanie materiałów + filtr „moje"
# ============================================================
class MaterialDeleteTests(TestCase):
    def setUp(self):
        self.owner = _verified_student(email='owner@uj.edu.pl')
        self.other = _verified_student(email='other@uj.edu.pl')
        self.admin = _verified_admin()
        self.mat = Material.objects.create(
            title='Owned', authorId=self.owner.email, category='grammar',
            status=Material.STATUS_VERIFIED, isVerified=True)

    def test_owner_deletes_own(self):
        client = _login(self.owner)
        resp = client.post(reverse('material_delete', args=[self.mat.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Material.objects.filter(pk=self.mat.id).exists())

    def test_other_cannot_delete(self):
        client = _login(self.other)
        client.post(reverse('material_delete', args=[self.mat.id]))
        self.assertTrue(Material.objects.filter(pk=self.mat.id).exists())

    def test_admin_deletes_any(self):
        client = _login(self.admin)
        resp = client.post(reverse('material_delete', args=[self.mat.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Material.objects.filter(pk=self.mat.id).exists())

    def test_mine_filter(self):
        Material.objects.create(title='Foreign', authorId='zzz@uj.edu.pl',
                                category='grammar', status='VERIFIED', isVerified=True)
        client = _login(self.owner)
        resp = client.get(reverse('materials_list') + '?mine=1')
        self.assertContains(resp, 'Owned')
        self.assertNotContains(resp, 'Foreign')


# ============================================================
# Blokada konta — komunikat z datą + auto-odblokowanie
# ============================================================
class BlockMessageTests(TestCase):
    def setUp(self):
        self.admin = _verified_admin()
        self.victim = _verified_student(email='victim@uj.edu.pl')

    def test_temporary_block_sets_until(self):
        self.admin.manageUserAccount(self.victim.email, User.STATUS_BLOCKED, days=7)
        self.victim.refresh_from_db()
        self.assertEqual(self.victim.status, User.STATUS_BLOCKED)
        self.assertIsNotNone(self.victim.blockedUntil)

    def test_login_shows_block_message(self):
        self.admin.manageUserAccount(self.victim.email, User.STATUS_BLOCKED, days=7)
        client = Client()
        resp = client.post(reverse('login'), {
            'email': self.victim.email, 'password': 'SilneHaslo123',
        }, follow=True)
        self.assertContains(resp, 'zablokowane do')

    def test_expired_block_auto_unblocks_on_login(self):
        self.admin.manageUserAccount(self.victim.email, User.STATUS_BLOCKED, days=1)
        self.victim.refresh_from_db()
        self.victim.blockedUntil = timezone.now() - timedelta(minutes=1)
        self.victim.save(update_fields=['blockedUntil'])
        session = User.authenticate(self.victim.email, 'SilneHaslo123')
        self.assertIsNotNone(session)  # auto-odblokowany
        self.victim.refresh_from_db()
        self.assertEqual(self.victim.status, User.STATUS_ACTIVE)

    def test_permanent_block_no_date(self):
        self.admin.manageUserAccount(self.victim.email, User.STATUS_BLOCKED, days=None)
        self.victim.refresh_from_db()
        self.assertIsNone(self.victim.blockedUntil)


# ============================================================
# Admin — filtr moderatorów + zabranie roli z listy
# ============================================================
class UsersListFilterTests(TestCase):
    def setUp(self):
        self.admin = _verified_admin()
        self.student = _verified_student(email='zwykly@uj.edu.pl')
        self.mod = _verified_moderator(email='moderek@uj.edu.pl')

    def test_filter_moderators_only(self):
        client = _login(self.admin)
        resp = client.get(reverse('admin_users_list') + '?role=moderator')
        self.assertContains(resp, 'moderek@uj.edu.pl')
        self.assertNotContains(resp, 'zwykly@uj.edu.pl')

    def test_filter_students_only(self):
        client = _login(self.admin)
        resp = client.get(reverse('admin_users_list') + '?role=student')
        self.assertContains(resp, 'zwykly@uj.edu.pl')
        self.assertNotContains(resp, 'moderek@uj.edu.pl')

    def test_revoke_from_list(self):
        client = _login(self.admin)
        resp = client.post(reverse('admin_revoke_moderator', args=[self.mod.email]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Moderator.objects.filter(pk=self.mod.pk).exists())
        self.assertTrue(Student.objects.filter(pk=self.mod.pk).exists())


# ============================================================
# Seed administratora
# ============================================================
class SeedAdminTests(TestCase):
    def test_seed_creates_admin(self):
        from django.core.management import call_command
        call_command('seed_admin', verbosity=0)
        self.assertTrue(Admin.objects.filter(email='admin@uj.edu.pl').exists())
        # logowanie działa
        self.assertIsNotNone(User.authenticate('admin@uj.edu.pl', 'AdminHaslo123'))


# ============================================================
# Kolejne poprawki: dostęp do oceniania prac, „odczytaj wszystkie",
# skróty na panelu dla moderatora/admina
# ============================================================
from ExtLearnerUJ.models import Work, Package, WorkReview


class ModeratorGradesPaidWorksTests(TestCase):
    def setUp(self):
        self.mod = _verified_moderator()
        self.pkg = Package.objects.create(name='Rozszerzony', price=25.0, scope='s', description='d')
        self.work = Work.objects.create(
            title='Essay', description='Treść pracy do oceny.',
            studentId='s@uj.edu.pl', packageId=str(self.pkg.id),
            status=Work.STATUS_PAID)

    def test_nav_has_grading_link(self):
        # Prace do oceny są dostępne wewnątrz panelu Moderacja.
        client = _login(self.mod)
        resp = client.get(reverse('moderator_dashboard'))
        self.assertContains(resp, reverse('moderator_works_queue'))

    def test_full_grading_flow(self):
        client = _login(self.mod)
        self.assertEqual(client.get(reverse('moderator_works_queue')).status_code, 200)
        self.assertEqual(client.post(reverse('moderator_reserve_work', args=[self.work.id])).status_code, 302)
        self.assertEqual(client.get(reverse('moderator_work_editor', args=[self.work.id])).status_code, 200)
        resp = client.post(reverse('moderator_work_editor', args=[self.work.id]), {
            'action': 'publish', 'grade': 'B2',
            'generalComment': 'Dobra praca, spójna argumentacja i poprawna gramatyka.',
        })
        self.assertEqual(resp.status_code, 302)
        self.work.refresh_from_db()
        self.assertEqual(self.work.status, Work.STATUS_REVIEWED)


class MarkAllReadTests(TestCase):
    def test_mark_all_read(self):
        student = _verified_student()
        Notification.objects.create(userId=student.email, message='a')
        Notification.objects.create(userId=student.email, message='b')
        client = _login(student)
        resp = client.post(reverse('notifications_mark_all_read'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Notification.objects.filter(userId=student.email, isRead=False).count(), 0)

    def test_button_shown_when_unread(self):
        student = _verified_student()
        Notification.objects.create(userId=student.email, message='x', isRead=False)
        client = _login(student)
        resp = client.get(reverse('notifications_list'))
        self.assertContains(resp, 'Odczytaj wszystkie')


class DashboardShortcutsParityTests(TestCase):
    def test_moderator_sees_learning_shortcuts(self):
        client = _login(_verified_moderator())
        resp = client.get(reverse('dashboard'))
        self.assertContains(resp, reverse('exam_start'))
        self.assertContains(resp, reverse('my_stats'))
        self.assertContains(resp, reverse('material_create'))

    def test_admin_sees_learning_shortcuts(self):
        client = _login(_verified_admin())
        resp = client.get(reverse('dashboard'))
        self.assertContains(resp, reverse('exam_start'))
        self.assertContains(resp, reverse('my_stats'))


# ============================================================
# Admin ma moderację + zarobki jak moderator; „Co dalej" z linkami
# ============================================================
class AdminModerationParityTests(TestCase):
    def setUp(self):
        self.admin = _verified_admin()

    def test_admin_can_view_earnings(self):
        client = _login(self.admin)
        self.assertEqual(client.get(reverse('moderator_earnings')).status_code, 200)

    def test_admin_can_request_payout(self):
        # bez salda → redirect z komunikatem (ale dostęp jest)
        client = _login(self.admin)
        self.assertEqual(client.post(reverse('moderator_request_payout')).status_code, 302)

    def test_admin_earnings_method_works(self):
        stats = self.admin.viewModeratorStats()
        self.assertIn('available', stats)

    def test_admin_dashboard_has_moderation_links(self):
        client = _login(self.admin)
        resp = client.get(reverse('moderator_dashboard'))
        self.assertContains(resp, reverse('moderator_works_queue'))
        self.assertContains(resp, reverse('moderator_earnings'))


class ModeratorDashboardContentTests(TestCase):
    def setUp(self):
        self.mod = _verified_moderator()

    def test_codalej_has_works_and_earnings(self):
        client = _login(self.mod)
        resp = client.get(reverse('moderator_dashboard'))
        self.assertContains(resp, 'Prace do oceny')
        self.assertContains(resp, 'Zarobki')

    def test_has_weryfikacja_materialow_button(self):
        client = _login(self.mod)
        resp = client.get(reverse('moderator_dashboard'))
        self.assertContains(resp, 'Weryfikacja materiałów')

    def test_no_sprint_mentions(self):
        client = _login(self.mod)
        resp = client.get(reverse('moderator_dashboard'))
        self.assertNotContains(resp, 'Sprint')
        self.assertNotContains(resp, 'Sprinc')


# ============================================================
# Reset hasła a weryfikacja e-maila + ponowne wysłanie kodu
# ============================================================
class ResetAndVerificationTests(TestCase):
    def test_reset_marks_unverified_as_verified(self):
        # konto niezweryfikowane (świeża rejestracja)
        user = User.register('unv@uj.edu.pl', 'SilneHaslo123', 'U')
        self.assertFalse(user.emailVerified)
        token = PasswordResetToken.issue(user.email)
        Client().post(reverse('reset_password', args=[token.token]), {
            'password': 'NoweHaslo123', 'password_confirm': 'NoweHaslo123',
        })
        user.refresh_from_db()
        self.assertTrue(user.emailVerified)
        # po resecie da się od razu zalogować — bez ponownej weryfikacji
        self.assertIsNotNone(User.authenticate(user.email, 'NoweHaslo123'))

    def test_resend_sends_new_code(self):
        user = User.register('unv2@uj.edu.pl', 'SilneHaslo123', 'U')
        mail.outbox.clear()
        client = Client()
        session = client.session
        session['pending_verification_email'] = user.email
        session.save()
        resp = client.post(reverse('resend_verification_code'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('weryfikacyjny', mail.outbox[0].subject.lower())

    def test_resend_when_verified_redirects_no_email(self):
        user = _verified_student('ver@uj.edu.pl')
        client = Client()
        session = client.session
        session['pending_verification_email'] = user.email
        session.save()
        mail.outbox.clear()
        resp = client.post(reverse('resend_verification_code'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    def test_verify_page_has_resend_button(self):
        user = User.register('unv3@uj.edu.pl', 'SilneHaslo123', 'U')
        client = Client()
        session = client.session
        session['pending_verification_email'] = user.email
        session.save()
        resp = client.get(reverse('verify_email'))
        self.assertContains(resp, 'Wyślij kod ponownie')


# ============================================================
# Usuwanie konta (RODO)
# ============================================================
class DeleteAccountTests(TestCase):
    def test_confirmation_page_renders(self):
        client = _login(_verified_student('p@uj.edu.pl'))
        resp = client.get(reverse('delete_account'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'nieodwracalna')

    def test_wrong_password_does_not_delete(self):
        user = _verified_student('keep@uj.edu.pl')
        client = _login(user)
        resp = client.post(reverse('delete_account'), {'password': 'zleHaslo000'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(User.objects.filter(email='keep@uj.edu.pl').exists())

    def test_delete_removes_account_and_all_data(self):
        from ExtLearnerUJ.models import Vote, Work, Session
        user = _verified_student('del@uj.edu.pl')
        Material.objects.create(title='Mój', authorId=user.email,
                                category='grammar', status='PENDING')
        Notification.objects.create(userId=user.email, message='x')
        Vote.objects.create(userId=user.email, materialId='12345')
        Work.objects.create(title='Praca', description='d', studentId=user.email,
                            packageId='1', status=Work.STATUS_PENDING_PAYMENT)
        client = _login(user)
        resp = client.post(reverse('delete_account'), {'password': 'SilneHaslo123'})
        self.assertEqual(resp.status_code, 302)
        # konto i wszystkie dane zniknęły
        self.assertFalse(User.objects.filter(email='del@uj.edu.pl').exists())
        self.assertFalse(Student.objects.filter(email='del@uj.edu.pl').exists())
        self.assertFalse(Material.objects.filter(authorId='del@uj.edu.pl').exists())
        self.assertFalse(Notification.objects.filter(userId='del@uj.edu.pl').exists())
        self.assertFalse(Vote.objects.filter(userId='del@uj.edu.pl').exists())
        self.assertFalse(Work.objects.filter(studentId='del@uj.edu.pl').exists())
        self.assertFalse(Session.objects.filter(userId='del@uj.edu.pl').exists())
        # logowanie już niemożliwe
        self.assertIsNone(User.authenticate('del@uj.edu.pl', 'SilneHaslo123'))

    def test_dashboard_has_delete_link(self):
        client = _login(_verified_student('lnk@uj.edu.pl'))
        resp = client.get(reverse('dashboard'))
        self.assertContains(resp, reverse('delete_account'))


# ============================================================
# Test kwalifikacyjny we wniosku moderatorskim
# ============================================================
from ExtLearnerUJ.moderator_test import QUESTIONS, grade_answers


def _test_answers(all_correct=True):
    """Buduje słownik POST z odpowiedziami testu (poprawnymi lub błędnymi)."""
    data = {}
    for q in QUESTIONS:
        idx = q['correct'] if all_correct else (q['correct'] + 1) % len(q['options'])
        data[f"test_{q['id']}"] = str(idx)
    return data


class ModeratorQualificationTestTests(TestCase):
    def test_grade_answers(self):
        self.assertEqual(grade_answers(_test_answers(True)), 100.0)
        self.assertEqual(grade_answers(_test_answers(False)), 0.0)
        self.assertEqual(grade_answers({}), 0.0)

    def test_fail_auto_rejects_without_admin(self):
        student = _verified_student('fail@uj.edu.pl')
        client = _login(student)
        data = {'motivation': 'Chcę pomagać innym w nauce angielskiego!' * 2}
        data.update(_test_answers(all_correct=False))
        resp = client.post(reverse('apply_moderator'), data)
        self.assertEqual(resp.status_code, 302)
        app = ModeratorApplication.objects.get(candidateId=student.email)
        self.assertEqual(app.status, 'REJECTED')
        self.assertEqual(app.testScore, 0.0)
        # admin nie widzi: licznik PENDING = 0, lista wniosków pusta
        admin = _verified_admin('adm-q@uj.edu.pl')
        self.assertEqual(admin.viewSystemStats()['applications_pending'], 0)
        self.assertEqual(len(admin.reviewModeratorApplications()), 0)
        # kandydat dostał powiadomienie o odrzuceniu
        self.assertTrue(Notification.objects.filter(
            userId=student.email, message__icontains='odrzucony').exists())

    def test_pass_creates_pending_with_score(self):
        student = _verified_student('pass@uj.edu.pl')
        client = _login(student)
        data = {'motivation': 'Chcę pomagać innym w nauce angielskiego!' * 2}
        data.update(_test_answers(all_correct=True))
        client.post(reverse('apply_moderator'), data)
        app = ModeratorApplication.objects.get(candidateId=student.email)
        self.assertEqual(app.status, 'PENDING')
        self.assertEqual(app.testScore, 100.0)

    def test_admin_sees_score_in_review(self):
        student = _verified_student('seen@uj.edu.pl')
        student.applyForModerator(motivation='x' * 40, testScore=88.0)
        app = ModeratorApplication.objects.get(candidateId=student.email)
        admin = _verified_admin('adm-s@uj.edu.pl')
        client = _login(admin)
        resp = client.get(reverse('admin_review_application', args=[app.id]))
        self.assertContains(resp, 'Wynik testu kwalifikacyjnego')
        self.assertContains(resp, '88%')

    def test_can_retry_after_auto_reject(self):
        student = _verified_student('retry@uj.edu.pl')
        student.applyForModerator(motivation='x' * 40, testScore=10.0)  # auto-reject
        app2 = student.applyForModerator(motivation='y' * 40, testScore=90.0)
        self.assertEqual(app2.status, 'PENDING')


# ============================================================
# Rozliczenie indywidualne zamiast bramek płatności
# ============================================================
class DirectSettlementTests(TestCase):
    def setUp(self):
        self.student = _verified_student('zlec@uj.edu.pl')
        self.pkg = Package.objects.create(name='Podstawowy', price=15.0,
                                          scope='s', description='d')
        self.work = Work.objects.create(
            title='Esej', description='Treść.', studentId=self.student.email,
            packageId=str(self.pkg.id), status=Work.STATUS_PENDING_PAYMENT)

    def test_gateways_shown_as_disabled(self):
        client = _login(self.student)
        resp = client.get(reverse('work_payment', args=[self.work.id]))
        self.assertContains(resp, 'niedostępne')
        self.assertContains(resp, 'Rozliczenie indywidualne')

    def test_gateway_method_rejected(self):
        client = _login(self.student)
        client.post(reverse('work_payment', args=[self.work.id]), {'method': 'BLIK'})
        self.work.refresh_from_db()
        self.assertEqual(self.work.status, Work.STATUS_PENDING_PAYMENT)

    def test_direct_moves_work_to_queue(self):
        client = _login(self.student)
        resp = client.post(reverse('work_payment', args=[self.work.id]),
                           {'method': 'DIRECT'})
        self.assertEqual(resp.status_code, 302)
        self.work.refresh_from_db()
        self.assertEqual(self.work.status, Work.STATUS_PAID)

    def test_reservation_locks_and_notifies_student(self):
        self.work.status = Work.STATUS_PAID
        self.work.save(update_fields=['status'])
        mod1 = _verified_moderator('rez1@uj.edu.pl')
        mod2 = _verified_moderator('rez2@uj.edu.pl')
        self.assertTrue(mod1.reserveWork(self.work.id))
        # nikt inny nie może przejąć
        self.assertFalse(mod2.reserveWork(self.work.id))
        # zleceniodawca dostał powiadomienie z e-mailem sprawdzającego
        n = Notification.objects.filter(
            userId=self.student.email, message__icontains='zarezerwowana').first()
        self.assertIsNotNone(n)
        self.assertIn('rez1@uj.edu.pl', n.message)
        self.assertIn('rez1@uj.edu.pl', n.details)


# ============================================================
# Powiadomienia: „Pokaż szczegóły" z komentarzem
# ============================================================
class NotificationDetailsTests(TestCase):
    def test_material_verification_comment_in_details(self):
        mod = _verified_moderator('det-m@uj.edu.pl')
        mat = Material.objects.create(title='M', authorId='aut@uj.edu.pl',
                                      category='grammar', status='PENDING')
        mod.verifyMaterial(mat.id, 'NEEDS_REVISION',
                           comment='Popraw sekcję o czasach przeszłych.')
        n = Notification.objects.get(userId='aut@uj.edu.pl')
        self.assertIn('Popraw sekcję', n.details)

    def test_details_toggle_rendered(self):
        user = _verified_student('det-u@uj.edu.pl')
        Notification.objects.create(userId=user.email, message='Decyzja.',
                                    details='Długi komentarz do wglądu.')
        client = _login(user)
        resp = client.get(reverse('notifications_list'))
        self.assertContains(resp, 'Pokaż szczegóły')
        self.assertContains(resp, 'Długi komentarz do wglądu.')

    def test_no_toggle_without_details(self):
        user = _verified_student('det-n@uj.edu.pl')
        Notification.objects.create(userId=user.email, message='Krótkie.')
        client = _login(user)
        resp = client.get(reverse('notifications_list'))
        self.assertNotContains(resp, 'Pokaż szczegóły')


# ============================================================
# Zarobki: tylko statystyki, bez marży i wypłat
# ============================================================
class EarningsStatsOnlyTests(TestCase):
    def test_full_price_no_margin(self):
        from ExtLearnerUJ.services import StatisticsService
        mod = _verified_moderator('full@uj.edu.pl')
        pkg = Package.objects.create(name='Rozszerzony', price=25.0,
                                     scope='s', description='d')
        w = Work.objects.create(title='W', description='d', studentId='s@uj.edu.pl',
                                packageId=str(pkg.id), status=Work.STATUS_PAID)
        mod.reserveWork(w.id)
        rev = WorkReview.objects.create(workId=str(w.id), moderatorId=mod.email,
                                        grade='B2', generalComment='OK')
        rev.publish()
        stats = mod.viewModeratorStats()
        self.assertEqual(stats['total_earned'], 25.0)  # 100% ceny pakietu

    def test_earnings_page_has_no_payout_button(self):
        client = _login(_verified_moderator('nopay@uj.edu.pl'))
        resp = client.get(reverse('moderator_earnings'))
        self.assertNotContains(resp, 'Zleć wypłatę')
        self.assertNotContains(resp, 'faktur')
        self.assertContains(resp, 'nie pobiera marży')


class RankingHeadingTests(TestCase):
    def test_heading_renamed(self):
        client = _login(_verified_student('rank@uj.edu.pl'))
        resp = client.get(reverse('ranking'))
        self.assertContains(resp, 'Najaktywniejsi')
        self.assertNotContains(resp, 'Top 10')


# ============================================================
# Oceny sprawdzających, zarobek w kolejce, typy plików,
# powiadomienie o rezerwacji (regresja: admin)
# ============================================================
from ExtLearnerUJ.models import ModeratorRating


def _reviewed_work(student, moderator, price=25.0, title='Esej'):
    pkg = Package.objects.create(name=f'P{price}', price=price, scope='s', description='d')
    w = Work.objects.create(title=title, description='d', studentId=student.email,
                            packageId=str(pkg.id), status=Work.STATUS_PAID)
    moderator.reserveWork(w.id)
    WorkReview.objects.create(workId=str(w.id), moderatorId=moderator.email,
                              grade='B2', generalComment='OK',
                              status=WorkReview.STATUS_PUBLISHED)
    w.refresh_from_db()
    return w


class ModeratorRatingTests(TestCase):
    def setUp(self):
        self.student = _verified_student('oceniam@uj.edu.pl')
        self.mod = _verified_moderator('oceniany@uj.edu.pl')
        self.work = _reviewed_work(self.student, self.mod)

    def test_student_can_rate_after_review(self):
        client = _login(self.student)
        resp = client.post(reverse('rate_moderator', args=[self.work.id]),
                           {'score': '4', 'comment': 'Rzeczowo i na czas.'})
        self.assertEqual(resp.status_code, 302)
        r = ModeratorRating.objects.get(workId=str(self.work.id))
        self.assertEqual(r.score, 4)
        self.assertEqual(r.moderatorId, self.mod.email)

    def test_rating_overwrites_not_duplicates(self):
        self.student.rateModerator(self.work.id, 5)
        self.student.rateModerator(self.work.id, 2)
        self.assertEqual(ModeratorRating.objects.filter(workId=str(self.work.id)).count(), 1)
        self.assertEqual(ModeratorRating.objects.get(workId=str(self.work.id)).score, 2)

    def test_cannot_rate_unreviewed_work(self):
        pkg = Package.objects.create(name='X', price=15.0, scope='s', description='d')
        w2 = Work.objects.create(title='Nowa', description='d', studentId=self.student.email,
                                 packageId=str(pkg.id), status=Work.STATUS_PAID)
        self.assertIsNone(self.student.rateModerator(w2.id, 5))

    def test_cannot_rate_someone_elses_work(self):
        other = _verified_student('obcy@uj.edu.pl')
        self.assertIsNone(other.rateModerator(self.work.id, 1))

    def test_score_validation(self):
        self.assertIsNone(self.student.rateModerator(self.work.id, 0))
        self.assertIsNone(self.student.rateModerator(self.work.id, 6))
        self.assertIsNone(self.student.rateModerator(self.work.id, 'abc'))

    def test_admin_sees_average(self):
        w2 = _reviewed_work(self.student, self.mod, title='Drugi')
        self.student.rateModerator(self.work.id, 5)
        self.student.rateModerator(w2.id, 4)
        avg, cnt = ModeratorRating.average_for(self.mod.email)
        self.assertEqual((avg, cnt), (4.5, 2))
        admin = _verified_admin('adm-r@uj.edu.pl')
        client = _login(admin)
        resp = client.get(reverse('admin_user_detail', args=[self.mod.email]))
        self.assertContains(resp, 'Średnia ocen od zleceniodawców')
        self.assertContains(resp, '4,5')
        resp = client.get(reverse('admin_users_list') + '?role=moderator')
        self.assertContains(resp, '4,5')

    def test_rating_form_on_work_detail(self):
        client = _login(self.student)
        resp = client.get(reverse('work_detail', args=[self.work.id]))
        self.assertContains(resp, 'Oceń sprawdzającego')


class QueueEarningsTests(TestCase):
    def test_moderator_sees_earn_amount(self):
        mod = _verified_moderator('widzi@uj.edu.pl')
        pkg = Package.objects.create(name='Premium', price=40.0, scope='s', description='d')
        Work.objects.create(title='Praca40', description='d', studentId='s@uj.edu.pl',
                            packageId=str(pkg.id), status=Work.STATUS_PAID)
        client = _login(mod)
        resp = client.get(reverse('moderator_works_queue'))
        self.assertContains(resp, 'Zarobek')
        self.assertContains(resp, '40,0 zł')


class WorkFileTypesTests(TestCase):
    def _form(self, content_type):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from ExtLearnerUJ.forms import WorkForm
        pkg = Package.objects.first() or Package.objects.create(
            name='B', price=15.0, scope='s', description='d')
        f = SimpleUploadedFile('praca.bin', b'tresc', content_type=content_type)
        return WorkForm({'title': 'Tytuł pracy', 'description': '',
                         'package': pkg.id}, {'attachment': f})

    def test_image_types_now_accepted(self):
        self.assertTrue(self._form('image/jpeg').is_valid())
        self.assertTrue(self._form('image/png').is_valid())
        self.assertTrue(self._form('application/pdf').is_valid())

    def test_bad_type_still_rejected(self):
        form = self._form('application/zip')
        self.assertFalse(form.is_valid())
        self.assertIn('attachment', form.errors)


class AdminReservationNotificationTests(TestCase):
    """Regresja: rezerwacja przez ADMINA też musi powiadamiać zleceniodawcę."""
    def test_admin_reserve_notifies_student(self):
        student = _verified_student('powiadom@uj.edu.pl')
        admin = _verified_admin('adm-rez@uj.edu.pl')
        pkg = Package.objects.create(name='B', price=15.0, scope='s', description='d')
        w = Work.objects.create(title='Praca', description='d', studentId=student.email,
                                packageId=str(pkg.id), status=Work.STATUS_PAID)
        client = _login(admin)
        resp = client.post(reverse('moderator_reserve_work', args=[w.id]))
        self.assertEqual(resp.status_code, 302)
        w.refresh_from_db()
        self.assertEqual(w.assignedModeratorId, admin.email)
        n = Notification.objects.filter(
            userId=student.email, message__icontains='zarezerwowana').first()
        self.assertIsNotNone(n)
        self.assertIn(admin.email, n.message)

    def test_double_reserve_sends_one_notification(self):
        student = _verified_student('jeden@uj.edu.pl')
        mod = _verified_moderator('m-rez@uj.edu.pl')
        pkg = Package.objects.create(name='B', price=15.0, scope='s', description='d')
        w = Work.objects.create(title='Praca', description='d', studentId=student.email,
                                packageId=str(pkg.id), status=Work.STATUS_PAID)
        mod.reserveWork(w.id)
        mod.reserveWork(w.id)  # idempotentnie
        self.assertEqual(Notification.objects.filter(
            userId=student.email, message__icontains='zarezerwowana').count(), 1)
