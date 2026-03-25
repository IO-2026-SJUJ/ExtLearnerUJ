classDiagram
    class User {
        -Int id
        -String email
        -String password
        -String name
        -Date registrationDate
        -UserStatus status 
        -bool emailVerified
        +register(email, password, name) boolean
        +verifyEmail(id) boolean
        +login(email, password) Session
        +logout()
        +deleteAccount() boolean
        +submitReport(targetType, targetId, reason) Report
    }
    class Student {
        +takeDiagnosticTest() TestResult
        +viewRecommendations() List~Material~
        +browseMaterials(filters) List~Material~
        +viewMaterial(materialId) Material
        +addToFavorites(materialId) Favorite
        +voteMaterial(materialId) Vote
        +submitWork(workData, packageId, files) Work
        +viewStats()
        +downloadLearningReport() File
        +applyForModerator() ModeratorApplication
        +rateModerator(workId, score, comment)
    }

     class Moderator {
        +viewMaterialsToVerify() List~Material~
        +verifyMaterial(materialId, decision, comment) MaterialVerification
        +editMaterialTests(materialId, newQuestions) boolean
        +viewWorksToCheck() List~Work~
        +reserveWork(workId) boolean
        +checkWork(workId, reviewData) WorkReview
        +viewModeratorStats()
    }

    class Admin {
        +viewSystemStats() Map
        +reviewModeratorApplications() List~ModeratorApplication~
        +acceptCandidate(applicationId) boolean
        +rejectCandidate(applicationId, reason) boolean
        +handleUserReports() List~Report~
        +reviewReport(reportId, decision) boolean
        +manageUserAccount(userId, newStatus, newRole)
    }

    User <|-- Student
    User <|-- Moderator
    User <|-- Admin

    class Session {
        -String id
        -String userId
        -String token
        -DateTime expiresAt
        +create(userId) Session
        +invalidate()
    }
    User "1" -- "0..*" Session : has_active_session

    class EmailVerificationToken {
        -String token
        -String userId
        -DateTime expiresAt
        +verify() boolean
    }
    User "1" -- "0..*" EmailVerificationToken : owns

    class Material {
        -String id
        -String title
        -String content
        -String authorId
        -VerificationStatus status
        -int priority
        -bool isVerified
        +create(data, files) Material
        +addTest(test) boolean
        +addFile(file) FileAttachment
        +increasePriority()
        +getDetails() Material
    }
    Student "1" -- "0..*" Material : authors
    Material "1" -- "0..*" FileAttachment : contains_files

    class FileAttachment {
        -String id
        -String fileName
        -String filePath
        -String fileType
        -long sizeBytes
        -Date uploadedAt
        +upload(fileStream) boolean
    }

    class Test {
        -String id
        -String title
        -TestType type
        -String materialId
        +addQuestion(question) boolean
        +calculateScore(answers) float
    }
    Material "1" -- "0..*" Test : has_checking_test
    Test "1" -- "0..*" Question : contains_questions
    Test "1" -- "0..*" TestResult : produces_results

    class DiagnosticTest {
        -List~Area~ areas
        +calculateAreaScores(answers) Map~String,float~
    }
    Test <|-- DiagnosticTest

    class MaterialTest {
    }
    Test <|-- MaterialTest

    class ModeratorTest {
    }
    Test <|-- ModeratorTest

    class Question {
        -String id
        -String text
        -QuestionType qType
        -List~String~ options
        -String correctAnswer
        -int points
    }

    class TestResult {
        -String id
        -String testId
        -String userId
        -float score
        -Map answers
        -DateTime completedAt
        +save()
    }

    Student "1" -- "0..*" TestResult : achieves

    class DiagnosticResult {
        -Map~String,float~ areaScores % wyniki per obszar (UC05)
        +getWeakAreas() List~String~
    }
    TestResult <|-- DiagnosticResult

    class Favorite {
        -String userId
        -String materialId
        -DateTime addedAt
    }
    Student "1" -- "0..*" Favorite : favorites_list
    Material "1" -- "0..*" Favorite : favorited_by_users

    class Vote {
        -String userId
        -String materialId
        -DateTime votedAt
    }
    Student "1" -- "0..*" Vote : casts_votes
    Material "1" -- "0..*" Vote : voted_by_users

    class GradingService {
        +autoGradeDiagnostic(testId, answers) DiagnosticResult
        +autoGradeMaterialTest(testId, answers) TestResult
    }
    TestResult -- GradingService : generated_by

    class RecommendationService {
        +getRecommendationsForUser(userId) List~Material~
    }
    Student -- RecommendationService : requests_recommendations
    Material -- RecommendationService : used_as_recommendation

    class StatisticsService {
        +updateUserStats(testResult)
        +getUserStatistics(userId) Map
        +getModeratorStats(moderatorId) Map
        +getSystemStats() Map
        +generateLearningReport(userId, period) File
    }
    Student -- StatisticsService : views_stats / downloads_report
    Moderator -- StatisticsService : views_own_stats
    Admin -- StatisticsService : views_system_stats
    TestResult -- StatisticsService : triggers_update

    class RankingService {
        +getStudentRanking() List~Student~
    }
    Student -- RankingService : checks_ranking

    class ReportGenerator {
        +buildPdf(userId, period) File
    }
    Student -- ReportGenerator : uses_to_download_report

    class Notification {
        -String id
        -String userId
        -String message
        -bool isRead
        +send()
        +markAsRead()
    }
    User "1" -- "0..*" Notification : receives

    class Work {
        -String id
        -String title
        -String description
        -String studentId
        -String packageId
        -WorkStatus status
        -String assignedModeratorId
        -DateTime submittedAt
        +submit(files, packageId) Work
        +assignModerator(moderatorId) boolean
    }
    Student "1" -- "0..*" Work : submits
    Work "1" -- "1" Package : selects_package
    Work "1" -- "0..*" FileAttachment : includes_submitted_files

    class Package {
        -String id
        -String name
        -float price
        -String scope              % zakres sprawdzenia
        +select() Package
    }

    class PaymentTransaction {
        -String id
        -String workId
        -String userId
        -float amount
        -PaymentStatus status
        -String method
        +process() boolean
    }
    Work "1" -- "1" PaymentTransaction : has_payment
    Student ..> PaymentTransaction : initiates_payment

    class WorkReview {
        -String id
        -String workId
        -String moderatorId
        -String grade
        -String generalComment
        -ReviewStatus status
        +addErrorMark(mark) ErrorMark
        +addComment(comment) String
        +publish() boolean
    }
    Work "1" -- "0..*" WorkReview : has_review
    Moderator "1" -- "0..*" WorkReview : authors

    class ErrorMark {
        -String id
        -String reviewId
        -String textSnippet
        -ErrorType type
        -String positionInText
    }
    WorkReview "1" -- "0..*" ErrorMark : contains_errors

    class MaterialVerification {
        -String id
        -String materialId
        -String moderatorId
        -VerificationDecision decision
        -DateTime verifiedAt
        +submit(decision, comment) boolean
    }
    Material "1" -- "1" MaterialVerification : undergoes_verification
    Moderator "1" -- "0..*" MaterialVerification : performs

    class ModeratorApplication {
        -String id
        -String candidateId
        -ApplicationStatus status
        -String formData
        -String testResultId
        +submit() boolean
        +evaluate() boolean
    }
    Student "1" -- "0..*" ModeratorApplication : applies_as_candidate
    ModeratorApplication "1" -- "1" TestResult : includes_qualification_test
    ModeratorApplication "1" -- "0..*" FileAttachment : attachments

    class Report {
        -String id
        -String reporterId
        -ReportTargetType targetType
        -String targetId
        -String reason
        -ReportStatus status
        +submit() boolean
        +review(decision) boolean
    }
    User "1" -- "0..*" Report : submits

    class Comment {
        -String id
        -String authorId
        -String targetType
        -String targetId
        -String text
        -DateTime createdAt
    }
    MaterialVerification "1" -- "0..*" Comment : has_comments
    WorkReview "1" -- "0..*" Comment : has_comments 
