"""
Modele domenowe ExtLearnerUJ.

Hierarchia (LSP z opis.md):
    User → Student | Moderator | Admin    (multi-table inheritance)

Sprint 1 implementuje: User, Session, EmailVerificationToken, Student,
Material, FileAttachment, Test/DiagnosticTest, Question, TestResult/DiagnosticResult.
Pozostałe encje są zdefiniowane jako szkielety pod Sprint 2.
"""
from __future__ import annotations

import os
import uuid
import random
from datetime import timedelta

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.utils import timezone
# ============================================================
# Helpery — callable defaulty (fix bugu z poprzedniej wersji)
# ============================================================
def _default_email_token() -> str:
    """6-cyfrowy token weryfikacyjny. Musi być callable — inaczej
    Django ewaluuje wartość raz przy starcie i wszyscy dostają ten sam token."""
    return str(random.randint(100000, 999999))


def _default_email_token_expiry():
    return timezone.now() + timedelta(days=1)


def _default_session_expiry():
    return timezone.now() + timedelta(hours=settings.SESSION_LIFETIME_HOURS)


# ============================================================
# User + role (hierarchia LSP)
# ============================================================
class User(models.Model):
    """Bazowy użytkownik. Wszystkie role (Student/Moderator/Admin)
    dziedziczą przez multi-table inheritance."""

    STATUS_ACTIVE = 'ACTIVE'
    STATUS_BLOCKED = 'BLOCKED'
    STATUS_DELETED = 'DELETED'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Aktywne'),
        (STATUS_BLOCKED, 'Zablokowane'),
        (STATUS_DELETED, 'Usunięte'),
    ]

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    emailVerified = models.BooleanField(default=False)
    registrationDate = models.DateTimeField(auto_now_add=True)
    # Termin końca blokady czasowej (None = brak blokady / blokada bezterminowa).
    blockedUntil = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['email'])]

    def __str__(self) -> str:
        return f'{self.name} <{self.email}>'

    # -------------------------
    # Rejestracja / weryfikacja
    # -------------------------
    @classmethod
    def register(cls, email: str, password: str, name: str) -> 'User | None':
        """Tworzy konto studenta (domyślna rola) + wysyła token weryfikacyjny.
        Zwraca nowego usera lub None gdy email jest już zajęty."""
        if cls.objects.filter(email=email).exists():
            return None

        # Domyślna rola przy rejestracji to Student (kandydat na moderatora
        # rejestruje się osobnym flowem w Sprincie 2 — FR-02).
        student = Student.objects.create(
            email=email,
            password=make_password(password),
            name=name,
            status=cls.STATUS_ACTIVE,
            emailVerified=False,
        )
        token = EmailVerificationToken.objects.create(userId=student.email)
        student._send_verification_email(token.token)
        return student

    def _send_verification_email(self, token_code: str) -> None:
        subject = 'ExtLearnerUJ — kod weryfikacyjny'
        message = (
            f'Witaj {self.name}!\n\n'
            f'Twój kod weryfikacyjny: {token_code}\n\n'
            f'Kod jest ważny przez 24 godziny.\n\n'
            f'Jeśli nie zakładałeś/aś konta, zignoruj tę wiadomość.'
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.email])

    def verifyEmail(self, token_code: str) -> bool:
        """Weryfikuje token i aktywuje konto. UC02."""
        try:
            token = EmailVerificationToken.objects.get(
                userId=self.email, token=token_code
            )
        except EmailVerificationToken.DoesNotExist:
            return False

        if not token.verify():
            token.delete()
            return False

        self.emailVerified = True
        self.save(update_fields=['emailVerified'])
        token.delete()
        return True

    def sendVerificationCode(self) -> bool:
        """Generuje świeży kod weryfikacyjny i wysyła go mailem (ponowne
        wysłanie). Stare tokeny tej osoby usuwamy. Zwraca False, gdy konto
        jest już zweryfikowane."""
        if self.emailVerified:
            return False
        EmailVerificationToken.objects.filter(userId=self.email).delete()
        token = EmailVerificationToken.objects.create(userId=self.email)
        self._send_verification_email(token.token)
        return True

    # -------------------------
    # Logowanie / sesje
    # -------------------------
    @classmethod
    def authenticate(cls, email: str, password: str) -> 'Session | None':
        """Sprawdza dane logowania i tworzy sesję. UC03.
        E-mail traktujemy bez rozróżniania wielkości liter."""
        try:
            user = cls.objects.get(email__iexact=(email or '').strip())
        except cls.DoesNotExist:
            return None
        except cls.MultipleObjectsReturned:
            user = cls.objects.filter(email__iexact=(email or '').strip()).first()
        # Auto-odblokowanie: jeśli blokada czasowa już wygasła — reaktywuj.
        if user.status == cls.STATUS_BLOCKED and user.is_block_expired():
            user.status = cls.STATUS_ACTIVE
            user.blockedUntil = None
            user.save(update_fields=['status', 'blockedUntil'])
        if user.status != cls.STATUS_ACTIVE:
            return None
        if not user.emailVerified:
            return None
        if not check_password(password, user.password):
            return None
        return Session.create(user.email)

    def is_block_expired(self) -> bool:
        """True, gdy blokada była czasowa i już minęła."""
        return self.blockedUntil is not None and timezone.now() >= self.blockedUntil

    def logout(self) -> None:
        Session.objects.filter(userId=self.email).delete()

    # -------------------------
    # Usuwanie konta (RODO — O-01)
    # -------------------------
    def deleteAccount(self) -> bool:
        """RODO (O-01) — trwałe usunięcie konta wraz ze WSZYSTKIMI danymi
        osobowymi użytkownika. Operacja nieodwracalna, w jednej transakcji."""
        from django.db import transaction
        email = self.email
        try:
            with transaction.atomic():
                # --- Moje prace pisemne (wraz z recenzjami, błędami,
                #     płatnościami i załącznikami) ---
                my_work_ids = [str(w.id) for w in Work.objects.filter(studentId=email)]
                if my_work_ids:
                    rev_ids = [str(r.id) for r in WorkReview.objects.filter(workId__in=my_work_ids)]
                    if rev_ids:
                        ErrorMark.objects.filter(reviewId__in=rev_ids).delete()
                    WorkReview.objects.filter(workId__in=my_work_ids).delete()
                    PaymentTransaction.objects.filter(workId__in=my_work_ids).delete()
                    Work.objects.filter(studentId=email).delete()  # FK → załączniki

                # --- Prace, które oceniałem(-am) jako moderator: zdejmuję
                #     swoje autorstwo i zwracam je do kolejki ---
                my_reviews = WorkReview.objects.filter(moderatorId=email)
                reviewed_work_ids = [r.workId for r in my_reviews]
                rev_ids = [str(r.id) for r in my_reviews]
                if rev_ids:
                    ErrorMark.objects.filter(reviewId__in=rev_ids).delete()
                my_reviews.delete()
                if reviewed_work_ids:
                    Work.objects.filter(id__in=reviewed_work_ids).update(
                        assignedModeratorId=None, status=Work.STATUS_PAID,
                    )

                # --- Materiały, których jestem autorem (+ ich głosy,
                #     weryfikacje, komentarze, załączniki) ---
                my_material_ids = [str(m.id) for m in Material.objects.filter(authorId=email)]
                if my_material_ids:
                    Vote.objects.filter(materialId__in=my_material_ids).delete()
                    Favorite.objects.filter(materialId__in=my_material_ids).delete()
                    MaterialVerification.objects.filter(materialId__in=my_material_ids).delete()
                    Comment.objects.filter(targetId__in=my_material_ids).delete()
                    Material.objects.filter(authorId=email).delete()  # FK → załączniki

                # --- Moja aktywność i ślady osobowe ---
                MaterialVerification.objects.filter(moderatorId=email).delete()
                Vote.objects.filter(userId=email).delete()
                Favorite.objects.filter(userId=email).delete()
                Comment.objects.filter(authorId=email).delete()
                Notification.objects.filter(userId=email).delete()
                TestResult.objects.filter(userId=email).delete()  # + DiagnosticResult (MTI)
                ExamAttempt.objects.filter(userId=email).delete()
                UserStats.objects.filter(userId=email).delete()
                PaymentTransaction.objects.filter(userId=email).delete()
                Payout.objects.filter(moderatorId=email).delete()
                Report.objects.filter(reporterId=email).delete()
                Report.objects.filter(targetType=Report.TARGET_USER, targetId=email).delete()
                ModeratorApplication.objects.filter(candidateId=email).delete()
                PasswordResetToken.objects.filter(userId=email).delete()
                EmailVerificationToken.objects.filter(userId=email).delete()
                Session.objects.filter(userId=email).delete()

                # --- Na końcu samo konto (MTI: usunięcie roli usuwa też User) ---
                self.delete()
            return True
        except Exception:
            return False

    # -------------------------
    # Zgłoszenia (Sprint 2)
    # -------------------------
    def submitReport(self, targetType: str, targetId: str, reason: str):
        """Składa zgłoszenie o nadużyciu (FR-13, UC25).
        targetType: 'MATERIAL'|'USER'|'COMMENT'"""
        report = Report.objects.create(
            reporterId=self.email,
            targetType=targetType,
            targetId=str(targetId),
            reason=reason,
            status='PENDING',
        )
        return report

    # -------------------------
    # Funkcje dostępne dla KAŻDEJ roli (Student/Moderator/Admin).
    # Moderator i admin też mogą się uczyć: diagnostyka, egzamin, materiały,
    # prace pisemne, statystyki. Dlatego metody są na klasie bazowej User.
    # -------------------------
    def takeDiagnosticTest(self):
        return DiagnosticTest.objects.first()

    def browseMaterials(self, filters: dict | None = None):
        qs = Material.objects.all()
        if filters:
            if 'status' in filters:
                qs = qs.filter(status=filters['status'])
            if 'verified' in filters:
                qs = qs.filter(isVerified=filters['verified'])
        return list(qs.order_by('-priority', '-id'))

    def viewMaterial(self, materialId):
        try:
            return Material.objects.get(pk=materialId)
        except Material.DoesNotExist:
            return None

    def viewRecommendations(self):
        """FR-05: rekomendacje materiałów na podstawie najsłabszych obszarów
        z ostatniego testu diagnostycznego."""
        from .services import RecommendationService
        return RecommendationService().getRecommendationsForUser(self.email)

    def addToFavorites(self, materialId):
        return None

    def voteMaterial(self, materialId):
        """Oddaje głos na materiał (FR-09). Idempotentne."""
        try:
            material = Material.objects.get(pk=materialId)
        except Material.DoesNotExist:
            return None
        vote, created = Vote.objects.get_or_create(
            userId=self.email, materialId=str(materialId),
        )
        if created:
            material.increasePriority()
        return vote

    def submitWork(self, workData: dict, packageId, files=None):
        """Przesyła pracę pisemną do sprawdzenia (FR-15, UC19)."""
        try:
            package = Package.objects.get(pk=packageId)
        except Package.DoesNotExist:
            return None
        work = Work.objects.create(
            title=workData.get('title', ''),
            description=workData.get('description', ''),
            studentId=self.email,
            packageId=str(package.id),
            status=Work.STATUS_PENDING_PAYMENT,
        )
        if files:
            for f in files:
                att = FileAttachment()
                if att.upload(f):
                    att.work = work
                    att.save()
        return work

    def viewStats(self):
        from .services import StatisticsService
        return StatisticsService().getUserStatistics(self.email)

    def downloadLearningReport(self):
        from .services import ReportGenerator
        return ReportGenerator().buildPdf(self.email, 'all')

    def deleteOwnMaterial(self, materialId) -> bool:
        """Autor może usunąć własny materiał."""
        try:
            material = Material.objects.get(pk=materialId, authorId=self.email)
        except Material.DoesNotExist:
            return False
        material.delete()
        return True

    def applyForModerator(self, motivation: str = '', certificatePath: str = '',
                          testScore=None):
        """Składa wniosek o rolę moderatora. Jeden aktywny (PENDING) wniosek
        na osobę. Kandydat wypełnia test kwalifikacyjny — wynik poniżej progu
        oznacza automatyczne odrzucenie (bez angażowania administratora);
        w przeciwnym razie wniosek trafia do kolejki admina wraz z wynikiem."""
        from .moderator_test import PASS_THRESHOLD
        existing = ModeratorApplication.objects.filter(
            candidateId=self.email, status='PENDING',
        ).first()
        if existing:
            return existing

        # Automatyczne odrzucenie przy zbyt niskim wyniku testu.
        if testScore is not None and testScore < PASS_THRESHOLD:
            application = ModeratorApplication.objects.create(
                candidateId=self.email,
                status=ModeratorApplication.STATUS_REJECTED,
                motivation=motivation,
                certificatePath=certificatePath,
                testScore=testScore,
                decisionComment=(
                    f'Odrzucono automatycznie: wynik testu kwalifikacyjnego '
                    f'{testScore}% jest poniżej progu {PASS_THRESHOLD:.0f}%.'
                ),
                reviewedAt=timezone.now(),
                reviewedBy='system',
            )
            Notification.objects.create(
                userId=self.email,
                message=(
                    f'Twój wniosek o rolę moderatora został odrzucony — wynik '
                    f'testu kwalifikacyjnego ({testScore}%) jest poniżej '
                    f'wymaganych {PASS_THRESHOLD:.0f}%. Możesz spróbować ponownie.'
                ),
                link='/moderator/apply/',
            )
            return application

        application = ModeratorApplication.objects.create(
            candidateId=self.email,
            status='PENDING',
            motivation=motivation,
            certificatePath=certificatePath,
            testScore=testScore,
        )
        Notification.objects.create(
            userId=self.email,
            message=(
                '✓ Twój wniosek o rolę moderatora został wysłany. '
                'Administrator rozpatrzy go wkrótce.'
            ),
            link='/moderator/apply/',
        )
        return application

    def rateModerator(self, workId, score, comment=''):
        """Ocena sprawdzającego (1-5 gwiazdek) po opublikowanej ocenie pracy.
        Jedna ocena na pracę — ponowne wystawienie nadpisuje poprzednią.
        Zwraca ModeratorRating albo None, gdy ocena niemożliwa."""
        try:
            score = int(score)
        except (TypeError, ValueError):
            return None
        if not 1 <= score <= 5:
            return None
        try:
            work = Work.objects.get(pk=workId, studentId=self.email)
        except Work.DoesNotExist:
            return None
        review = WorkReview.objects.filter(
            workId=str(work.id), status=WorkReview.STATUS_PUBLISHED,
        ).first()
        if review is None:
            return None  # można ocenić dopiero po otrzymaniu oceny pracy
        rating, _created = ModeratorRating.objects.update_or_create(
            workId=str(work.id),
            studentId=self.email,
            defaults={
                'moderatorId': review.moderatorId,
                'score': score,
                'comment': comment or '',
            },
        )
        return rating

    # -------------------------
    # Panel finansowy (FR-14) — dostępny dla moderatora i admina.
    # -------------------------
    def viewModeratorStats(self):
        """Statystyki + zarobki za sprawdzone prace."""
        from .services import StatisticsService
        return StatisticsService().getModeratorStats(self.email)

    def requestPayout(self):
        """Zleca wypłatę dostępnego salda; tworzy Payout z numerem faktury."""
        from .services import StatisticsService
        stats = StatisticsService().getModeratorStats(self.email)
        available = stats.get('available', 0.0)
        if available <= 0:
            return None
        return Payout.create_for(self.email, available)

    def reserveWork(self, workId):
        """Rezerwuje pracę do sprawdzenia (UC39). Idempotentne —
        jeśli moderator już ją miał, zwraca True. Po rezerwacji nikt inny
        nie może przejąć pracy, a zleceniodawca dostaje powiadomienie
        z kontaktem do sprawdzającego (rozliczenie indywidualne)."""
        try:
            work = Work.objects.get(pk=workId)
        except Work.DoesNotExist:
            return False

        # Czy ktoś inny nie zarezerwował wcześniej?
        if work.assignedModeratorId and work.assignedModeratorId != self.email:
            return False

        already_mine = work.assignedModeratorId == self.email
        work.assignedModeratorId = self.email
        work.status = Work.STATUS_IN_REVIEW
        work.save(update_fields=['assignedModeratorId', 'status'])

        if not already_mine:
            Notification.objects.create(
                userId=work.studentId,
                message=(
                    f'Twoja praca „{work.title}" została zarezerwowana do '
                    f'sprawdzenia przez: {self.name} ({self.email}).'
                ),
                details=(
                    f'Sprawdzający skontaktuje się z Tobą w sprawie ustalenia '
                    f'płatności (rozliczenie indywidualne). Możesz też napisać '
                    f'bezpośrednio na adres: {self.email}.'
                ),
                link=f'/works/{work.id}/',
            )
        return True



class Student(User):
    """Domyślna rola po rejestracji. Wszystkie metody „uczniowskie"
    (diagnostyka, egzamin, materiały, prace, statystyki) są na klasie bazowej
    User — dzięki temu mają je też Moderator i Admin."""
    pass


class Moderator(User):
    def viewMaterialsToVerify(self):
        """Zwraca listę materiałów do weryfikacji, posortowaną po priorytecie
        malejąco (najbardziej oczekiwane najpierw — UC36)."""
        return list(
            Material.objects.filter(status=Material.STATUS_PENDING)
            .order_by('-priority', 'createdAt')
        )

    def verifyMaterial(self, materialId, decision, comment=''):
        """Weryfikuje materiał. decision: 'ACCEPTED'|'REJECTED'|'NEEDS_REVISION'.
        Tworzy MaterialVerification, zmienia status materiału,
        wysyła Notification do autora (UC31 + UC32)."""
        try:
            material = Material.objects.get(pk=materialId)
        except Material.DoesNotExist:
            return None

        verification = MaterialVerification.objects.create(
            materialId=str(materialId),
            moderatorId=self.email,
            decision=decision,
        )

        if decision == 'ACCEPTED':
            material.status = Material.STATUS_VERIFIED
            material.isVerified = True
        elif decision == 'REJECTED':
            material.status = Material.STATUS_REJECTED
            material.isVerified = False
        # NEEDS_REVISION zostawia status=PENDING, tylko dodaje komentarz
        material.save(update_fields=['status', 'isVerified'])

        # Powiadomienie dla autora (UC32)
        msg_map = {
            'ACCEPTED': f'Twój materiał "{material.title}" został zaakceptowany ✓',
            'REJECTED': f'Twój materiał "{material.title}" został odrzucony',
            'NEEDS_REVISION': f'Twój materiał "{material.title}" wymaga poprawy',
        }
        notification = Notification.objects.create(
            userId=material.authorId,
            message=msg_map.get(decision, f'Status materiału "{material.title}" się zmienił'),
            details=(f'Komentarz moderatora: {comment}' if comment else ''),
        )
        if comment:
            Comment.objects.create(
                authorId=self.email,
                targetType='MATERIAL',
                targetId=str(materialId),
                text=comment,
            )

        return verification

    def editMaterialTests(self, materialId, newQuestions): return False
    def viewWorksToCheck(self):
        """Lista prac opłaconych, czekających na moderatora.
        Pomija prace zarezerwowane przez innych moderatorów."""
        return list(
            Work.objects.filter(
                status__in=[Work.STATUS_PAID, Work.STATUS_IN_REVIEW],
            ).filter(
                # Niezarezerwowane LUB zarezerwowane przeze mnie
                models.Q(assignedModeratorId__isnull=True)
                | models.Q(assignedModeratorId='')
                | models.Q(assignedModeratorId=self.email)
            ).order_by('submittedAt')
        )

    def checkWork(self, workId, reviewData: dict):
        """Tworzy WorkReview (szkic) lub zwraca istniejący (UC40)."""
        try:
            work = Work.objects.get(pk=workId, assignedModeratorId=self.email)
        except Work.DoesNotExist:
            return None

        review, _ = WorkReview.objects.get_or_create(
            workId=str(workId),
            moderatorId=self.email,
            defaults={
                'grade': reviewData.get('grade', ''),
                'generalComment': reviewData.get('generalComment', ''),
                'status': WorkReview.STATUS_DRAFT,
            },
        )
        return review


class Admin(User):
    def viewSystemStats(self):
        """Statystyki dla dashboardu admina."""
        return {
            'total_users': User.objects.count(),
            'total_students': Student.objects.count(),
            'total_moderators': Moderator.objects.count(),
            'total_admins': Admin.objects.count(),
            'materials_pending': Material.objects.filter(
                status=Material.STATUS_PENDING
            ).count(),
            'materials_verified': Material.objects.filter(isVerified=True).count(),
            'reports_open': Report.objects.filter(
                status=Report.STATUS_PENDING
            ).count(),
            'works_pending': Work.objects.filter(
                status__in=[Work.STATUS_PAID, Work.STATUS_IN_REVIEW]
            ).count(),
            'applications_pending': ModeratorApplication.objects.filter(
                status=ModeratorApplication.STATUS_PENDING
            ).count(),
        }

    def reviewModeratorApplications(self):
        return list(
            ModeratorApplication.objects.filter(status='PENDING').order_by('createdAt')
        )

    def acceptCandidate(self, applicationId):
        """FR-12: akceptuje wniosek — promuje Studenta na Moderatora.
        Przy MTI tworzymy wiersz potomny Moderator dla istniejącego User
        i usuwamy wiersz Student (rolę rozstrzyga middleware po tabeli potomnej)."""
        try:
            application = ModeratorApplication.objects.get(pk=applicationId)
        except ModeratorApplication.DoesNotExist:
            return False
        if application.status != 'PENDING':
            return False

        promoted = promote_to_moderator(application.candidateId)
        if not promoted:
            return False

        application.status = 'ACCEPTED'
        application.reviewedAt = timezone.now()
        application.reviewedBy = self.email
        application.save(update_fields=['status', 'reviewedAt', 'reviewedBy'])

        Notification.objects.create(
            userId=application.candidateId,
            message=(
                'Gratulacje! Twój wniosek o rolę moderatora został zaakceptowany. '
                'Po ponownym zalogowaniu zobaczysz panel moderatora.'
            ),
        )
        return True

    def rejectCandidate(self, applicationId, reason=''):
        """FR-12: odrzuca wniosek o rolę moderatora."""
        try:
            application = ModeratorApplication.objects.get(pk=applicationId)
        except ModeratorApplication.DoesNotExist:
            return False
        if application.status != 'PENDING':
            return False

        application.status = 'REJECTED'
        application.decisionComment = reason
        application.reviewedAt = timezone.now()
        application.reviewedBy = self.email
        application.save(update_fields=[
            'status', 'decisionComment', 'reviewedAt', 'reviewedBy',
        ])

        Notification.objects.create(
            userId=application.candidateId,
            message='Twój wniosek o rolę moderatora został odrzucony.',
            details=(f'Powód decyzji: {reason}' if reason else ''),
        )
        return True

    def revokeModerator(self, moderatorEmail, reason=''):
        """FR-12: odbiera uprawnienia moderatora (Moderator → Student)."""
        if not demote_to_student(moderatorEmail):
            return False
        Notification.objects.create(
            userId=moderatorEmail,
            message='Twoje uprawnienia moderatora zostały cofnięte.',
            details=(f'Powód decyzji: {reason}' if reason else ''),
        )
        return True

    def handleUserReports(self):
        """Lista nierozpatrzonych zgłoszeń."""
        return list(Report.objects.filter(status=Report.STATUS_PENDING))

    def reviewReport(self, reportId, decision, comment=''):
        """Rozpatrzenie zgłoszenia (UC47). decision: RESOLVED | DISMISSED."""
        try:
            report = Report.objects.get(pk=reportId)
        except Report.DoesNotExist:
            return False

        report.review(decision, admin_email=self.email)

        # Uznanie zgłoszenia za zasadne (RESOLVED) usuwa materiał, którego
        # dotyczyło — wraz z powiadomieniem autora.
        if decision == Report.STATUS_RESOLVED and report.targetType == Report.TARGET_MATERIAL:
            material = Material.objects.filter(pk=report.targetId).first()
            if material:
                Notification.objects.create(
                    userId=material.authorId,
                    message=(
                        f'Twój materiał „{material.title}" został usunięty po '
                        f'rozpatrzeniu zgłoszenia (naruszenie regulaminu).'
                    ),
                    details=(f'Komentarz administratora: {comment}' if comment else ''),
                )
                material.delete()

        # Powiadomienie dla zgłaszającego
        msg_map = {
            Report.STATUS_RESOLVED: (
                'Twoje zgłoszenie zostało uznane za zasadne. '
                'Dziękujemy za dbanie o jakość platformy.'
            ),
            Report.STATUS_DISMISSED: (
                'Po rozpatrzeniu Twoje zgłoszenie zostało odrzucone. '
                'Materiał nie narusza regulaminu.'
            ),
        }
        Notification.objects.create(
            userId=report.reporterId,
            message=msg_map.get(decision, 'Twoje zgłoszenie zostało rozpatrzone.'),
            details=(f'Komentarz administratora: {comment}' if comment else ''),
        )
        return True

    def manageUserAccount(self, userId, newStatus, days=None, reason=''):
        """Blokada/odblokowanie konta (FR-11, UC48).
        userId jest emailem usera. days=N oznacza blokadę tymczasową —
        zapisujemy termin końca w blockedUntil (auto-odblokowanie przy logowaniu)."""
        try:
            target = User.objects.get(email=userId)
        except User.DoesNotExist:
            return False

        target.status = newStatus
        if newStatus == User.STATUS_BLOCKED:
            target.blockedUntil = (
                timezone.now() + timedelta(days=int(days)) if days else None
            )
        else:
            target.blockedUntil = None
        target.save(update_fields=['status', 'blockedUntil'])

        # Powiadomienie dla usera
        if newStatus == User.STATUS_BLOCKED:
            if target.blockedUntil:
                until = timezone.localtime(target.blockedUntil).strftime('%d.%m.%Y %H:%M')
                msg = f'Twoje konto zostało zablokowane do {until}.'
            else:
                msg = 'Twoje konto zostało zablokowane bezterminowo.'
            msg += ' Powód: naruszenie regulaminu. W razie pytań skontaktuj się z administracją.'
        elif newStatus == User.STATUS_ACTIVE:
            msg = 'Twoje konto zostało odblokowane. Witamy z powrotem.'
        else:
            msg = f'Status Twojego konta zmieniony na: {newStatus}.'

        Notification.objects.create(
            userId=target.email, message=msg,
            details=(f'Powód: {reason}' if reason else ''),
        )

        # Zablokowany user = wylogowanie wszystkich sesji
        if newStatus != User.STATUS_ACTIVE:
            Session.objects.filter(userId=target.email).delete()

        return True

    def deleteMaterial(self, materialId, reason='') -> bool:
        """FR-11/O-06: admin może usunąć dowolny materiał."""
        material = Material.objects.filter(pk=materialId).first()
        if not material:
            return False
        Notification.objects.create(
            userId=material.authorId,
            message=(
                f'Twój materiał „{material.title}" został usunięty przez '
                f'administratora.'
            ),
            details=(f'Powód: {reason}' if reason else ''),
        )
        material.delete()
        return True


# ============================================================
# Sesje i tokeny
# ============================================================
class Session(models.Model):
    userId = models.CharField(max_length=255, db_index=True)
    token = models.CharField(max_length=255, unique=True)
    expiresAt = models.DateTimeField(default=_default_session_expiry)

    @classmethod
    def create(cls, userId: str) -> 'Session':
        return cls.objects.create(
            userId=userId,
            token=str(uuid.uuid4()),
            expiresAt=_default_session_expiry(),
        )

    def is_valid(self) -> bool:
        return self.expiresAt > timezone.now()

    def refresh(self) -> None:
        """Odświeża sesję jeśli zostało <1h do wygaśnięcia."""
        threshold = timezone.now() + timedelta(hours=settings.SESSION_REFRESH_THRESHOLD_HOURS)
        if self.expiresAt < threshold:
            self.expiresAt = _default_session_expiry()
            self.save(update_fields=['expiresAt'])

    def invalidate(self) -> None:
        self.delete()


class EmailVerificationToken(models.Model):
    userId = models.CharField(max_length=255, db_index=True)
    # FIX: callable defaulty — inaczej Django ewaluuje wartość raz przy starcie
    token = models.CharField(max_length=10, default=_default_email_token)
    expiresAt = models.DateTimeField(default=_default_email_token_expiry)

    def verify(self) -> bool:
        return self.expiresAt > timezone.now()


def _default_reset_token() -> str:
    return uuid.uuid4().hex


def _default_reset_expiry():
    return timezone.now() + timedelta(hours=1)


class PasswordResetToken(models.Model):
    """Token resetu hasła (funkcja „Zapomniałem hasła"). Ważny 1h, jednorazowy."""
    userId = models.CharField(max_length=255, db_index=True)
    token = models.CharField(max_length=64, unique=True, default=_default_reset_token)
    expiresAt = models.DateTimeField(default=_default_reset_expiry)
    used = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True)

    @classmethod
    def issue(cls, email: str) -> 'PasswordResetToken':
        """Tworzy świeży token, unieważniając wcześniejsze dla tego maila."""
        cls.objects.filter(userId=email, used=False).update(used=True)
        return cls.objects.create(userId=email)

    def is_valid(self) -> bool:
        return (not self.used) and self.expiresAt > timezone.now()


# ============================================================
# Materiały + pliki
# ============================================================
class Material(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_VERIFIED = 'VERIFIED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Oczekuje'),
        (STATUS_VERIFIED, 'Zweryfikowany'),
        (STATUS_REJECTED, 'Odrzucony'),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    authorId = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=100, blank=True)  # grammar/reading/listening/vocabulary
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_PENDING)
    priority = models.IntegerField(default=0)
    isVerified = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority', '-id']

    def __str__(self) -> str:
        return self.title

    @classmethod
    def create(cls, data: dict, files=None) -> 'Material':
        material = cls.objects.create(
            title=data.get('title', ''),
            content=data.get('content', ''),
            authorId=data.get('authorId', ''),
            category=data.get('category', ''),
            status=cls.STATUS_PENDING,
            priority=0,
            isVerified=False,
        )
        if files:
            for f in files:
                att = FileAttachment()
                if att.upload(f):
                    att.material = material
                    att.save()
        return material

    def addTest(self, test: 'Test') -> bool:
        test.materialId = str(self.id)
        test.save()
        return True

    def addFile(self, file_attachment: 'FileAttachment') -> bool:
        try:
            file_attachment.material = self
            file_attachment.save()
            return True
        except Exception:
            return False

    def increasePriority(self) -> None:
        self.priority = (self.priority or 0) + 1
        self.save(update_fields=['priority'])

    def getDetails(self) -> 'Material':
        return self


class FileAttachment(models.Model):
    fileName = models.CharField(max_length=255)
    filePath = models.CharField(max_length=500)
    fileType = models.CharField(max_length=50, blank=True)
    sizeBytes = models.BigIntegerField(default=0)
    uploadedAt = models.DateTimeField(auto_now_add=True)
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='attachments',
    )
    work = models.ForeignKey(
        'Work',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='attachments',
    )

    def upload(self, fileStream) -> bool:
        try:
            self.fileName = fileStream.name
            self.sizeBytes = getattr(fileStream, 'size', 0)
            self.fileType = getattr(fileStream, 'content_type', '')
            folder = 'uploads/'
            name = default_storage.save(os.path.join(folder, self.fileName), fileStream)
            self.filePath = name
            self.save()
            return True
        except Exception as e:  # noqa: BLE001
            print(f'Błąd podczas uploadu: {e}')
            return False


# ============================================================
# Testy i pytania (Test / DiagnosticTest / Question / TestResult)
# ============================================================
class Test(models.Model):
    TYPE_DIAGNOSTIC = 'DIAGNOSTIC'
    TYPE_MATERIAL = 'MATERIAL'
    TYPE_MODERATOR = 'MODERATOR'

    TYPE_EXAM = 'EXAM'

    title = models.CharField(max_length=255)
    type = models.CharField(max_length=50, default=TYPE_MATERIAL)
    materialId = models.CharField(max_length=255, blank=True)
    # Sprint 3 (FR-06): limit czasu w minutach. 0 = bez limitu (testy materiałowe,
    # diagnostyka). Symulacja egzaminu ustawia np. 60.
    durationMinutes = models.IntegerField(default=0)

    def addQuestion(self, question: 'Question') -> bool:
        question.test = self
        question.save()
        return True

    def calculateScore(self, answers: dict) -> float:
        """Porównuje odpowiedzi z kluczem. Zwraca procent poprawnych (0–100)."""
        questions = list(self.questions.all())
        if not questions:
            return 0.0
        correct = sum(
            1 for q in questions
            if str(answers.get(str(q.id), '')).strip() == q.correctAnswer.strip()
        )
        return round(100.0 * correct / len(questions), 2)


class DiagnosticTest(Test):
    """Test diagnostyczny z podziałem na obszary (gramatyka/słuchanie/czytanie/słownictwo).
    UC04 + UC05."""

    def calculateAreaScores(self, answers: dict) -> dict[str, float]:
        """Zwraca słownik {obszar: procent poprawnych}."""
        area_stats: dict[str, list[int]] = {}  # area -> [correct, total]
        for q in self.questions.all():
            area = q.area or 'general'
            area_stats.setdefault(area, [0, 0])
            area_stats[area][1] += 1
            if str(answers.get(str(q.id), '')).strip() == q.correctAnswer.strip():
                area_stats[area][0] += 1
        return {
            area: round(100.0 * correct / total, 2) if total else 0.0
            for area, (correct, total) in area_stats.items()
        }


class Question(models.Model):
    QTYPE_SINGLE = 'SINGLE_CHOICE'
    QTYPE_MULTI = 'MULTI_CHOICE'
    QTYPE_TEXT = 'TEXT'

    test = models.ForeignKey(
        Test, on_delete=models.CASCADE,
        null=True, blank=True, related_name='questions',
    )
    text = models.TextField()
    qType = models.CharField(max_length=50, default=QTYPE_SINGLE)
    options = models.JSONField(default=list, blank=True)  # ["A", "B", "C", "D"]
    correctAnswer = models.CharField(max_length=255)
    points = models.IntegerField(default=1)
    area = models.CharField(max_length=50, blank=True)  # grammar/listening/reading/vocabulary


class TestResult(models.Model):
    testId = models.CharField(max_length=255, db_index=True)
    userId = models.CharField(max_length=255, db_index=True)
    score = models.FloatField(default=0.0)
    answers = models.JSONField(default=dict)
    completedAt = models.DateTimeField(auto_now_add=True)


class DiagnosticResult(TestResult):
    areaScores = models.JSONField(default=dict)

    def getWeakAreas(self, threshold: float = 50.0) -> list[str]:
        """Zwraca listę obszarów z wynikiem poniżej progu (domyślnie 50% — FR-05)."""
        return [area for area, score in self.areaScores.items() if score < threshold]


# ============================================================
# Encje pod Sprint 2 — szkielety (nie implementujemy logiki teraz)
# ============================================================
class Favorite(models.Model):
    userId = models.CharField(max_length=255)
    materialId = models.CharField(max_length=255)
    addedAt = models.DateTimeField(auto_now_add=True)


class Vote(models.Model):
    userId = models.CharField(max_length=255)
    materialId = models.CharField(max_length=255)
    votedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Jeden user nie może oddać dwóch głosów na ten sam materiał (FR-09)
        unique_together = [('userId', 'materialId')]
        indexes = [models.Index(fields=['materialId'])]


class Notification(models.Model):
    userId = models.CharField(max_length=255, db_index=True)
    message = models.TextField()
    # Dłuższa treść do wglądu (np. komentarz moderatora/admina) — w UI
    # rozwijana przyciskiem „Pokaż szczegóły".
    details = models.TextField(blank=True, default='')
    link = models.CharField(max_length=500, blank=True)  # URL dokąd ma prowadzić klik
    isRead = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-createdAt']

    def send(self):
        """Alias dla save() — trzyma kontrakt z classDiagram.md."""
        self.save()

    def markAsRead(self):
        self.isRead = True
        self.save(update_fields=['isRead'])


class Work(models.Model):
    STATUS_PENDING_PAYMENT = 'PENDING_PAYMENT'
    STATUS_PAID = 'PAID'              # Zapłacone, czeka na moderatora
    STATUS_IN_REVIEW = 'IN_REVIEW'    # Moderator ją zarezerwował
    STATUS_REVIEWED = 'REVIEWED'      # Moderator wystawił ocenę (PUBLISHED)
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PENDING_PAYMENT, 'Oczekuje na płatność'),
        (STATUS_PAID, 'Opłacone — w kolejce'),
        (STATUS_IN_REVIEW, 'W trakcie sprawdzania'),
        (STATUS_REVIEWED, 'Sprawdzone'),
        (STATUS_CANCELLED, 'Anulowane'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    studentId = models.CharField(max_length=255, db_index=True)
    packageId = models.CharField(max_length=255)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default=STATUS_PENDING_PAYMENT,
    )
    assignedModeratorId = models.CharField(max_length=255, null=True, blank=True)
    submittedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submittedAt']
        indexes = [models.Index(fields=['status', 'submittedAt'])]

    @classmethod
    def submit(cls, files, packageId, studentId='', title='', description=''):
        """Kompatybilność z sygnaturą z classDiagram.md, ale w praktyce
        używamy Student.submitWork()."""
        work = cls.objects.create(
            title=title, description=description,
            studentId=studentId, packageId=str(packageId),
            status=cls.STATUS_PENDING_PAYMENT,
        )
        if files:
            for f in files:
                att = FileAttachment()
                if att.upload(f):
                    att.work = work
                    att.save()
        return work

    def assignModerator(self, moderatorId):
        if self.assignedModeratorId and self.assignedModeratorId != moderatorId:
            return False
        self.assignedModeratorId = moderatorId
        self.status = self.STATUS_IN_REVIEW
        self.save(update_fields=['assignedModeratorId', 'status'])
        return True


class Package(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField(default=0.0)
    scope = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f'{self.name} ({self.price} zł)'

    def select(self):
        return self


class PaymentTransaction(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_FAILED = 'FAILED'

    METHOD_BLIK = 'BLIK'
    METHOD_CARD = 'CARD'
    METHOD_TRANSFER = 'TRANSFER'
    # Rozliczenie indywidualne — student i sprawdzający ustalają płatność
    # bezpośrednio między sobą (poza platformą).
    METHOD_DIRECT = 'DIRECT'

    workId = models.CharField(max_length=255, db_index=True)
    userId = models.CharField(max_length=255)
    amount = models.FloatField(default=0.0)
    status = models.CharField(max_length=50, default=STATUS_PENDING)
    method = models.CharField(max_length=50, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    completedAt = models.DateTimeField(null=True, blank=True)

    def process(self):
        """MOCK BRAMKI PŁATNOŚCI.
        W Sprincie 2 zawsze zwraca sukces. W produkcji integracja z Przelewy24.
        Zwraca True przy sukcesie."""
        from .services import PaymentGateway
        gateway = PaymentGateway()
        self.status = self.STATUS_PROCESSING
        self.save(update_fields=['status'])

        success = gateway.charge(self.amount)
        if success:
            self.status = self.STATUS_COMPLETED
            self.completedAt = timezone.now()
            self.save(update_fields=['status', 'completedAt'])

            # Przejście Work w status PAID
            try:
                work = Work.objects.get(pk=self.workId)
                work.status = Work.STATUS_PAID
                work.save(update_fields=['status'])
            except Work.DoesNotExist:
                pass
            return True
        else:
            self.status = self.STATUS_FAILED
            self.save(update_fields=['status'])
            return False


class WorkReview(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_PUBLISHED = 'PUBLISHED'

    workId = models.CharField(max_length=255, db_index=True)
    moderatorId = models.CharField(max_length=255)
    grade = models.CharField(max_length=50, blank=True)  # A1-C2
    generalComment = models.TextField(blank=True)
    status = models.CharField(max_length=50, default=STATUS_DRAFT)
    createdAt = models.DateTimeField(auto_now_add=True)
    publishedAt = models.DateTimeField(null=True, blank=True)

    def addErrorMark(self, textSnippet, mark_type, positionInText=''):
        mark = ErrorMark.objects.create(
            reviewId=str(self.id),
            textSnippet=textSnippet,
            type=mark_type,
            positionInText=positionInText,
        )
        return mark

    def addComment(self, text, authorId):
        return Comment.objects.create(
            authorId=authorId,
            targetType='WORK_REVIEW',
            targetId=str(self.id),
            text=text,
        )

    def publish(self):
        """Publikuje ocenę — student dostaje notyfikację, Work → REVIEWED."""
        self.status = self.STATUS_PUBLISHED
        self.publishedAt = timezone.now()
        self.save(update_fields=['status', 'publishedAt'])

        try:
            work = Work.objects.get(pk=self.workId)
            work.status = Work.STATUS_REVIEWED
            work.save(update_fields=['status'])

            Notification.objects.create(
                userId=work.studentId,
                message=(
                    f'Twoja praca "{work.title}" została sprawdzona. '
                    f'Ocena: {self.grade or "—"}. Zobacz szczegóły.'
                ),
                details=(f'Komentarz sprawdzającego: {self.generalComment}'
                         if self.generalComment else ''),
                link=f'/works/{work.id}/review/',
            )
        except Work.DoesNotExist:
            pass
        return True


class ErrorMark(models.Model):
    TYPE_GRAMMAR = 'GRAMMAR'      # czerwone
    TYPE_UNNATURAL = 'UNNATURAL'  # żółte
    TYPE_POSITIVE = 'POSITIVE'    # zielone

    TYPE_CHOICES = [
        (TYPE_GRAMMAR, 'Błąd gramatyczny'),
        (TYPE_UNNATURAL, 'Nienaturalne sformułowanie'),
        (TYPE_POSITIVE, 'Dobre sformułowanie'),
    ]

    reviewId = models.CharField(max_length=255, db_index=True)
    textSnippet = models.TextField()
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    positionInText = models.CharField(max_length=255, blank=True)
    comment = models.TextField(blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['createdAt']


class MaterialVerification(models.Model):
    DECISION_ACCEPTED = 'ACCEPTED'
    DECISION_REJECTED = 'REJECTED'
    DECISION_NEEDS_REVISION = 'NEEDS_REVISION'
    DECISION_CHOICES = [
        (DECISION_ACCEPTED, 'Zaakceptowany'),
        (DECISION_REJECTED, 'Odrzucony'),
        (DECISION_NEEDS_REVISION, 'Do poprawy'),
    ]

    materialId = models.CharField(max_length=255, db_index=True)
    moderatorId = models.CharField(max_length=255)
    decision = models.CharField(max_length=50, choices=DECISION_CHOICES, blank=True)
    comment = models.TextField(blank=True)
    verifiedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-verifiedAt']

    def submit(self, decision, comment=''):
        self.decision = decision
        self.comment = comment
        self.save()
        return True


class ModeratorApplication(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_ACCEPTED = 'ACCEPTED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Oczekuje'),
        (STATUS_ACCEPTED, 'Zaakceptowany'),
        (STATUS_REJECTED, 'Odrzucony'),
    ]

    candidateId = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_PENDING)
    testResultId = models.CharField(max_length=255, blank=True)
    # Wynik (%) testu kwalifikacyjnego wypełnianego przy składaniu wniosku.
    testScore = models.FloatField(null=True, blank=True)
    motivation = models.TextField(blank=True)            # FR-12: dlaczego chce zostać moderatorem
    certificatePath = models.CharField(max_length=500, blank=True)  # FR-02: dyplom/certyfikat
    decisionComment = models.TextField(blank=True)
    createdAt = models.DateTimeField(auto_now_add=True, null=True)
    reviewedAt = models.DateTimeField(null=True, blank=True)
    reviewedBy = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['createdAt']

    def submit(self): return True
    def evaluate(self): return True


class Report(models.Model):
    TARGET_MATERIAL = 'MATERIAL'
    TARGET_USER = 'USER'
    TARGET_COMMENT = 'COMMENT'
    TARGET_CHOICES = [
        (TARGET_MATERIAL, 'Materiał'),
        (TARGET_USER, 'Użytkownik'),
        (TARGET_COMMENT, 'Komentarz'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_DISMISSED = 'DISMISSED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Oczekuje'),
        (STATUS_RESOLVED, 'Rozpatrzone'),
        (STATUS_DISMISSED, 'Odrzucone'),
    ]

    reporterId = models.CharField(max_length=255, db_index=True)
    targetType = models.CharField(max_length=50, choices=TARGET_CHOICES)
    targetId = models.CharField(max_length=255, db_index=True)
    reason = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_PENDING)
    createdAt = models.DateTimeField(auto_now_add=True)
    resolvedAt = models.DateTimeField(null=True, blank=True)
    resolvedBy = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-createdAt']
        indexes = [models.Index(fields=['status', 'createdAt'])]

    def submit(self):
        self.save()
        return True

    def review(self, decision, admin_email=''):
        """decision: 'RESOLVED' (potwierdzone) | 'DISMISSED' (odrzucone)."""
        self.status = decision
        self.resolvedAt = timezone.now()
        self.resolvedBy = admin_email
        self.save()
        return True


# ============================================================
# Comment — dodajemy w Sprincie 2 (było w classDiagram.md)
# ============================================================
class Comment(models.Model):
    authorId = models.CharField(max_length=255)
    targetType = models.CharField(max_length=50)  # MATERIAL / WORK / etc.
    targetId = models.CharField(max_length=255, db_index=True)
    text = models.TextField()
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-createdAt']


class Statistics(models.Model):
    """Placeholder — rozbudowa w Sprincie 3 (patrz UserStats poniżej)."""
    pass


# ============================================================
# Sprint 3 — symulacja egzaminu (FR-06), gamifikacja (FR-07),
# wypłaty moderatorów (FR-14)
# ============================================================
class ExamAttempt(models.Model):
    """Pojedyncze podejście studenta do symulacji egzaminu (FR-06).

    Twardy timer jest egzekwowany SERWEROWO: przy starcie zapisujemy
    `deadline = startedAt + durationMinutes`. Po przekroczeniu deadline
    odpowiedzi nie są już przyjmowane (`is_expired()`), niezależnie od tego
    co robi przeglądarka. Zegar po stronie klienta to tylko UX.
    """
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, 'W trakcie'),
        (STATUS_SUBMITTED, 'Zakończone'),
    ]

    testId = models.CharField(max_length=255, db_index=True)
    userId = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    answers = models.JSONField(default=dict)        # autozapis (NFR-02)
    score = models.FloatField(default=0.0)
    areaScores = models.JSONField(default=dict)
    pointsAwarded = models.IntegerField(default=0)
    startedAt = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(null=True, blank=True)
    submittedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-startedAt']
        indexes = [models.Index(fields=['userId', 'status'])]

    @classmethod
    def start(cls, test: 'Test', userId: str) -> 'ExamAttempt':
        """Tworzy nowe podejście i ustawia twardy deadline."""
        now = timezone.now()
        duration = test.durationMinutes or 0
        deadline = now + timedelta(minutes=duration) if duration else None
        return cls.objects.create(
            testId=str(test.id), userId=str(userId),
            status=cls.STATUS_IN_PROGRESS, deadline=deadline,
        )

    def is_expired(self) -> bool:
        return self.deadline is not None and timezone.now() > self.deadline

    def seconds_left(self) -> int:
        if self.deadline is None:
            return 0
        delta = (self.deadline - timezone.now()).total_seconds()
        return max(0, int(delta))

    def submit(self, answers: dict | None = None) -> 'ExamAttempt':
        """Kończy podejście: liczy wynik, przyznaje punkty (FR-07).
        Idempotentne — drugi submit nic nie zmienia."""
        if self.status == self.STATUS_SUBMITTED:
            return self
        if answers is not None:
            self.answers = answers

        try:
            test = Test.objects.get(pk=self.testId)
        except Test.DoesNotExist:
            test = None

        if test is not None:
            self.score = test.calculateScore(self.answers)
            # Wyniki per obszar (te same area co w diagnostyce)
            area_stats: dict[str, list[int]] = {}
            for q in test.questions.all():
                area = q.area or 'general'
                area_stats.setdefault(area, [0, 0])
                area_stats[area][1] += 1
                if str(self.answers.get(str(q.id), '')).strip() == q.correctAnswer.strip():
                    area_stats[area][0] += 1
            self.areaScores = {
                a: round(100.0 * c / t, 2) if t else 0.0
                for a, (c, t) in area_stats.items()
            }

        # Gamifikacja (FR-07): punkty = zaokrąglony wynik procentowy.
        self.pointsAwarded = int(round(self.score))
        self.status = self.STATUS_SUBMITTED
        self.submittedAt = timezone.now()
        self.save()

        UserStats.record_exam(self.userId, self.pointsAwarded)
        return self


class UserStats(models.Model):
    """Zagregowane statystyki + punkty rankingowe użytkownika (FR-07).

    Klucz to email (spójnie z resztą modeli, które trzymają userId jako email).
    """
    userId = models.CharField(max_length=255, unique=True, db_index=True)
    points = models.IntegerField(default=0)
    examsCompleted = models.IntegerField(default=0)
    diagnosticsCompleted = models.IntegerField(default=0)
    bestExamScore = models.FloatField(default=0.0)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-points']

    @classmethod
    def for_user(cls, userId: str) -> 'UserStats':
        stats, _ = cls.objects.get_or_create(userId=str(userId))
        return stats

    @classmethod
    def record_exam(cls, userId: str, points: int) -> 'UserStats':
        stats = cls.for_user(userId)
        stats.points = (stats.points or 0) + max(0, points)
        stats.examsCompleted = (stats.examsCompleted or 0) + 1
        if points > stats.bestExamScore:
            stats.bestExamScore = points
        stats.save(update_fields=[
            'points', 'examsCompleted', 'bestExamScore', 'updatedAt',
        ])
        return stats

    @classmethod
    def record_diagnostic(cls, userId: str, points: int = 10) -> 'UserStats':
        stats = cls.for_user(userId)
        stats.points = (stats.points or 0) + max(0, points)
        stats.diagnosticsCompleted = (stats.diagnosticsCompleted or 0) + 1
        stats.save(update_fields=['points', 'diagnosticsCompleted', 'updatedAt'])
        return stats


class Payout(models.Model):
    """Wypłata zarobków moderatora (FR-14)."""
    STATUS_PENDING = 'PENDING'
    STATUS_PAID = 'PAID'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Oczekuje na realizację'),
        (STATUS_PAID, 'Zrealizowana'),
    ]

    moderatorId = models.CharField(max_length=255, db_index=True)
    amount = models.FloatField(default=0.0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_PENDING)
    invoiceNumber = models.CharField(max_length=64, blank=True)
    requestedAt = models.DateTimeField(auto_now_add=True)
    paidAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requestedAt']

    @classmethod
    def create_for(cls, moderatorId: str, amount: float) -> 'Payout':
        payout = cls.objects.create(
            moderatorId=str(moderatorId),
            amount=round(amount, 2),
            status=cls.STATUS_PENDING,
        )
        # Numer faktury: FV/<rok>/<id> — zgodnie z O-02 (dokumentacja skarbowa)
        payout.invoiceNumber = f'FV/{timezone.now().year}/{payout.id:05d}'
        payout.save(update_fields=['invoiceNumber'])
        Notification.objects.create(
            userId=str(moderatorId),
            message=(
                f'Zlecono wypłatę {payout.amount:.2f} zł '
                f'(faktura {payout.invoiceNumber}). Realizacja do 7 dni roboczych.'
            ),
        )
        return payout


class ModeratorRating(models.Model):
    """Ocena sprawdzającego wystawiona przez zleceniodawcę (1-5 gwiazdek)
    po opublikowanej ocenie pracy. Jedna ocena na pracę."""
    workId = models.CharField(max_length=255, db_index=True)
    studentId = models.CharField(max_length=255, db_index=True)
    moderatorId = models.CharField(max_length=255, db_index=True)
    score = models.PositiveSmallIntegerField()  # 1-5
    comment = models.TextField(blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('workId', 'studentId')]

    @classmethod
    def average_for(cls, moderator_email):
        """Średnia ocen i liczba głosów dla danego sprawdzającego."""
        from django.db.models import Avg, Count
        agg = cls.objects.filter(moderatorId=moderator_email).aggregate(
            avg=Avg('score'), cnt=Count('id'),
        )
        return (round(agg['avg'], 2) if agg['avg'] is not None else None,
                agg['cnt'] or 0)


# ============================================================
# Helpery promocji/degradacji ról (FR-12) — multi-table inheritance.
# Tworzymy/usuwamy wiersz potomny dla istniejącego wiersza User; rolę
# rozstrzyga SessionAuthMiddleware._resolve_role po tabeli potomnej.
#
# UWAGA: nie wolno usuwać roli przez `Student.objects.delete()` — w MTI
# usunięcie instancji potomnej KASKADOWO usuwa też wiersz rodzica (User).
# Dlatego wiersz tabeli potomnej kasujemy surowym SQL-em (tylko ta tabela).
# ============================================================
def _delete_child_row(child_model, pk) -> None:
    from django.db import connection
    table = child_model._meta.db_table
    pk_col = child_model._meta.pk.column  # 'user_ptr_id'
    with connection.cursor() as cursor:
        cursor.execute(
            f'DELETE FROM "{table}" WHERE "{pk_col}" = %s', [pk]
        )


def promote_to_moderator(email: str) -> bool:
    try:
        base = User.objects.get(email=email)
    except User.DoesNotExist:
        return False
    if Moderator.objects.filter(pk=base.pk).exists():
        return True  # już moderator
    # Wstaw wiersz potomny Moderator wskazujący na ten sam User (raw=True →
    # zapisujemy tylko tabelę lokalną, bez ponownego INSERT-u rodzica).
    mod = Moderator(user_ptr_id=base.pk)
    mod.save_base(raw=True)
    # Usuń TYLKO wiersz potomny Student (User zostaje nietknięty).
    _delete_child_row(Student, base.pk)
    return True


def demote_to_student(email: str) -> bool:
    try:
        base = User.objects.get(email=email)
    except User.DoesNotExist:
        return False
    if not Moderator.objects.filter(pk=base.pk).exists():
        return False
    if not Student.objects.filter(pk=base.pk).exists():
        st = Student(user_ptr_id=base.pk)
        st.save_base(raw=True)
    _delete_child_row(Moderator, base.pk)
    return True
