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
    hours = getattr(settings, 'SESSION_LIFETIME_HOURS', 24)
    return timezone.now() + timedelta(hours=hours)


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
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST', 'noreply@example.com')
        send_mail(subject, message, from_email, [self.email])

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
        report = Report(
            reporterId=self.email,
            targetType=targetType,
            targetId=targetId,
            reason=reason,
        )
        report.submit()
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
        return None

    def submitWork(self, workData, packageId, files):
        return None

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
    # Implementacja w Sprincie 2
    def viewMaterialsToVerify(self): return []
    def verifyMaterial(self, materialId, decision, comment): return None
    def editMaterialTests(self, materialId, newQuestions): return False
    def viewWorksToCheck(self): return []
    def reserveWork(self, workId): return False
    def checkWork(self, workId, reviewData): return None
    def viewModeratorStats(self): pass


class Admin(User):
    # Implementacja w Sprincie 2/3
    def viewSystemStats(self): return {}
    def reviewModeratorApplications(self): return []
    def acceptCandidate(self, applicationId): return False
    def rejectCandidate(self, applicationId, reason): return False
    def handleUserReports(self): return []
    def reviewReport(self, reportId, decision): return False
    def manageUserAccount(self, userId, newStatus, newRole): pass


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
        threshold_hours = getattr(settings, 'SESSION_REFRESH_THRESHOLD_HOURS', 1)
        threshold = timezone.now() + timedelta(hours=threshold_hours)
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


class Notification(models.Model):
    userId = models.CharField(max_length=255)
    message = models.TextField()
    isRead = models.BooleanField(default=False)

    def send(self): pass
    def markAsRead(self):
        self.isRead = True
        self.save()


class Work(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    studentId = models.CharField(max_length=255)
    packageId = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default='PENDING')
    assignedModeratorId = models.CharField(max_length=255, null=True, blank=True)

    @classmethod
    def submit(cls, files, packageId): return None
    def assignModerator(self, moderatorId): return False


class Package(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField(default=0.0)
    scope = models.CharField(max_length=255, blank=True)

    def select(self): return self


class PaymentTransaction(models.Model):
    workId = models.CharField(max_length=255)
    userId = models.CharField(max_length=255)
    amount = models.FloatField(default=0.0)
    status = models.CharField(max_length=50, default='PENDING')
    method = models.CharField(max_length=50, blank=True)

    def process(self): return False


class WorkReview(models.Model):
    workId = models.CharField(max_length=255)
    moderatorId = models.CharField(max_length=255)
    grade = models.CharField(max_length=50, blank=True)
    generalComment = models.TextField(blank=True)
    status = models.CharField(max_length=50, default='DRAFT')

    def addErrorMark(self, mark): return mark
    def addComment(self, comment): return comment
    def publish(self):
        self.status = 'PUBLISHED'
        self.save()
        return True


class ErrorMark(models.Model):
    reviewId = models.CharField(max_length=255)
    textSnippet = models.TextField()
    type = models.CharField(max_length=50)
    positionInText = models.CharField(max_length=255, blank=True)


class MaterialVerification(models.Model):
    materialId = models.CharField(max_length=255)
    moderatorId = models.CharField(max_length=255)
    decision = models.CharField(max_length=50, blank=True)

    def submit(self, decision, comment):
        self.decision = decision
        self.save()
        return True


class ModeratorApplication(models.Model):
    candidateId = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default='PENDING')
    testResultId = models.CharField(max_length=255, blank=True)

    def submit(self): return True
    def evaluate(self): return True


class Report(models.Model):
    reporterId = models.CharField(max_length=255)
    targetType = models.CharField(max_length=50)
    targetId = models.CharField(max_length=255)
    reason = models.TextField()
    status = models.CharField(max_length=50, default='PENDING')

    def submit(self):
        self.save()
        return True

    def review(self, decision):
        self.status = decision
        self.save()
        return True


class Statistics(models.Model):
    """Placeholder — rozbudowa w Sprincie 3."""
    pass
