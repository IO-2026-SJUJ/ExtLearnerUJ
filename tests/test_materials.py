from django.test import TestCase
from unittest.mock import patch

class TestMaterialsAndGrading(TestCase):

    @patch('ExtLearnerUJ.models.Material.save')
    def test_material_create(self, mock_save):
        from ExtLearnerUJ.models import Material
        f1 = Material.create({"title": "Family"}, ["file1.pdf"])
        self.assertEqual(f1.title, "Family")

    @patch('ExtLearnerUJ.models.Test.save')
    def test_material_addTest(self, mock_save):
        from ExtLearnerUJ.models import Material, Test
        m1 = Material(id="m_1")
        test = Test(id="test_1")
        result = m1.addTest(test)
        self.assertTrue(result)

    @patch('ExtLearnerUJ.models.FileAttachment.upload')
    def test_material_addFile(self, mock_upload):
        from ExtLearnerUJ.models import Material, FileAttachment
        mock_upload.return_value = True
        m1 = Material(id="m_1")
        file = FileAttachment(id="f_1")
        result = m1.addFile(file)
        self.assertIsNotNone(result)

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

    @patch('ExtLearnerUJ.models.FileAttachment.save')
    def test_fileAttachment_upload(self, mock_save):
        from ExtLearnerUJ.models import FileAttachment
        file = FileAttachment()
        result = file.upload("Passive voice")
        self.assertTrue(result)

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
