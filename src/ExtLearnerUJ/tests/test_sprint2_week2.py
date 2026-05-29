"""
Testy Sprintu 2 (tydzień 2) — prace pisemne, płatności, edytor błędów,
panel admina.

Pokrywa: FR-10, FR-11, FR-15, UC19, UC20, UC21, UC38, UC39, UC40,
UC41, UC42, UC46, UC47, UC48.
"""
import json

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from ExtLearnerUJ.models import (
    User, Student, Moderator, Admin, EmailVerificationToken,
    Material, Work, Package, PaymentTransaction,
    WorkReview, ErrorMark, Notification, Report,
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
    return Moderator.objects.create(
        email=email,
        password=make_password(password),
        name='Test Moderator',
        status=User.STATUS_ACTIVE,
        emailVerified=True,
    )


def _verified_admin(email='admin@uj.edu.pl', password='SilneHaslo123'):
    return Admin.objects.create(
        email=email,
        password=make_password(password),
        name='Test Admin',
        status=User.STATUS_ACTIVE,
        emailVerified=True,
    )


def _login_client(user, password='SilneHaslo123'):
    session = User.authenticate(user.email, password)
    client = Client()
    client.cookies[settings.SESSION_COOKIE_NAME_APP] = session.token
    return client


def _mk_package(name='Podstawowy', price=15.0):
    return Package.objects.create(
        name=name, price=price, scope='test scope', description='test description',
    )


# ============================================================
# FR-15: Wysłanie pracy + płatność
# ============================================================
class WorkSubmissionTests(TestCase):
    def setUp(self):
        self.student = _verified_student()
        self.client = _login_client(self.student)
        self.package = _mk_package()

    def test_new_form_accessible(self):
        response = self.client.get(reverse('work_new'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Podstawowy')
        self.assertContains(response, '15.0 zł')

    def test_submit_work_creates_pending_payment(self):
        response = self.client.post(reverse('work_new'), {
            'title': 'My essay',
            'description': 'This is my opinion essay on free education. ' * 5,
            'package': self.package.id,
        })
        self.assertEqual(response.status_code, 302)
        work = Work.objects.get(studentId=self.student.email)
        self.assertEqual(work.status, Work.STATUS_PENDING_PAYMENT)
        self.assertEqual(work.title, 'My essay')

    def test_submit_requires_content_or_file(self):
        response = self.client.post(reverse('work_new'), {
            'title': 'Empty', 'description': '',
            'package': self.package.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Work.objects.filter(title='Empty').exists())

    def test_submit_accepts_pdf(self):
        pdf = SimpleUploadedFile(
            'essay.pdf', b'PDF-like', content_type='application/pdf',
        )
        response = self.client.post(reverse('work_new'), {
            'title': 'Essay with PDF', 'description': '',
            'package': self.package.id, 'attachment': pdf,
        })
        self.assertEqual(response.status_code, 302)
        work = Work.objects.get(studentId=self.student.email)
        self.assertEqual(work.attachments.count(), 1)

    def test_requires_student_role(self):
        mod = _verified_moderator('ineligible@uj.edu.pl')
        client = _login_client(mod)
        response = client.get(reverse('work_new'))
        self.assertEqual(response.status_code, 403)


class PaymentFlowTests(TestCase):
    def setUp(self):
        self.student = _verified_student()
        self.client = _login_client(self.student)
        self.package = _mk_package()

        # Utwórz pracę bezpośrednio (pomija formularz)
        self.work = Work.objects.create(
            title='Essay', description='xxx',
            studentId=self.student.email,
            packageId=str(self.package.id),
            status=Work.STATUS_PENDING_PAYMENT,
        )

    def test_payment_page_shows_package_price(self):
        response = self.client.get(reverse('work_payment', args=[self.work.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '15.0 zł')

    def test_payment_processes_and_transitions_work_to_paid(self):
        response = self.client.post(
            reverse('work_payment', args=[self.work.id]),
            {'method': 'BLIK'},
        )
        self.assertEqual(response.status_code, 302)
        self.work.refresh_from_db()
        self.assertEqual(self.work.status, Work.STATUS_PAID)
        self.assertEqual(PaymentTransaction.objects.count(), 1)
        tx = PaymentTransaction.objects.first()
        self.assertEqual(tx.status, PaymentTransaction.STATUS_COMPLETED)

    def test_cant_pay_for_others_work(self):
        other = _verified_student('ktos-inny@uj.edu.pl')
        other_client = _login_client(other)
        response = other_client.get(
            reverse('work_payment', args=[self.work.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_already_paid_redirects_to_detail(self):
        self.work.status = Work.STATUS_PAID
        self.work.save()
        response = self.client.get(reverse('work_payment', args=[self.work.id]))
        self.assertEqual(response.status_code, 302)


class MyWorksTests(TestCase):
    def test_list_shows_only_own(self):
        student = _verified_student()
        other = _verified_student('inny@uj.edu.pl')
        pkg = _mk_package()

        Work.objects.create(
            title='My work', studentId=student.email, packageId=str(pkg.id),
            status=Work.STATUS_PAID,
        )
        Work.objects.create(
            title='Their work', studentId=other.email, packageId=str(pkg.id),
            status=Work.STATUS_PAID,
        )

        client = _login_client(student)
        response = client.get(reverse('my_works'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My work')
        self.assertNotContains(response, 'Their work')


# ============================================================
# FR-10: Edytor recenzji (UC38, UC39, UC40, UC41, UC42)
# ============================================================
class WorkReviewFlowTests(TestCase):
    def setUp(self):
        self.student = _verified_student()
        self.mod = _verified_moderator()
        self.pkg = _mk_package()

        self.work = Work.objects.create(
            title='Essay',
            description='This is my essay text with various mistakes. ' * 3,
            studentId=self.student.email,
            packageId=str(self.pkg.id),
            status=Work.STATUS_PAID,
        )

    def test_moderator_sees_paid_work_in_queue(self):
        client = _login_client(self.mod)
        response = client.get(reverse('moderator_works_queue'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Essay')

    def test_reserve_assigns_moderator(self):
        client = _login_client(self.mod)
        response = client.post(reverse('moderator_reserve_work', args=[self.work.id]))
        self.assertEqual(response.status_code, 302)
        self.work.refresh_from_db()
        self.assertEqual(self.work.assignedModeratorId, self.mod.email)
        self.assertEqual(self.work.status, Work.STATUS_IN_REVIEW)

    def test_reserve_fails_if_already_taken(self):
        other_mod = _verified_moderator('inny-mod@uj.edu.pl')
        self.work.assignModerator(other_mod.email)

        client = _login_client(self.mod)
        response = client.post(reverse('moderator_reserve_work', args=[self.work.id]))
        self.assertEqual(response.status_code, 302)
        self.work.refresh_from_db()
        # Nadal przypisane do other_mod
        self.assertEqual(self.work.assignedModeratorId, other_mod.email)

    def test_editor_shows_work_content(self):
        self.work.assignModerator(self.mod.email)
        client = _login_client(self.mod)
        response = client.get(reverse('moderator_work_editor', args=[self.work.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'my essay text')

    def test_editor_blocks_unassigned_moderator(self):
        """Moderator nie może otworzyć edytora dla pracy nieprzypisanej do niego."""
        other_mod = _verified_moderator('inny@uj.edu.pl')
        self.work.assignModerator(other_mod.email)

        client = _login_client(self.mod)
        response = client.get(reverse('moderator_work_editor', args=[self.work.id]))
        self.assertEqual(response.status_code, 302)

    def test_save_draft_review(self):
        self.work.assignModerator(self.mod.email)
        client = _login_client(self.mod)
        response = client.post(reverse('moderator_work_editor', args=[self.work.id]), {
            'action': 'save',
            'grade': 'B2',
            'generalComment': 'Good effort but needs more practice. ' * 2,
        })
        self.assertEqual(response.status_code, 302)
        review = WorkReview.objects.get(workId=str(self.work.id))
        self.assertEqual(review.status, WorkReview.STATUS_DRAFT)
        self.assertEqual(review.grade, 'B2')

    def test_publish_transitions_work_to_reviewed_and_notifies_student(self):
        self.work.assignModerator(self.mod.email)
        client = _login_client(self.mod)
        response = client.post(reverse('moderator_work_editor', args=[self.work.id]), {
            'action': 'publish',
            'grade': 'B2+',
            'generalComment': 'Well-structured essay with minor grammar issues. ' * 2,
        })
        self.assertEqual(response.status_code, 302)
        self.work.refresh_from_db()
        self.assertEqual(self.work.status, Work.STATUS_REVIEWED)

        review = WorkReview.objects.get(workId=str(self.work.id))
        self.assertEqual(review.status, WorkReview.STATUS_PUBLISHED)

        # Notyfikacja dla studenta
        self.assertTrue(
            Notification.objects.filter(
                userId=self.student.email
            ).filter(message__contains='sprawdzona').exists()
        )

    def test_add_error_mark_ajax(self):
        self.work.assignModerator(self.mod.email)
        review = WorkReview.objects.create(
            workId=str(self.work.id), moderatorId=self.mod.email,
            status=WorkReview.STATUS_DRAFT,
        )
        client = _login_client(self.mod)

        payload = {
            'snippet': 'various mistakes',
            'type': 'GRAMMAR',
            'position': '',
            'comment': 'Should be "several"',
        }
        response = client.post(
            reverse('moderator_add_error_mark', args=[review.id]),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ErrorMark.objects.filter(reviewId=str(review.id)).count(), 1)

    def test_delete_error_mark(self):
        self.work.assignModerator(self.mod.email)
        review = WorkReview.objects.create(
            workId=str(self.work.id), moderatorId=self.mod.email,
        )
        mark = ErrorMark.objects.create(
            reviewId=str(review.id),
            textSnippet='test', type=ErrorMark.TYPE_GRAMMAR,
        )
        client = _login_client(self.mod)
        response = client.post(
            reverse('moderator_delete_error_mark', args=[mark.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ErrorMark.objects.filter(pk=mark.id).exists())

    def test_cant_delete_others_mark(self):
        """Moderator nie może usunąć zaznaczenia z recenzji innego moderatora."""
        other_mod = _verified_moderator('inny@uj.edu.pl')
        other_review = WorkReview.objects.create(
            workId='999', moderatorId=other_mod.email,
        )
        mark = ErrorMark.objects.create(
            reviewId=str(other_review.id),
            textSnippet='x', type=ErrorMark.TYPE_GRAMMAR,
        )
        client = _login_client(self.mod)
        response = client.post(
            reverse('moderator_delete_error_mark', args=[mark.id])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ErrorMark.objects.filter(pk=mark.id).exists())


# ============================================================
# FR-11, UC46, UC47, UC48: Panel admina
# ============================================================
class AdminDashboardTests(TestCase):
    def test_requires_admin_role(self):
        student = _verified_student()
        client = _login_client(student)
        response = client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_admin_sees_stats(self):
        admin = _verified_admin()
        client = _login_client(admin)
        response = client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Statystyki')


class AdminReportsTests(TestCase):
    def setUp(self):
        self.admin = _verified_admin()
        self.reporter = _verified_student('reporter@uj.edu.pl')
        self.client = _login_client(self.admin)

        self.report = Report.objects.create(
            reporterId=self.reporter.email,
            targetType=Report.TARGET_MATERIAL,
            targetId='42',
            reason='Ten materiał jest pełen błędów gramatycznych.',
            status=Report.STATUS_PENDING,
        )

    def test_queue_shows_pending_only(self):
        # Rozpatrzone zgłoszenie nie powinno się pokazać
        Report.objects.create(
            reporterId='inny@uj.edu.pl', targetType='MATERIAL',
            targetId='99', reason='Stare', status=Report.STATUS_RESOLVED,
        )
        response = self.client.get(reverse('admin_reports_queue'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'pełen błędów')
        self.assertNotContains(response, 'Stare')

    def test_resolve_report_notifies_reporter(self):
        response = self.client.post(
            reverse('admin_review_report', args=[self.report.id]),
            {'decision': 'RESOLVED', 'comment': ''},
        )
        self.assertEqual(response.status_code, 302)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, Report.STATUS_RESOLVED)
        self.assertEqual(self.report.resolvedBy, self.admin.email)

        # Notyfikacja dla zgłaszającego
        self.assertTrue(
            Notification.objects.filter(
                userId=self.reporter.email,
            ).filter(message__contains='zasadne').exists()
        )

    def test_dismiss_report_notifies_reporter(self):
        response = self.client.post(
            reverse('admin_review_report', args=[self.report.id]),
            {'decision': 'DISMISSED', 'comment': ''},
        )
        self.assertEqual(response.status_code, 302)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, Report.STATUS_DISMISSED)


class AdminUserManagementTests(TestCase):
    def setUp(self):
        self.admin = _verified_admin()
        self.target = _verified_student('target@uj.edu.pl')
        self.client = _login_client(self.admin)

    def test_users_list_shows_all(self):
        response = self.client.get(reverse('admin_users_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'target@uj.edu.pl')
        self.assertContains(response, 'admin@uj.edu.pl')

    def test_user_detail_shows_status(self):
        response = self.client.get(
            reverse('admin_user_detail', args=[self.target.email])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.target.name)

    def test_block_user_temporary(self):
        response = self.client.post(
            reverse('admin_user_detail', args=[self.target.email]),
            {'duration': '7', 'reason': 'Repeated spam postings.'},
        )
        self.assertEqual(response.status_code, 302)
        self.target.refresh_from_db()
        self.assertEqual(self.target.status, User.STATUS_BLOCKED)

    def test_block_user_permanent(self):
        response = self.client.post(
            reverse('admin_user_detail', args=[self.target.email]),
            {'duration': 'permanent', 'reason': 'Severe violation.'},
        )
        self.assertEqual(response.status_code, 302)
        self.target.refresh_from_db()
        self.assertEqual(self.target.status, User.STATUS_BLOCKED)

    def test_blocked_user_cant_login(self):
        self.admin.manageUserAccount(
            userId=self.target.email,
            newStatus=User.STATUS_BLOCKED,
            days=7,
        )
        # Po blokadzie authenticate powinno zwrócić None
        self.assertIsNone(
            User.authenticate('target@uj.edu.pl', 'SilneHaslo123')
        )

    def test_unblock_restores_access(self):
        self.admin.manageUserAccount(
            userId=self.target.email,
            newStatus=User.STATUS_BLOCKED,
        )
        response = self.client.post(
            reverse('admin_unblock_user', args=[self.target.email])
        )
        self.assertEqual(response.status_code, 302)
        self.target.refresh_from_db()
        self.assertEqual(self.target.status, User.STATUS_ACTIVE)
        # I teraz authenticate zadziała
        session = User.authenticate('target@uj.edu.pl', 'SilneHaslo123')
        self.assertIsNotNone(session)

    def test_block_notifies_user(self):
        self.client.post(
            reverse('admin_user_detail', args=[self.target.email]),
            {'duration': '7', 'reason': 'test'},
        )
        self.assertTrue(
            Notification.objects.filter(userId=self.target.email).exists()
        )


# ============================================================
# Model-level unit tests
# ============================================================
class WorkModelTests(TestCase):
    def test_submit_creates_work_in_pending_payment(self):
        student = _verified_student()
        pkg = _mk_package()
        work = student.submitWork(
            workData={'title': 'T', 'description': 'D'},
            packageId=pkg.id, files=None,
        )
        self.assertIsNotNone(work)
        self.assertEqual(work.status, Work.STATUS_PENDING_PAYMENT)
        self.assertEqual(work.studentId, student.email)

    def test_submit_with_invalid_package_returns_none(self):
        student = _verified_student()
        result = student.submitWork(
            workData={'title': 'T'}, packageId=99999, files=None,
        )
        self.assertIsNone(result)

    def test_payment_transaction_process_success(self):
        pkg = _mk_package()
        work = Work.objects.create(
            title='T', studentId='s@uj.edu.pl', packageId=str(pkg.id),
            status=Work.STATUS_PENDING_PAYMENT,
        )
        tx = PaymentTransaction.objects.create(
            workId=str(work.id), userId='s@uj.edu.pl',
            amount=pkg.price, method='BLIK',
        )
        self.assertTrue(tx.process())
        tx.refresh_from_db()
        self.assertEqual(tx.status, PaymentTransaction.STATUS_COMPLETED)

        work.refresh_from_db()
        self.assertEqual(work.status, Work.STATUS_PAID)

    def test_payment_fails_on_zero_amount(self):
        tx = PaymentTransaction.objects.create(
            workId='1', userId='x@uj.edu.pl', amount=0.0,
        )
        self.assertFalse(tx.process())
        tx.refresh_from_db()
        self.assertEqual(tx.status, PaymentTransaction.STATUS_FAILED)


class WorkReviewModelTests(TestCase):
    def test_publish_transitions_work_and_creates_notification(self):
        pkg = _mk_package()
        student = _verified_student()
        work = Work.objects.create(
            title='W', description='d',
            studentId=student.email, packageId=str(pkg.id),
            status=Work.STATUS_IN_REVIEW,
        )
        review = WorkReview.objects.create(
            workId=str(work.id), moderatorId='m@uj.edu.pl',
            grade='B2', generalComment='ok',
        )
        self.assertTrue(review.publish())
        work.refresh_from_db()
        self.assertEqual(work.status, Work.STATUS_REVIEWED)
        self.assertTrue(
            Notification.objects.filter(userId=student.email).exists()
        )


class AdminStatsTests(TestCase):
    def test_system_stats_returns_correct_counts(self):
        admin = _verified_admin()
        _verified_student('a@uj.edu.pl')
        _verified_student('b@uj.edu.pl')
        _verified_moderator()

        stats = admin.viewSystemStats()
        self.assertEqual(stats['total_students'], 2)
        self.assertEqual(stats['total_moderators'], 1)
        self.assertEqual(stats['total_admins'], 1)
        self.assertEqual(stats['reports_open'], 0)
