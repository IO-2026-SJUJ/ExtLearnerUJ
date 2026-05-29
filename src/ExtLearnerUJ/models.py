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

    # -------------------------
    # Logowanie / sesje
    # -------------------------
    @classmethod
    def authenticate(cls, email: str, password: str) -> 'Session | None':
        """Sprawdza dane logowania i tworzy sesję. UC03."""
        try:
            user = cls.objects.get(email=email)
        except cls.DoesNotExist:
            return None
        if user.status != cls.STATUS_ACTIVE:
            return None
        if not user.emailVerified:
            return None
        if not check_password(password, user.password):
            return None
        return Session.create(user.email)

    def logout(self) -> None:
        Session.objects.filter(userId=self.email).delete()

    # -------------------------
    # Usuwanie konta (RODO — O-01)
    # -------------------------
    def deleteAccount(self) -> bool:
        try:
            email = self.email
            Session.objects.filter(userId=email).delete()
            EmailVerificationToken.objects.filter(userId=email).delete()
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


class Student(User):
    """Podstawowy użytkownik. W Sprincie 1 implementujemy:
    takeDiagnosticTest, browseMaterials, viewMaterial."""

    def takeDiagnosticTest(self):
        """Zwraca aktywny test diagnostyczny (pierwszy DiagnosticTest w bazie).
        Właściwa logika oceniania jest w GradingService.autoGradeDiagnostic."""
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

    # Stuby pod Sprint 2
    def viewRecommendations(self):
        return []

    def addToFavorites(self, materialId):
        return None

    def voteMaterial(self, materialId):
        """Oddaje głos na materiał (zwiększa jego priorytet).
        Idempotentne — drugi głos tego samego usera nic nie robi (FR-09)."""
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
        """Przesyła pracę pisemną do sprawdzenia (FR-15, UC19).
        Tworzy Work w statusie PENDING_PAYMENT — po udanej płatności
        przechodzi w PAID i trafia do kolejki moderatora."""
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
        # Upload plików — jeśli są
        if files:
            for f in files:
                att = FileAttachment()
                if att.upload(f):
                    att.work = work
                    att.save()
        return work

    def viewStats(self):
        pass

    def downloadLearningReport(self):
        from .services import ReportGenerator
        return ReportGenerator().buildPdf(self.id, 'all')

    def applyForModerator(self):
        return None

    def rateModerator(self, workId, score, comment):
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

    def reserveWork(self, workId):
        """Rezerwuje pracę do sprawdzenia (UC39). Idempotentne —
        jeśli moderator już ją miał, zwraca True."""
        try:
            work = Work.objects.get(pk=workId)
        except Work.DoesNotExist:
            return False

        # Czy ktoś inny nie zarezerwował wcześniej?
        if work.assignedModeratorId and work.assignedModeratorId != self.email:
            return False

        work.assignedModeratorId = self.email
        work.status = Work.STATUS_IN_REVIEW
        work.save(update_fields=['assignedModeratorId', 'status'])
        return True

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

    def viewModeratorStats(self): pass


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
        }

    def reviewModeratorApplications(self):
        return list(ModeratorApplication.objects.filter(status='PENDING'))

    def acceptCandidate(self, applicationId): return False
    def rejectCandidate(self, applicationId, reason): return False

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
        )
        return True

    def manageUserAccount(self, userId, newStatus, days=None):
        """Blokada/odblokowanie konta (FR-11, UC48).
        userId jest emailem usera. days=N oznacza blokadę tymczasową."""
        try:
            target = User.objects.get(email=userId)
        except User.DoesNotExist:
            return False

        target.status = newStatus
        target.save(update_fields=['status'])

        # Powiadomienie dla usera
        if newStatus == User.STATUS_BLOCKED:
            msg = (f'Twoje konto zostało zablokowane na {days} dni.'
                   if days else 'Twoje konto zostało zablokowane.')
            msg += ' Powód: naruszenie regulaminu. W razie pytań skontaktuj się z administracją.'
        elif newStatus == User.STATUS_ACTIVE:
            msg = 'Twoje konto zostało odblokowane. Witamy z powrotem.'
        else:
            msg = f'Status Twojego konta zmieniony na: {newStatus}.'

        Notification.objects.create(userId=target.email, message=msg)

        # Zablokowany user = wylogowanie wszystkich sesji
        if newStatus != User.STATUS_ACTIVE:
            Session.objects.filter(userId=target.email).delete()

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

    title = models.CharField(max_length=255)
    type = models.CharField(max_length=50, default=TYPE_MATERIAL)
    materialId = models.CharField(max_length=255, blank=True)

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
    candidateId = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default='PENDING')
    testResultId = models.CharField(max_length=255, blank=True)

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
    """Placeholder — rozbudowa w Sprincie 3."""
    pass
