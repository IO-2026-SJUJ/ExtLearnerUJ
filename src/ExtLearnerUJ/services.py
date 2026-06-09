"""
Warstwa Service Layer (zgodnie z opis.md).

Sprint 1: GradingService.autoGradeDiagnostic (wzorzec Strategy).
Sprint 3: pełna implementacja RecommendationService (FR-05),
StatisticsService (statystyki + zarobki), RankingService (FR-07) oraz
ReportGenerator (UC15 — raport PDF, bez zewnętrznych zależności).
"""
from __future__ import annotations


# Stawka rozliczeniowa moderatora: udział w cenie pakietu za sprawdzoną pracę
# Zarobki sprawdzających: obecna wersja nie pobiera żadnej marży —
# 100% ceny pakietu jest liczone jako zarobek sprawdzającego.
MODERATOR_SHARE = 1.0


class GradingService:
    """Wzorzec Strategy: różne typy testów → różne algorytmy oceniania."""

    def autoGradeDiagnostic(self, testId: str, answers: dict, userId: str):
        """Ocenia test diagnostyczny: wynik ogólny + wyniki per obszar.
        Tworzy DiagnosticResult i przyznaje punkty rankingowe (FR-07)."""
        from .models import DiagnosticTest, DiagnosticResult, UserStats

        try:
            test = DiagnosticTest.objects.get(pk=testId)
        except DiagnosticTest.DoesNotExist:
            return None

        overall = test.calculateScore(answers)
        areas = test.calculateAreaScores(answers)

        result = DiagnosticResult.objects.create(
            testId=str(testId),
            userId=str(userId),
            score=overall,
            answers=answers,
            areaScores=areas,
        )
        # Gamifikacja: stała pula punktów za ukończenie diagnostyki.
        UserStats.record_diagnostic(userId)
        return result

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


class RecommendationService:
    """FR-05: rekomenduje materiały z obszarów, w których student wypadł
    najsłabiej (< progu) w ostatnim teście diagnostycznym.

    Mapowanie obszar testu → kategoria materiału jest 1:1 (grammar, reading,
    listening, vocabulary) — patrz seed_diagnostic / seed_materials.
    """

    WEAK_THRESHOLD = 50.0  # FR-05: obszary z wynikiem < 50%

    def getRecommendationsForUser(self, userId, limit_per_area: int = 3):
        from .models import DiagnosticResult, Material

        last = (
            DiagnosticResult.objects
            .filter(userId=str(userId))
            .order_by('-completedAt')
            .first()
        )
        if last is None:
            return []

        weak_areas = last.getWeakAreas(self.WEAK_THRESHOLD)
        if not weak_areas:
            return []

        recommendations = []
        for area in weak_areas:
            materials = list(
                Material.objects.filter(
                    category=area, isVerified=True,
                ).order_by('-priority', '-id')[:limit_per_area]
            )
            score = last.areaScores.get(area, 0.0)
            recommendations.append({
                'area': area,
                'score': score,
                'materials': materials,
            })
        return recommendations


class StatisticsService:
    def updateUserStats(self, testResult):
        pass

    def getUserStatistics(self, userId):
        """Zagregowane statystyki nauki studenta (do strony statystyk i raportu PDF)."""
        from .models import (
            DiagnosticResult, ExamAttempt, Material, UserStats, Work,
        )
        userId = str(userId)
        stats = UserStats.for_user(userId)

        diagnostics = list(
            DiagnosticResult.objects.filter(userId=userId).order_by('-completedAt')
        )
        exams = list(
            ExamAttempt.objects.filter(
                userId=userId, status=ExamAttempt.STATUS_SUBMITTED,
            ).order_by('-submittedAt')
        )
        materials_added = Material.objects.filter(authorId=userId).count()
        works_submitted = Work.objects.filter(studentId=userId).count()

        last_diag = diagnostics[0] if diagnostics else None
        avg_exam = (
            round(sum(e.score for e in exams) / len(exams), 1) if exams else 0.0
        )

        return {
            'points': stats.points,
            'exams_completed': len(exams),
            'diagnostics_completed': len(diagnostics),
            'best_exam_score': stats.bestExamScore,
            'avg_exam_score': avg_exam,
            'materials_added': materials_added,
            'works_submitted': works_submitted,
            'last_diagnostic': last_diag,
            'last_area_scores': last_diag.areaScores if last_diag else {},
            'exams': exams,
            'diagnostics': diagnostics,
        }

    def getModeratorStats(self, moderatorId):
        """FR-14: zarobki moderatora + saldo do wypłaty."""
        from .models import WorkReview, Work, Package, Payout
        moderatorId = str(moderatorId)

        reviews = WorkReview.objects.filter(
            moderatorId=moderatorId, status=WorkReview.STATUS_PUBLISHED,
        )
        reviewed_count = reviews.count()

        gross = 0.0
        for review in reviews:
            work = Work.objects.filter(pk=review.workId).first()
            if not work:
                continue
            package = Package.objects.filter(pk=work.packageId).first()
            if package:
                gross += package.price * MODERATOR_SHARE

        gross = round(gross, 2)
        paid = sum(
            p.amount for p in Payout.objects.filter(moderatorId=moderatorId)
        )
        available = round(gross - paid, 2)

        return {
            'reviewed_count': reviewed_count,
            'total_earned': gross,
            'paid_out': round(paid, 2),
            'available': max(0.0, available),
            'payouts': list(Payout.objects.filter(moderatorId=moderatorId)),
        }

    def getSystemStats(self):
        return {}

    def generateLearningReport(self, userId, period):
        return ReportGenerator().buildPdf(userId, period)


class RankingService:
    """FR-07: ranking studentów po punktach."""

    def getStudentRanking(self, top_n: int = 10):
        from .models import UserStats, User

        ranking = []
        rows = UserStats.objects.filter(points__gt=0).order_by('-points')[:top_n]
        for pos, row in enumerate(rows, start=1):
            user = User.objects.filter(email=row.userId).first()
            ranking.append({
                'position': pos,
                'name': user.name if user else row.userId,
                'email': row.userId,
                'points': row.points,
                'exams': row.examsCompleted,
            })
        return ranking

    def getUserPosition(self, userId):
        from .models import UserStats
        userId = str(userId)
        stats = UserStats.objects.filter(userId=userId).first()
        if not stats or stats.points <= 0:
            return None
        better = UserStats.objects.filter(points__gt=stats.points).count()
        return better + 1


class ReportGenerator:
    """UC15: generuje raport PDF z okresu nauki studenta.

    Świadomie BEZ zewnętrznych zależności (reportlab itp.) — piszemy minimalny,
    poprawny plik PDF 1.4 z warstwą tekstową. Dzięki temu działa w CI i na
    darmowym hostingu bez dodatkowych pakietów. Zwraca `bytes`.
    """

    def buildPdf(self, userId, period='all') -> bytes:
        from .models import User
        data = StatisticsService().getUserStatistics(userId)
        user = User.objects.filter(email=str(userId)).first()
        name = user.name if user else str(userId)

        lines = [
            'ExtLearnerUJ — Raport postepow nauki',
            '',
            f'Uczen: {name}',
            f'E-mail: {userId}',
            f'Okres: {period}',
            '',
            'Podsumowanie:',
            f'  Punkty rankingowe:        {data["points"]}',
            f'  Ukonczone diagnostyki:    {data["diagnostics_completed"]}',
            f'  Ukonczone symulacje egz.: {data["exams_completed"]}',
            f'  Najlepszy wynik egzaminu: {data["best_exam_score"]}%',
            f'  Sredni wynik egzaminu:    {data["avg_exam_score"]}%',
            f'  Dodane materialy:         {data["materials_added"]}',
            f'  Wyslane prace pisemne:    {data["works_submitted"]}',
            '',
        ]

        if data['last_area_scores']:
            lines.append('Ostatnia diagnostyka — wyniki per obszar:')
            for area, score in sorted(data['last_area_scores'].items()):
                lines.append(f'  {area:<14} {score}%')
            lines.append('')

        if data['exams']:
            lines.append('Historia symulacji egzaminu:')
            for e in data['exams'][:10]:
                when = e.submittedAt.strftime('%Y-%m-%d %H:%M') if e.submittedAt else '-'
                lines.append(f'  {when}  wynik {e.score}%  (+{e.pointsAwarded} pkt)')
            lines.append('')

        lines.append('Wygenerowano automatycznie przez ExtLearnerUJ.')
        return self._render_pdf(lines)

    @staticmethod
    def _escape(text: str) -> str:
        return text.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')

    def _render_pdf(self, lines: list[str]) -> bytes:
        """Buduje minimalny, poprawny jednostronicowy PDF z listą linii tekstu."""
        # Strumien tresci strony: tekst monospaced, od gory.
        content_parts = ['BT', '/F1 11 Tf', '14 TL', '60 770 Td']
        for i, line in enumerate(lines):
            content_parts.append(f'({self._escape(line)}) Tj')
            content_parts.append('T*')
        content_parts.append('ET')
        content = '\n'.join(content_parts).encode('latin-1', 'replace')

        objects = []
        objects.append(b'<< /Type /Catalog /Pages 2 0 R >>')
        objects.append(b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>')
        objects.append(
            b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] '
            b'/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>'
        )
        objects.append(
            b'<< /Length ' + str(len(content)).encode() + b' >>\nstream\n'
            + content + b'\nendstream'
        )
        objects.append(
            b'<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>'
        )

        pdf = bytearray(b'%PDF-1.4\n')
        offsets = []
        for idx, obj in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf += f'{idx} 0 obj\n'.encode() + obj + b'\nendobj\n'

        xref_pos = len(pdf)
        pdf += f'xref\n0 {len(objects) + 1}\n'.encode()
        pdf += b'0000000000 65535 f \n'
        for off in offsets:
            pdf += f'{off:010d} 00000 n \n'.encode()
        pdf += (
            b'trailer\n<< /Size ' + str(len(objects) + 1).encode()
            + b' /Root 1 0 R >>\nstartxref\n'
            + str(xref_pos).encode() + b'\n%%EOF'
        )
        return bytes(pdf)


class PaymentGateway:
    """MOCK bramki płatności. W Sprincie 2/3 zawsze zwraca sukces."""

    def charge(self, amount: float) -> bool:
        if amount <= 0:
            return False
        return True
