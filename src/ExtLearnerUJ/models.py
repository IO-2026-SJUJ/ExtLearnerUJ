from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import make_password, check_password
from django.urls import path
from django.core.mail import send_mail
from django.conf import settings
import random
import uuid
import os
from django.core.files.storage import default_storage
from django.urls import path
from django.core.mail import send_mail
from django.conf import settings
import random
from . import views # upewnij się, że masz plik views.py

class User(models.Model):
    email = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    emailVerified = models.BooleanField(default=False)
    registrationDate = models.DateTimeField(auto_now_add=True)

    def register(self, email, password, name):
        hashed_password = make_password(password)
    
        if User.objects.filter(email=email).exists():
            return False

        user = User.objects.create(
        email=email, 
        password=hashed_password, 
        name=name,
        status="ACTIVE"
        )

        token = EmailVerificationToken.objects.create(userId=user.email).token
        self.send_verification_email(user.email, token)
        
        return User.objects.filter(email=email).exists()

    def send_verification_email(self, email, token_code):
        subject = 'Twój kod weryfikacyjny - ExtLearnerUJ'

        message = f'Witaj {email}!\n\nTwój kod do weryfikacji konta to: {token_code}\n\nKod jest ważny przez 24 \\h.'
    
        send_mail(
            subject, 
            message, 
            settings.EMAIL_HOST, 
            [email]
        )

    def verifyEmail(self, id):
        try:
            token = EmailVerificationToken.objects.get(userId=self.email, token=id)
            self.emailVerified = True
            self.save()
            token.delete()
            return True
        
        except EmailVerificationToken.DoesNotExist:
            return False

    def login(self, email, password):
        try:
            user = User.objects.get(email=email)
            if check_password(password, user.password):
                if user.status != "ACTIVE":
                    return None
                return Session.create(user.email)
            
            return None
        except User.DoesNotExist:
            return None

    def logout(self):
        sessions = Session.objects.filter(userId=self.email)
        for session in sessions:
            session.invalidate()

    def deleteAccount(self):
        try:
            user_email = self.email
            
            Session.objects.filter(userId=user_email).delete()
            EmailVerificationToken.objects.filter(userId=user_email).delete()
            
            self.delete()
            
            return True
        except Exception:
            return False

    def submitReport(self, targetType, targetId, reason):
        return None  # RED


class Student(User):
    def takeDiagnosticTest(self):
        return None

    def viewRecommendations(self):
        return []

    def browseMaterials(self, filters):
        return []

    def viewMaterial(self, materialId):
        return None

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
        return ReportGenerator().buildPdf(self.id, "all")

    def applyForModerator(self):
        return None

    def rateModerator(self, workId, score, comment):
        pass


class Moderator(User):
    def viewMaterialsToVerify(self):
        return []

    def verifyMaterial(self, materialId, decision, comment):
        return None

    def editMaterialTests(self, materialId, newQuestions):
        return False

    def viewWorksToCheck(self):
        return []

    def reserveWork(self, workId):
        return False

    def checkWork(self, workId, reviewData):
        return None

    def viewModeratorStats(self):
        pass


class Admin(User):
    def viewSystemStats(self):
        return {}

    def reviewModeratorApplications(self):
        return []

    def acceptCandidate(self, applicationId):
        return False

    def rejectCandidate(self, applicationId, reason):
        return False

    def handleUserReports(self):
        return []

    def reviewReport(self, reportId, decision):
        return False

    def manageUserAccount(self, userId, newStatus, newRole):
        pass


class Session(models.Model):
    userId = models.CharField(max_length=255)
    token = models.CharField(max_length=255)
    expiresAt = models.DateTimeField(null=True)

    @classmethod
    def create(cls, userId):
        new_token = str(uuid.uuid4())
        expiry = timezone.now() + timedelta(days=1)

        return cls.objects.create(
            userId=userId, 
            token=new_token, 
            expiresAt=expiry
        )

    def invalidate(self):
        self.delete()


class EmailVerificationToken(models.Model):
    userId = models.CharField(max_length=255)
    token = models.CharField(default=random.randint(100000, 999999))
    expiresAt = models.DateTimeField(default=timezone.now() + timedelta(days=1))

    def verify(self):
        if self.expiresAt and timezone.now() > self.expiresAt:
            return False
        return True 


class FileAttachment(models.Model):
    fileName = models.CharField(max_length=255)
    filePath = models.CharField(max_length=255)
    fileType = models.CharField(max_length=50)
    sizeBytes = models.BigIntegerField(default=0)
    uploadedAt = models.DateTimeField(auto_now_add=True)

    material = models.ForeignKey(
        'Material', 
        on_delete=models.CASCADE, 
        null=True, 
        related_name='attachments'
    )

    def upload(self, fileStream):
        try:
            self.fileName = fileStream.name
            self.sizeBytes = fileStream.size
            self.fileType = fileStream.content_type

            folder = 'uploads/'
            name = default_storage.save(os.path.join(folder, self.fileName), fileStream)

            self.filePath = name
            self.save()
            return True
        except Exception as e:
            print(f"Błąd podczas uploadu: {e}")
            return False

class Material(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    authorId = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    priority = models.IntegerField(default=0)
    isVerified = models.BooleanField(default=False)

    @classmethod
    def create(cls, data, files):
        material = cls.objects.create(
            title=data.get('title'),
            content=data.get('content'),
            authorId=data.get('authorId'),
            status="PENDING", 
            priority=0,
            isVerified=False
        )

        if files:
            for f in files:
                attachment = FileAttachment()
                if attachment.upload(f):
                    material.attachments.add(attachment)

        return material

    def addTest(self, test):
        return False

    def addFile(self, file_attachment):
       try:
            file_attachment.material = self
            file_attachment.save()
            return True
       except Exception:
            return False

    def increasePriority(self):
        pass

    def getDetails(self):
        return None





class Test(models.Model):
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=50)
    materialId = models.CharField(max_length=255)

    def addQuestion(self, question):
        return False

    def calculateScore(self, answers):
        return 0.0


class DiagnosticTest(Test):
    def calculateAreaScores(self, answers):
        return {}


class Question(models.Model):
    text = models.TextField()
    qType = models.CharField(max_length=50)
    correctAnswer = models.CharField(max_length=255)
    points = models.IntegerField(default=1)


class TestResult(models.Model):
    testId = models.CharField(max_length=255)
    userId = models.CharField(max_length=255)
    score = models.FloatField(default=0.0)
    completedAt = models.DateTimeField(auto_now_add=True)


class DiagnosticResult(TestResult):
    areaScores = models.JSONField(default=dict)

    def getWeakAreas(self):
        return []


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

    def send(self):
        pass

    def markAsRead(self):
        pass


class Work(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    studentId = models.CharField(max_length=255)
    packageId = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    assignedModeratorId = models.CharField(max_length=255, null=True)

    @classmethod
    def submit(cls, files, packageId):
        return None

    def assignModerator(self, moderatorId):
        return False


class Package(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField(default=0.0)
    scope = models.CharField(max_length=255)

    def select(self):
        return None


class PaymentTransaction(models.Model):
    workId = models.CharField(max_length=255)
    userId = models.CharField(max_length=255)
    amount = models.FloatField(default=0.0)
    status = models.CharField(max_length=50)
    method = models.CharField(max_length=50)

    def process(self):
        return False


class WorkReview(models.Model):
    workId = models.CharField(max_length=255)
    moderatorId = models.CharField(max_length=255)
    grade = models.CharField(max_length=50)
    generalComment = models.TextField()
    status = models.CharField(max_length=50)

    def addErrorMark(self, mark):
        return None

    def addComment(self, comment):
        return None

    def publish(self):
        return False


class ErrorMark(models.Model):
    reviewId = models.CharField(max_length=255)
    textSnippet = models.TextField()
    type = models.CharField(max_length=50)
    positionInText = models.CharField(max_length=255)


class MaterialVerification(models.Model):
    materialId = models.CharField(max_length=255)
    moderatorId = models.CharField(max_length=255)
    decision = models.CharField(max_length=50)

    def submit(self, decision, comment):
        return False


class ModeratorApplication(models.Model):
    candidateId = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    testResultId = models.CharField(max_length=255)

    def submit(self):
        return False

    def evaluate(self):
        return False


class Report(models.Model):
    reporterId = models.CharField(max_length=255)
    targetType = models.CharField(max_length=50)
    targetId = models.CharField(max_length=255)
    reason = models.TextField()
    status = models.CharField(max_length=50, default="PENDING")

    def submit(self):
        return False

    def review(self, decision):
        return False

class Statistics(models.Model):
    pass
