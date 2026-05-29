"""
Warstwa Service Layer (zgodnie z opis.md).

Sprint 1: pełna implementacja GradingService.autoGradeDiagnostic
(wzorzec Strategy). Pozostałe serwisy to stuby pod Sprint 2/3.
"""
from __future__ import annotations


class GradingService:
    """Wzorzec Strategy: różne typy testów → różne algorytmy oceniania."""

    def autoGradeDiagnostic(self, testId: str, answers: dict, userId: str):
        """Ocenia test diagnostyczny: wynik ogólny + wyniki per obszar.
        Tworzy i zwraca DiagnosticResult."""
        from .models import DiagnosticTest, DiagnosticResult

        try:
            test = DiagnosticTest.objects.get(pk=testId)
        except DiagnosticTest.DoesNotExist:
            return None

        overall = test.calculateScore(answers)
        areas = test.calculateAreaScores(answers)

        return DiagnosticResult.objects.create(
            testId=str(testId),
            userId=str(userId),
            score=overall,
            answers=answers,
            areaScores=areas,
        )

    def autoGradeMaterialTest(self, testId: str, answers: dict, userId: str):
        """Sprint 2."""
        from .models import Test, TestResult
        try:
            test = Test.objects.get(pk=testId)
        except Test.DoesNotExist:
            return None
        score = test.calculateScore(answers)
        return TestResult.objects.create(
            testId=str(testId), userId=str(userId), score=score, answers=answers,
        )


# Stuby — Sprint 2/3
class RecommendationService:
    def getRecommendationsForUser(self, userId):
        return []


class StatisticsService:
    def updateUserStats(self, testResult): pass
    def getUserStatistics(self, userId): return {}
    def getModeratorStats(self, moderatorId): return {}
    def getSystemStats(self): return {}
    def generateLearningReport(self, userId, period): return None


class RankingService:
    def getStudentRanking(self): return []


class ReportGenerator:
    def buildPdf(self, userId, period): return None


class PaymentGateway:
<<<<<<< HEAD
    def charge(self, amount): return False
=======
    """MOCK bramki płatności.
    W Sprincie 2 zawsze zwraca sukces — symulujemy prawdziwą integrację.
    W Sprincie 3 / produkcji: integracja z Przelewy24 / Stripe."""

    def charge(self, amount: float) -> bool:
        if amount <= 0:
            return False
        # W prawdziwej bramce byłby tu request do API dostawcy płatności.
        # Dla celów demo: zawsze sukces.
        return True
>>>>>>> sprint-2
