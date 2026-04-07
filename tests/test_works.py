from django.test import TestCase
from unittest.mock import patch

class TestWorksAndApplications(TestCase):

    @patch('ExtLearnerUJ.models.Work.save')
    def test_work_submit(self, mock_save):
        from ExtLearnerUJ.models import Work
        work = Work.submit(["file.txt"], "pkg_1")
        self.assertEqual(work.packageId, "pkg_1")

    @patch('ExtLearnerUJ.models.Work.save')
    def test_work_assignModerator(self, mock_save):
        from ExtLearnerUJ.models import Work
        work = Work(id="w_1", status="PENDING")
        result = work.assignModerator("mod_1")
        self.assertTrue(result)
        self.assertEqual(work.assignedModeratorId, "mod_1")

    def test_package_select(self):
        from ExtLearnerUJ.models import Package
        pkg = Package(id="pkg_1", name="Premium")
        selected = pkg.select()
        self.assertEqual(selected.id, "pkg_1")

    @patch('ExtLearnerUJ.services.PaymentGateway.charge')
    def test_paymentTransaction_process(self, mock_charge):
        mock_charge.return_value = True
        from ExtLearnerUJ.models import PaymentTransaction
        pt = PaymentTransaction(amount=50.0)
        result = pt.process()
        self.assertTrue(result)

    @patch('ExtLearnerUJ.models.ErrorMark.save')
    def test_workReview_addErrorMark(self, mock_save):
        from ExtLearnerUJ.models import WorkReview, ErrorMark
        review = WorkReview(id="rev_1")
        mark = ErrorMark(textSnippet="bad grammar")
        result = review.addErrorMark(mark)
        self.assertEqual(result.textSnippet, "bad grammar")

    @patch('ExtLearnerUJ.models.WorkReview.save')
    def test_workReview_addComment(self, mock_save):
        from ExtLearnerUJ.models import WorkReview
        review = WorkReview(id="rev_1")
        result = review.addComment("Need more details.")
        self.assertEqual(result, "Need more details.")

    @patch('ExtLearnerUJ.models.WorkReview.save')
    def test_workReview_publish(self, mock_save):
        from ExtLearnerUJ.models import WorkReview
        review = WorkReview(id="rev_1", status="DRAFT")
        result = review.publish()
        self.assertTrue(result)
        self.assertEqual(review.status, "PUBLISHED")

    @patch('ExtLearnerUJ.models.MaterialVerification.save')
    def test_materialVerification_submit(self, mock_save):
        from ExtLearnerUJ.models import MaterialVerification
        mv = MaterialVerification(id="mv_1")
        result = mv.submit("ACCEPTED", "Looks perfect")
        self.assertTrue(result)

    @patch('ExtLearnerUJ.models.ModeratorApplication.save')
    def test_moderatorApplication_submit(self, mock_save):
        from ExtLearnerUJ.models import ModeratorApplication
        app = ModeratorApplication(candidateId="user_1")
        result = app.submit()
        self.assertTrue(result)

    @patch('ExtLearnerUJ.models.ModeratorApplication.save')
    def test_moderatorApplication_evaluate(self, mock_save):
        from ExtLearnerUJ.models import ModeratorApplication
        app = ModeratorApplication(id="app_1", status="PENDING")
        result = app.evaluate()
        self.assertTrue(result)

    @patch('ExtLearnerUJ.models.Report.save')
    def test_report_submit(self, mock_save):
        from ExtLearnerUJ.models import Report
        rep = Report(targetId="user_2")
        result = rep.submit()
        self.assertTrue(result)

    @patch('ExtLearnerUJ.models.Report.save')
    def test_report_review(self, mock_save):
        from ExtLearnerUJ.models import Report
        rep = Report(id="rep_1", status="PENDING")
        result = rep.review("RESOLVED")
        self.assertTrue(result)
        self.assertEqual(rep.status, "RESOLVED")
