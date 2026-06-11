"""
Testy Sprintu 3 — rekomendacje (FR-05), symulacja egzaminu z twardym timerem
(FR-06), ranking/gamifikacja (FR-07), wnioski moderatorskie i zarządzanie
rolami (FR-12), wypłaty moderatorów (FR-14) oraz raport PDF (UC15).
"""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from ExtLearnerUJ.models import (
    User, Student, Moderator, Admin, EmailVerificationToken,
    Material, DiagnosticTest, DiagnosticResult, Question,
    Test, ExamAttempt, UserStats, Payout, ModeratorApplication,
    Work, Package, WorkReview, Notification,
    promote_to_moderator, demote_to_student,
)
from ExtLearnerUJ.services import (
    RecommendationService, RankingService, StatisticsService, ReportGenerator,
)


# ============================================================
# Helpery (spójne z testami Sprintu 2)
# ============================================================
def _verified_student(email='stud@uj.edu.pl', password='SilneHaslo123', name='Test Student'):
    user = User.register(email, password, name)
    token = EmailVerificationToken.objects.get(userId=email).token
    user.verifyEmail(token)
    return user


def _verified_moderator(email='mod@uj.edu.pl', password='SilneHaslo123'):
    return Moderator.objects.create(
        email=email, password=make_password(password), name='Test Moderator',
        status=User.STATUS_ACTIVE, emailVerified=True,
    )


def _verified_admin(email='admin@uj.edu.pl', password='SilneHaslo123'):
    return Admin.objects.create(
        email=email, password=make_password(password), name='Test Admin',
        status=User.STATUS_ACTIVE, emailVerified=True,
    )


def _login_client(user, password='SilneHaslo123'):
    session = User.authenticate(user.email, password)
    client = Client()
    client.cookies[settings.SESSION_COOKIE_NAME_APP] = session.token
    return client


def _mk_exam(duration=30):
    test = Test.objects.create(
        title='Symulacja egzaminu', type=Test.TYPE_EXAM, durationMinutes=duration,
    )
    q1 = Question.objects.create(
        test=test, text='2+2?', qType=Question.QTYPE_SINGLE,
        options=['3', '4'], correctAnswer='4', area='grammar', points=1,
    )
    q2 = Question.objects.create(
        test=test, text='Opposite of hot?', qType=Question.QTYPE_SINGLE,
        options=['cold', 'warm'], correctAnswer='cold', area='vocabulary', points=1,
    )
    return test, q1, q2


# ============================================================
# FR-05 — rekomendacje materiałów
# ============================================================
class RecommendationTests(TestCase):
    def setUp(self):
        self.student = _verified_student()
        # Słaby wynik w 'grammar' (30%), dobry w 'reading' (80%).
        DiagnosticResult.objects.create(
            testId='1', userId=self.student.email, score=55.0, answers={},
            areaScores={'grammar': 30.0, 'reading': 80.0},
        )
        self.weak_mat = Material.objects.create(
            title='Grammar drills', authorId='x@uj.edu.pl', category='grammar',
            status=Material.STATUS_VERIFIED, isVerified=True,
        )
        # Materiał w mocnym obszarze — nie powinien być rekomendowany.
        Material.objects.create(
            title='Reading set', authorId='x@uj.edu.pl', category='reading',
            status=Material.STATUS_VERIFIED, isVerified=True,
        )

    def test_service_recommends_only_weak_areas(self):
        recs = RecommendationService().getRecommendationsForUser(self.student.email)
        areas = [r['area'] for r in recs]
        self.assertIn('grammar', areas)
        self.assertNotIn('reading', areas)

    def test_service_skips_unverified_materials(self):
        Material.objects.create(
            title='Unverified grammar', authorId='x@uj.edu.pl', category='grammar',
            status=Material.STATUS_PENDING, isVerified=False,
        )
        recs = RecommendationService().getRecommendationsForUser(self.student.email)
        grammar = next(r for r in recs if r['area'] == 'grammar')
        titles = [m.title for m in grammar['materials']]
        self.assertIn('Grammar drills', titles)
        self.assertNotIn('Unverified grammar', titles)

    def test_no_recommendations_without_diagnostic(self):
        other = _verified_student(email='new@uj.edu.pl')
        recs = RecommendationService().getRecommendationsForUser(other.email)
        self.assertEqual(recs, [])

    def test_dashboard_shows_recommendations(self):
        client = _login_client(self.student)
        response = client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rekomendowane dla Ciebie')
        self.assertContains(response, 'Grammar drills')


# ============================================================
# FR-06 — symulacja egzaminu z twardym timerem
# ============================================================
class ExamSimulationTests(TestCase):
    def setUp(self):
        self.student = _verified_student()
        self.client = _login_client(self.student)
        self.test, self.q1, self.q2 = _mk_exam(duration=30)

    def test_start_creates_attempt_with_deadline(self):
        response = self.client.post(reverse('exam_start'))
        self.assertEqual(response.status_code, 302)
        attempt = ExamAttempt.objects.get(userId=self.student.email)
        self.assertEqual(attempt.status, ExamAttempt.STATUS_IN_PROGRESS)
        self.assertIsNotNone(attempt.deadline)
        self.assertGreater(attempt.seconds_left(), 0)

    def test_take_page_renders_timer(self):
        attempt = ExamAttempt.start(self.test, self.student.email)
        response = self.client.get(reverse('exam_take', args=[attempt.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'exam-timer')

    def test_submit_scores_and_awards_points(self):
        attempt = ExamAttempt.start(self.test, self.student.email)
        response = self.client.post(reverse('exam_take', args=[attempt.id]), {
            f'q_{self.q1.id}': '4',          # poprawnie
            f'q_{self.q2.id}': 'warm',       # błędnie
        })
        self.assertEqual(response.status_code, 302)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, ExamAttempt.STATUS_SUBMITTED)
        self.assertEqual(attempt.score, 50.0)
        self.assertEqual(attempt.pointsAwarded, 50)
        stats = UserStats.objects.get(userId=self.student.email)
        self.assertEqual(stats.points, 50)
        self.assertEqual(stats.examsCompleted, 1)

    def test_expired_attempt_autosubmits_on_open(self):
        attempt = ExamAttempt.start(self.test, self.student.email)
        # Symuluj upłynięcie czasu.
        attempt.deadline = timezone.now() - timedelta(seconds=1)
        attempt.save(update_fields=['deadline'])
        response = self.client.get(reverse('exam_take', args=[attempt.id]), follow=True)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, ExamAttempt.STATUS_SUBMITTED)
        # Po wygaśnięciu trafiamy na wynik.
        self.assertContains(response, 'Wynik')

    def test_autosave_rejected_after_deadline(self):
        attempt = ExamAttempt.start(self.test, self.student.email)
        attempt.deadline = timezone.now() - timedelta(seconds=1)
        attempt.save(update_fields=['deadline'])
        response = self.client.post(
            reverse('exam_autosave', args=[attempt.id]),
            data='{"answers": {"1": "4"}}', content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['expired'])
        self.assertFalse(payload['ok'])

    def test_autosave_persists_answers(self):
        attempt = ExamAttempt.start(self.test, self.student.email)
        response = self.client.post(
            reverse('exam_autosave', args=[attempt.id]),
            data=f'{{"answers": {{"{self.q1.id}": "4"}}}}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        attempt.refresh_from_db()
        self.assertEqual(attempt.answers.get(str(self.q1.id)), '4')

    def test_no_exam_seeded_redirects(self):
        Test.objects.filter(type=Test.TYPE_EXAM).delete()
        response = self.client.get(reverse('exam_start'))
        self.assertEqual(response.status_code, 302)


# ============================================================
# FR-07 — ranking / gamifikacja
# ============================================================
class RankingTests(TestCase):
    def setUp(self):
        self.s1 = _verified_student(email='a@uj.edu.pl', name='Alice')
        self.s2 = _verified_student(email='b@uj.edu.pl', name='Bob')
        UserStats.record_exam(self.s1.email, 90)
        UserStats.record_exam(self.s2.email, 40)

    def test_ranking_sorted_desc(self):
        ranking = RankingService().getStudentRanking()
        self.assertEqual(ranking[0]['name'], 'Alice')
        self.assertEqual(ranking[0]['points'], 90)
        self.assertEqual(ranking[1]['name'], 'Bob')

    def test_user_position(self):
        self.assertEqual(RankingService().getUserPosition(self.s1.email), 1)
        self.assertEqual(RankingService().getUserPosition(self.s2.email), 2)

    def test_ranking_page_renders(self):
        client = _login_client(self.s1)
        response = client.get(reverse('ranking'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alice')
        self.assertContains(response, 'Bob')

    def test_zero_points_excluded(self):
        _verified_student(email='c@uj.edu.pl', name='Carol')  # 0 pkt
        ranking = RankingService().getStudentRanking()
        names = [r['name'] for r in ranking]
        self.assertNotIn('Carol', names)


# ============================================================
# FR-12 — wnioski moderatorskie + zarządzanie rolami
# ============================================================
class ModeratorApplicationTests(TestCase):
    def setUp(self):
        self.student = _verified_student()
        self.admin = _verified_admin()

    def test_student_can_apply(self):
        from ExtLearnerUJ.moderator_test import QUESTIONS
        client = _login_client(self.student)
        data = {'motivation': 'Mam certyfikat CAE i chcę pomagać innym studentom UJ.'}
        # poprawne odpowiedzi testu kwalifikacyjnego
        for q in QUESTIONS:
            data[f"test_{q['id']}"] = str(q['correct'])
        response = client.post(reverse('apply_moderator'), data)
        self.assertEqual(response.status_code, 302)
        app = ModeratorApplication.objects.get(candidateId=self.student.email)
        self.assertEqual(app.status, 'PENDING')
        self.assertEqual(app.testScore, 100.0)

    def test_duplicate_application_returns_existing(self):
        self.student.applyForModerator(motivation='x' * 40)
        self.student.applyForModerator(motivation='y' * 40)
        self.assertEqual(
            ModeratorApplication.objects.filter(candidateId=self.student.email).count(),
            1,
        )

    def test_admin_accept_promotes_to_moderator(self):
        app = self.student.applyForModerator(motivation='x' * 40)
        self.assertTrue(self.admin.acceptCandidate(app.id))
        app.refresh_from_db()
        self.assertEqual(app.status, 'ACCEPTED')
        # Rola rozstrzygana po tabeli potomnej — teraz to Moderator.
        self.assertTrue(Moderator.objects.filter(pk=self.student.pk).exists())
        self.assertFalse(Student.objects.filter(pk=self.student.pk).exists())
        # Kandydat dostaje powiadomienie.
        self.assertTrue(
            Notification.objects.filter(userId=self.student.email).exists()
        )

    def test_promoted_user_resolves_as_moderator_in_request(self):
        app = self.student.applyForModerator(motivation='x' * 40)
        self.admin.acceptCandidate(app.id)
        client = _login_client(self.student)
        # Panel moderatora jest teraz dostępny (rola = Moderator).
        response = client.get(reverse('moderator_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_admin_reject(self):
        app = self.student.applyForModerator(motivation='x' * 40)
        self.assertTrue(self.admin.rejectCandidate(app.id, reason='Brak certyfikatu'))
        app.refresh_from_db()
        self.assertEqual(app.status, 'REJECTED')
        self.assertFalse(Moderator.objects.filter(pk=self.student.pk).exists())

    def test_revoke_moderator(self):
        app = self.student.applyForModerator(motivation='x' * 40)
        self.admin.acceptCandidate(app.id)
        self.assertTrue(self.admin.revokeModerator(self.student.email))
        self.assertFalse(Moderator.objects.filter(pk=self.student.pk).exists())
        self.assertTrue(Student.objects.filter(pk=self.student.pk).exists())

    def test_admin_applications_page(self):
        self.student.applyForModerator(motivation='x' * 40)
        client = _login_client(self.admin)
        response = client.get(reverse('admin_applications'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student.email)


# ============================================================
# FR-14 — wypłaty moderatorów
# ============================================================
class PayoutTests(TestCase):
    def setUp(self):
        self.moderator = _verified_moderator()
        self.package = Package.objects.create(
            name='Rozszerzony', price=25.0, scope='s', description='d',
        )
        # Dwie opublikowane oceny → 2 × 25 zł (bez marży) = 50 zł.
        for i in range(2):
            work = Work.objects.create(
                title=f'Praca {i}', studentId='s@uj.edu.pl',
                packageId=str(self.package.id), status=Work.STATUS_REVIEWED,
                assignedModeratorId=self.moderator.email,
            )
            WorkReview.objects.create(
                workId=str(work.id), moderatorId=self.moderator.email,
                grade='B2', generalComment='ok', status=WorkReview.STATUS_PUBLISHED,
            )

    def test_earnings_computed(self):
        stats = StatisticsService().getModeratorStats(self.moderator.email)
        self.assertEqual(stats['reviewed_count'], 2)
        self.assertEqual(stats['total_earned'], 50.0)
        self.assertEqual(stats['available'], 50.0)

    def test_request_payout_creates_invoice(self):
        payout = self.moderator.requestPayout()
        self.assertIsNotNone(payout)
        self.assertEqual(payout.amount, 50.0)
        self.assertTrue(payout.invoiceNumber.startswith('FV/'))

    def test_payout_reduces_available(self):
        self.moderator.requestPayout()
        stats = StatisticsService().getModeratorStats(self.moderator.email)
        self.assertEqual(stats['available'], 0.0)
        self.assertEqual(stats['paid_out'], 50.0)

    def test_request_payout_with_no_balance(self):
        fresh = _verified_moderator(email='mod2@uj.edu.pl')
        self.assertIsNone(fresh.requestPayout())

    def test_earnings_page_renders(self):
        client = _login_client(self.moderator)
        response = client.get(reverse('moderator_earnings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panel finansowy')
        self.assertContains(response, 'zarobiono łącznie')
        self.assertNotContains(response, 'dostępne saldo')


# ============================================================
# UC15 — raport PDF
# ============================================================
class LearningReportTests(TestCase):
    def setUp(self):
        self.student = _verified_student()
        UserStats.record_exam(self.student.email, 70)

    def test_report_generator_returns_valid_pdf(self):
        pdf = ReportGenerator().buildPdf(self.student.email)
        self.assertIsInstance(pdf, (bytes, bytearray))
        self.assertTrue(pdf.startswith(b'%PDF-1.'))
        self.assertIn(b'%%EOF', pdf)

    def test_report_endpoint_serves_pdf(self):
        client = _login_client(self.student)
        response = client.get(reverse('learning_report_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_stats_page_renders(self):
        client = _login_client(self.student)
        response = client.get(reverse('my_stats'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Statystyki nauki')


# ============================================================
# Regresja — naprawiony konflikt merge w szablonach
# ============================================================
class TemplateRegressionTests(TestCase):
    def test_material_detail_renders(self):
        student = _verified_student()
        client = _login_client(student)
        material = Material.objects.create(
            title='Test material', authorId='x@uj.edu.pl', category='grammar',
            status=Material.STATUS_VERIFIED, isVerified=True,
        )
        response = client.get(reverse('material_detail', args=[material.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<<<<<<<')
        self.assertNotContains(response, '>>>>>>>')


# ============================================================
# Diagnostyka przyznaje punkty (gamifikacja przy ukończeniu)
# ============================================================
class DiagnosticPointsTests(TestCase):
    def test_diagnostic_completion_awards_points(self):
        student = _verified_student()
        test = DiagnosticTest.objects.create(title='Diag', type='DIAGNOSTIC')
        q = Question.objects.create(
            test=test, text='2+2?', options=['3', '4'], correctAnswer='4',
            area='grammar', points=1,
        )
        from ExtLearnerUJ.services import GradingService
        GradingService().autoGradeDiagnostic(test.id, {str(q.id): '4'}, student.email)
        stats = UserStats.objects.get(userId=student.email)
        self.assertEqual(stats.diagnosticsCompleted, 1)
        self.assertGreater(stats.points, 0)
