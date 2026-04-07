from django.test import TestCase
from unittest.mock import patch, MagicMock

class TestServices(TestCase):

    @patch('ExtLearnerUJ.models.Material.objects.filter')
    def test_recommendationService_getRecommendationsForUser(self, mock_filter):
        from ExtLearnerUJ.services import RecommendationService
        service = RecommendationService()
        recs = service.getRecommendationsForUser("user_1")
        mock_filter.assert_called()

    @patch('ExtLearnerUJ.models.Statistics.save')
    def test_statisticsService_updateUserStats(self, mock_save):
        from ExtLearnerUJ.services import StatisticsService
        service = StatisticsService()
        service.updateUserStats(MagicMock())
        mock_save.assert_called()

    def test_statisticsService_getUserStatistics(self):
        from ExtLearnerUJ.services import StatisticsService
        service = StatisticsService()
        stats = service.getUserStatistics("user_1")
        self.assertIsInstance(stats, dict)

    def test_statisticsService_getModeratorStats(self):
        from ExtLearnerUJ.services import StatisticsService
        service = StatisticsService()
        stats = service.getModeratorStats("mod_1")
        self.assertIsInstance(stats, dict)

    def test_statisticsService_getSystemStats(self):
        from ExtLearnerUJ.services import StatisticsService
        service = StatisticsService()
        stats = service.getSystemStats()
        self.assertIsInstance(stats, dict)

    @patch('ExtLearnerUJ.services.ReportGenerator.buildPdf')
    def test_statisticsService_generateLearningReport(self, mock_build):
        from ExtLearnerUJ.services import StatisticsService
        service = StatisticsService()
        service.generateLearningReport("user_1", "2026")
        mock_build.assert_called_once()

    @patch('ExtLearnerUJ.models.Student.objects.order_by')
    def test_rankingService_getStudentRanking(self, mock_order):
        from ExtLearnerUJ.services import RankingService
        service = RankingService()
        service.getStudentRanking()
        mock_order.assert_called()

    @patch('builtins.open')
    def test_reportGenerator_buildPdf(self, mock_open):
        from ExtLearnerUJ.services import ReportGenerator
        gen = ReportGenerator()
        file = gen.buildPdf("user_1", "2026")
        self.assertIsNotNone(file)
