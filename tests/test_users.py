from django.test import TestCase
from django.core import mail
from unittest.mock import patch, MagicMock
from ExtLearnerUJ.models import User, Student, Moderator, Admin
import re

class TestUserModel(TestCase):
    def setUp(self):
        self.user = User(id=1, email="test@example.com", name="Test User", status="ACTIVE")

    def test_register(self):
        result = self.user.register("new@example.com", "password123", "New User")
        self.assertTrue(result)

    def test_verifyEmail(self):
        self.user.register("student@uj.edu.pl", "password123", "New User")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["student@uj.edu.pl"])
        token = re.search(r'\d{6}', mail.outbox[0].body).group()
        self.assertTrue(User.objects.get(email="student@uj.edu.pl").verifyEmail(token))

    @patch('ExtLearnerUJ.models.Session.create')
    def test_login(self, mock_session_create):
        mock_session_create.return_value = MagicMock(token="token123")
        session = self.user.login("test@example.com", "password123")
        self.assertIsNotNone(session)
        mock_session_create.assert_called_once_with(self.user.id)

    @patch('ExtLearnerUJ.models.Session.invalidate')
    def test_logout(self, mock_invalidate):
        self.user.logout()
        mock_invalidate.assert_called()

    @patch('ExtLearnerUJ.models.User.delete')
    def test_deleteAccount(self, mock_delete):
        result = self.user.deleteAccount()
        self.assertTrue(result)
        mock_delete.assert_called_once()

    @patch('ExtLearnerUJ.models.Report.submit')
    def test_submitReport(self, mock_submit):
        report = self.user.submitReport("MATERIAL", "m_1", "Inappropriate content")
        self.assertIsNotNone(report)
        mock_submit.assert_called_once()

class TestStudentModel(TestCase):
    def setUp(self):
        self.student = Student(id=2, email="student@example.com")

    @patch('ExtLearnerUJ.services.GradingService.autoGradeDiagnostic')
    def test_takeDiagnosticTest(self, mock_grade):
        mock_grade.return_value = MagicMock(id="res_1")
        result = self.student.takeDiagnosticTest()
        self.assertIsNotNone(result)

    @patch('ExtLearnerUJ.services.RecommendationService.getRecommendationsForUser')
    def test_viewRecommendations(self, mock_recommend):
        mock_recommend.return_value = [MagicMock(id="mat_1")]
        recommendations = self.student.viewRecommendations()
        self.assertEqual(len(recommendations), 1)

    @patch('ExtLearnerUJ.models.Material.objects.filter')
    def test_browseMaterials(self, mock_filter):
        mock_filter.return_value = [MagicMock(id="m_1"), MagicMock(id="m_2")]
        materials = self.student.browseMaterials({"category": "Grammar"})
        self.assertEqual(len(materials), 2)

    @patch('ExtLearnerUJ.models.Material.getDetails')
    def test_viewMaterial(self, mock_details):
        material = self.student.viewMaterial("m_1")
        mock_details.assert_called_once()

    @patch('ExtLearnerUJ.models.Favorite.objects.create')
    def test_addToFavorites(self, mock_create):
        mock_create.return_value = MagicMock(materialId="m_1")
        favorite = self.student.addToFavorites("m_1")
        self.assertIsNotNone(favorite)

    @patch('ExtLearnerUJ.models.Vote.objects.create')
    @patch('ExtLearnerUJ.models.Material.increasePriority')
    def test_voteMaterial(self, mock_increase, mock_create):
        vote = self.student.voteMaterial("m_1")
        self.assertIsNotNone(vote)
        mock_increase.assert_called_once()

    @patch('ExtLearnerUJ.models.Work.submit')
    def test_submitWork(self, mock_submit):
        mock_submit.return_value = MagicMock(id="work_1")
        work = self.student.submitWork({"text": "data"}, "pkg_1", ["file1.pdf"])
        self.assertIsNotNone(work)

    @patch('ExtLearnerUJ.services.StatisticsService.getUserStatistics')
    def test_viewStats(self, mock_stats):
        self.student.viewStats()
        mock_stats.assert_called_once_with(self.student.id)

    @patch('ExtLearnerUJ.services.StatisticsService.generateLearningReport')
    def test_downloadLearningReport(self, mock_report):
        mock_report.return_value = MagicMock(fileName="report.pdf")
        file = self.student.downloadLearningReport()
        self.assertEqual(file.fileName, "report.pdf")

    @patch('ExtLearnerUJ.models.ModeratorApplication.submit')
    def test_applyForModerator(self, mock_submit):
        mock_submit.return_value = MagicMock(id="app_1")
        app = self.student.applyForModerator()
        self.assertIsNotNone(app)

    @patch('ExtLearnerUJ.models.WorkReview.objects.get')
    def test_rateModerator(self, mock_get_review):
        self.student.rateModerator("work_1", 5, "Great feedback")
        mock_get_review.assert_called_once_with(id="work_1")

class TestModeratorModel(TestCase):
    def setUp(self):
        self.moderator = Moderator(id=3, email="mod@example.com")

    @patch('ExtLearnerUJ.models.Material.objects.filter')
    def test_viewMaterialsToVerify(self, mock_filter):
        self.moderator.viewMaterialsToVerify()
        mock_filter.assert_called()

    @patch('ExtLearnerUJ.models.MaterialVerification.submit')
    def test_verifyMaterial(self, mock_submit):
        mock_submit.return_value = MagicMock(decision="ACCEPTED")
        verification = self.moderator.verifyMaterial("m_1", "ACCEPTED", "Looks good")
        self.assertIsNotNone(verification)

    @patch('ExtLearnerUJ.models.Test.objects.get')
    def test_editMaterialTests(self, mock_get):
        result = self.moderator.editMaterialTests("m_1", [{"q": "new question?"}])
        self.assertTrue(result)

    @patch('ExtLearnerUJ.models.Work.objects.filter')
    def test_viewWorksToCheck(self, mock_filter):
        self.moderator.viewWorksToCheck()
        mock_filter.assert_called()

    @patch('ExtLearnerUJ.models.Work.assignModerator')
    def test_reserveWork(self, mock_assign):
        mock_assign.return_value = True
        result = self.moderator.reserveWork("work_1")
        self.assertTrue(result)

    @patch('ExtLearnerUJ.models.WorkReview.publish')
    def test_checkWork(self, mock_publish):
        review = self.moderator.checkWork("work_1", {"grade": "A"})
        self.assertIsNotNone(review)

    @patch('ExtLearnerUJ.services.StatisticsService.getModeratorStats')
    def test_viewModeratorStats(self, mock_stats):
        self.moderator.viewModeratorStats()
        mock_stats.assert_called_once_with(self.moderator.id)

class TestAdminModel(TestCase):
    def setUp(self):
        self.admin = Admin(id=4)

    @patch('ExtLearnerUJ.services.StatisticsService.getSystemStats')
    def test_viewSystemStats(self, mock_stats):
        self.admin.viewSystemStats()
        mock_stats.assert_called_once()

    @patch('ExtLearnerUJ.models.ModeratorApplication.objects.filter')
    def test_reviewModeratorApplications(self, mock_filter):
        self.admin.reviewModeratorApplications()
        mock_filter.assert_called()

    @patch('ExtLearnerUJ.models.ModeratorApplication.evaluate')
    def test_acceptCandidate(self, mock_eval):
        mock_eval.return_value = True
        result = self.admin.acceptCandidate("app_1")
        self.assertTrue(result)

    @patch('ExtLearnerUJ.models.ModeratorApplication.evaluate')
    def test_rejectCandidate(self, mock_eval):
        mock_eval.return_value = True
        result = self.admin.rejectCandidate("app_1", "Lacks experience")
        self.assertTrue(result)

    @patch('ExtLearnerUJ.models.Report.objects.filter')
    def test_handleUserReports(self, mock_filter):
        self.admin.handleUserReports()
        mock_filter.assert_called()

    @patch('ExtLearnerUJ.models.Report.review')
    def test_reviewReport(self, mock_review):
        mock_review.return_value = True
        result = self.admin.reviewReport("rep_1", "BANNED")
        self.assertTrue(result)

    @patch('ExtLearnerUJ.models.User.objects.get')
    def test_manageUserAccount(self, mock_get):
        mock_user = MagicMock()
        mock_get.return_value = mock_user
        self.admin.manageUserAccount("user_1", "BLOCKED", "USER")
        self.assertEqual(mock_user.status, "BLOCKED")
