"""
Testy Sprintu 1 — test diagnostyczny.

Pokrywa: Test.calculateScore, DiagnosticTest.calculateAreaScores,
DiagnosticResult.getWeakAreas, GradingService.autoGradeDiagnostic,
widoki diagnostic_start/test/result/autosave.
"""
import json

from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse

from ExtLearnerUJ.models import (
    User, Student, Session, EmailVerificationToken,
    DiagnosticTest, Question, DiagnosticResult,
)
from ExtLearnerUJ.services import GradingService


# ============================================================
# Helpery
# ============================================================
def _make_verified_student(email='diag@uj.edu.pl', password='SilneHaslo123'):
    user = User.register(email, password, 'Diag Student')
    token = EmailVerificationToken.objects.get(userId=email).token
    user.verifyEmail(token)
    return user


def _make_test_with_questions():
    test = DiagnosticTest.objects.create(title='Test', type='DIAGNOSTIC')
    q1 = Question.objects.create(
        test=test, text='Q1', correctAnswer='A', area='grammar',
        options=['A', 'B', 'C', 'D'],
    )
    q2 = Question.objects.create(
        test=test, text='Q2', correctAnswer='B', area='grammar',
        options=['A', 'B', 'C', 'D'],
    )
    q3 = Question.objects.create(
        test=test, text='Q3', correctAnswer='C', area='reading',
        options=['A', 'B', 'C', 'D'],
    )
    q4 = Question.objects.create(
        test=test, text='Q4', correctAnswer='D', area='reading',
        options=['A', 'B', 'C', 'D'],
    )
    return test, [q1, q2, q3, q4]


# ============================================================
# Test (model) + DiagnosticTest
# ============================================================
class TestModelScoringTests(TestCase):
    def setUp(self):
        self.test, self.qs = _make_test_with_questions()

    def test_all_correct_gives_100(self):
        answers = {str(self.qs[0].id): 'A', str(self.qs[1].id): 'B',
                   str(self.qs[2].id): 'C', str(self.qs[3].id): 'D'}
        self.assertEqual(self.test.calculateScore(answers), 100.0)

    def test_half_correct_gives_50(self):
        answers = {str(self.qs[0].id): 'A', str(self.qs[1].id): 'B',
                   str(self.qs[2].id): 'X', str(self.qs[3].id): 'X'}
        self.assertEqual(self.test.calculateScore(answers), 50.0)

    def test_none_correct_gives_0(self):
        answers = {str(q.id): 'X' for q in self.qs}
        self.assertEqual(self.test.calculateScore(answers), 0.0)

    def test_empty_answers_gives_0(self):
        self.assertEqual(self.test.calculateScore({}), 0.0)

    def test_test_with_no_questions_gives_0(self):
        empty = DiagnosticTest.objects.create(title='Empty', type='DIAGNOSTIC')
        self.assertEqual(empty.calculateScore({}), 0.0)


class DiagnosticTestAreaScoresTests(TestCase):
    def setUp(self):
        self.test, self.qs = _make_test_with_questions()

    def test_area_scores_split_correctly(self):
        # Grammar: 1/2, Reading: 2/2
        answers = {
            str(self.qs[0].id): 'A',   # grammar: OK
            str(self.qs[1].id): 'X',   # grammar: ŹLE
            str(self.qs[2].id): 'C',   # reading: OK
            str(self.qs[3].id): 'D',   # reading: OK
        }
        scores = self.test.calculateAreaScores(answers)
        self.assertEqual(scores['grammar'], 50.0)
        self.assertEqual(scores['reading'], 100.0)

    def test_missing_answers_counted_as_wrong(self):
        scores = self.test.calculateAreaScores({})
        self.assertEqual(scores['grammar'], 0.0)
        self.assertEqual(scores['reading'], 0.0)

    def test_areas_without_questions_not_in_result(self):
        scores = self.test.calculateAreaScores({})
        self.assertNotIn('listening', scores)


class DiagnosticResultWeakAreasTests(TestCase):
    def test_weak_areas_below_50(self):
        result = DiagnosticResult(
            testId='1', userId='x@uj.edu.pl', score=50.0,
            areaScores={'grammar': 30.0, 'reading': 85.0, 'listening': 49.9, 'vocabulary': 50.0},
        )
        weak = result.getWeakAreas()
        self.assertIn('grammar', weak)
        self.assertIn('listening', weak)
        self.assertNotIn('reading', weak)
        self.assertNotIn('vocabulary', weak)  # 50.0 to próg, nie "poniżej"

    def test_weak_areas_custom_threshold(self):
        result = DiagnosticResult(
            testId='1', userId='x@uj.edu.pl', score=70.0,
            areaScores={'grammar': 65.0, 'reading': 75.0},
        )
        weak = result.getWeakAreas(threshold=70.0)
        self.assertEqual(weak, ['grammar'])

    def test_empty_area_scores(self):
        result = DiagnosticResult(
            testId='1', userId='x@uj.edu.pl', score=0.0, areaScores={},
        )
        self.assertEqual(result.getWeakAreas(), [])


# ============================================================
# GradingService — wzorzec Strategy
# ============================================================
class GradingServiceTests(TestCase):
    def setUp(self):
        self.test, self.qs = _make_test_with_questions()
        self.service = GradingService()

    def test_auto_grade_diagnostic_creates_result(self):
        answers = {str(q.id): q.correctAnswer for q in self.qs}
        result = self.service.autoGradeDiagnostic(
            testId=self.test.id, answers=answers, userId='x@uj.edu.pl',
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, DiagnosticResult)
        self.assertEqual(result.score, 100.0)
        self.assertEqual(result.userId, 'x@uj.edu.pl')

    def test_auto_grade_diagnostic_saves_area_scores(self):
        answers = {
            str(self.qs[0].id): 'A',   # grammar OK
            str(self.qs[1].id): 'B',   # grammar OK
            str(self.qs[2].id): 'X',   # reading źle
            str(self.qs[3].id): 'X',   # reading źle
        }
        result = self.service.autoGradeDiagnostic(
            testId=self.test.id, answers=answers, userId='x@uj.edu.pl',
        )
        self.assertEqual(result.areaScores['grammar'], 100.0)
        self.assertEqual(result.areaScores['reading'], 0.0)

    def test_auto_grade_diagnostic_persists_to_db(self):
        self.service.autoGradeDiagnostic(
            testId=self.test.id, answers={}, userId='x@uj.edu.pl',
        )
        self.assertEqual(
            DiagnosticResult.objects.filter(userId='x@uj.edu.pl').count(), 1,
        )

    def test_auto_grade_diagnostic_nonexistent_test_returns_none(self):
        result = self.service.autoGradeDiagnostic(
            testId=99999, answers={}, userId='x@uj.edu.pl',
        )
        self.assertIsNone(result)


# ============================================================
# Widoki testu diagnostycznego (flow E2E)
# ============================================================
class DiagnosticViewsTests(TestCase):
    def setUp(self):
        self.user = _make_verified_student()
        self.session = User.authenticate('diag@uj.edu.pl', 'SilneHaslo123')
        self.client = Client()
        self.client.cookies[settings.SESSION_COOKIE_NAME_APP] = self.session.token

        self.test, self.qs = _make_test_with_questions()

    def test_start_requires_login(self):
        anon = Client()
        response = anon.get(reverse('diagnostic_start'))
        self.assertEqual(response.status_code, 302)

    def test_start_page_accessible_when_logged_in(self):
        response = self.client.get(reverse('diagnostic_start'))
        self.assertEqual(response.status_code, 200)

    def test_test_page_shows_questions(self):
        response = self.client.get(reverse('diagnostic_test', args=[self.test.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Q1')
        self.assertContains(response, 'Q4')

    def test_submit_creates_result_and_redirects(self):
        post_data = {f'q_{q.id}': q.correctAnswer for q in self.qs}
        response = self.client.post(
            reverse('diagnostic_test', args=[self.test.id]), post_data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            DiagnosticResult.objects.filter(userId='diag@uj.edu.pl').exists()
        )

    def test_result_page_shows_score(self):
        result = GradingService().autoGradeDiagnostic(
            testId=self.test.id,
            answers={str(q.id): q.correctAnswer for q in self.qs},
            userId='diag@uj.edu.pl',
        )
        response = self.client.get(reverse('diagnostic_result', args=[result.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '100')

    def test_result_not_accessible_by_other_user(self):
        """Inny user nie powinien móc obejrzeć cudzego wyniku."""
        result = GradingService().autoGradeDiagnostic(
            testId=self.test.id, answers={}, userId='someone_else@uj.edu.pl',
        )
        response = self.client.get(reverse('diagnostic_result', args=[result.id]))
        self.assertEqual(response.status_code, 404)


class AutosaveTests(TestCase):
    def setUp(self):
        self.user = _make_verified_student()
        self.session = User.authenticate('diag@uj.edu.pl', 'SilneHaslo123')
        self.client = Client()
        self.client.cookies[settings.SESSION_COOKIE_NAME_APP] = self.session.token
        self.test, self.qs = _make_test_with_questions()

    def test_autosave_stores_answers_in_session(self):
        payload = {'answers': {str(self.qs[0].id): 'A'}}
        response = self.client.post(
            reverse('diagnostic_autosave', args=[self.test.id]),
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['ok'])
        self.assertEqual(body['saved_answers'], 1)

    def test_autosave_rejects_malformed_payload(self):
        response = self.client.post(
            reverse('diagnostic_autosave', args=[self.test.id]),
            data='not-json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_autosave_requires_login(self):
        anon = Client()
        response = anon.post(
            reverse('diagnostic_autosave', args=[self.test.id]),
            data=json.dumps({'answers': {}}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)
