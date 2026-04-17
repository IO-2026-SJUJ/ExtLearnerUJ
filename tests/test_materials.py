import shutil
import tempfile
from django.test import TestCase, override_settings
from django.conf import settings
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from ExtLearnerUJ.models import Material, FileAttachment

MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TestMaterialsAndGrading(TestCase):

    def setUp(self):
        self.valid_data = {
            'title': 'Wzorce Projektowe',
            'content': 'Opis wzorca Fabryka i Singleton.',
            'authorId': 'student123@uj.edu.pl'
        }
        self.fake_file_content = b"To jest testowa zawartosc pliku."
        self.fake_file = SimpleUploadedFile(
            "notatki.pdf", 
            self.fake_file_content, 
            content_type="application/pdf"
        )

    def test_fileAttachment_upload(self):
        """Sprawdza, czy plik jest poprawnie zapisywany na dysku i w bazie."""
        attachment = FileAttachment()
        
        result = attachment.upload(self.fake_file)
        
        self.assertTrue(result, "Upload powinien zwrocic True")
        self.assertEqual(attachment.fileName, "notatki.pdf")
        self.assertGreater(attachment.sizeBytes, 0)
        self.assertTrue(default_storage.exists(attachment.filePath), "Plik powinien istniec w storage")
        
        if default_storage.exists(attachment.filePath):
            default_storage.delete(attachment.filePath)

    def test_material_addFile(self):
        material = Material.objects.create(title="Test Material", authorId="admin")
        attachment = FileAttachment.objects.create(
            fileName="doc.txt", 
            filePath="path/doc.txt"
        )
        
        result = material.addFile(attachment)
        
        self.assertTrue(result)
        attachment.refresh_from_db()
        self.assertEqual(attachment.material, material, "Zalacznik powinien miec przypisany material")
        self.assertIn(attachment, material.attachments.all(), "Material powinien widziec zalacznik w zbiorze")

        files_list = [self.fake_file]
        
        material = Material.create(self.valid_data, files_list)
        
        self.assertIsNotNone(material.id)
        self.assertEqual(material.title, self.valid_data['title'])
        self.assertEqual(material.status, "PENDING")
        
        attachments = material.attachments.all()
        self.assertEqual(attachments.count(), 1)
        self.assertEqual(attachments[0].fileName, "notatki.pdf")
        
        for att in attachments:
            default_storage.delete(att.filePath)

    @patch('ExtLearnerUJ.models.Test.save')
    def test_material_addTest(self, mock_save):
        from ExtLearnerUJ.models import Material, Test
        m1 = Material(id="m_1")
        test = Test(id="test_1")
        result = m1.addTest(test)
        self.assertTrue(result)

    def test_material_increasePriority(self):
        from ExtLearnerUJ.models import Material
        m1 = Material(id="m_1", priority=0)
        m1.increasePriority()
        self.assertEqual(m1.priority, 1)

    def test_material_getDetails(self):
        from ExtLearnerUJ.models import Material
        m1 = Material(id="m_1", title="Title")
        details = m1.getDetails()
        self.assertEqual(details.title, "Title")

    def test_test_addQuestion(self):
        from ExtLearnerUJ.models import Test, Question
        t = Test(id="t_1")
        q = Question(id="q_1")
        result = t.addQuestion(q)
        self.assertTrue(result)

    def test_test_calculateScore(self):
        from ExtLearnerUJ.models import Test
        t = Test(id="t_1")
        score = t.calculateScore({"q1": "A"})
        self.assertIsInstance(score, float)

    def test_diagnosticTest_calculateAreaScores(self):
        from ExtLearnerUJ.models import DiagnosticTest
        dt = DiagnosticTest()
        scores = dt.calculateAreaScores({"q1": "A"})
        self.assertIsInstance(scores, dict)

    @patch('ExtLearnerUJ.models.TestResult.save')
    def test_testResult_save(self, mock_save):
        from ExtLearnerUJ.models import TestResult
        tr = TestResult(score=10.0)
        tr.save()
        mock_save.assert_called_once()

    def test_diagnosticResult_getWeakAreas(self):
        from ExtLearnerUJ.models import DiagnosticResult
        dr = DiagnosticResult(areaScores={"Grammar": 2.0, "Reading": 9.0})
        weak = dr.getWeakAreas()
        self.assertIn("Grammar", weak)

    @patch('ExtLearnerUJ.models.DiagnosticTest.calculateAreaScores')
    def test_gradingService_autoGradeDiagnostic(self, mock_calc):
        from ExtLearnerUJ.services import GradingService
        mock_calc.return_value = {"Grammar": 5.0}
        service = GradingService()
        result = service.autoGradeDiagnostic("test_1", {"q1": "A"})
        self.assertIsNotNone(result)

    @patch('ExtLearnerUJ.models.Test.calculateScore')
    def test_gradingService_autoGradeMaterialTest(self, mock_calc):
        from ExtLearnerUJ.services import GradingService
        mock_calc.return_value = 10.0
        service = GradingService()
        result = service.autoGradeMaterialTest("test_2", {"q1": "B"})
        self.assertIsNotNone(result)

    @classmethod
    def tearDownClass(cls):
        """Wywoływane raz po zakończeniu WSZYSTKICH testów w tej klasie."""
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()