import unittest

from trustfacechain.metrics import confusion_at_threshold, evaluate_scores


class MetricsTest(unittest.TestCase):
    def test_confusion_at_threshold(self):
        result = confusion_at_threshold(
            scores=[0.9, 0.8, 0.2, 0.1],
            labels=[1, 1, 0, 0],
            threshold=0.5,
        )
        self.assertEqual(result.true_accepts, 2)
        self.assertEqual(result.true_rejects, 2)
        self.assertEqual(result.false_accepts, 0)
        self.assertEqual(result.false_rejects, 0)
        self.assertEqual(result.accuracy, 1.0)

    def test_evaluate_scores(self):
        report = evaluate_scores(
            scores=[0.95, 0.85, 0.4, 0.2],
            labels=[1, 1, 0, 0],
        )
        self.assertEqual(report.best_accuracy, 1.0)
        self.assertLessEqual(report.eer, 0.5)


if __name__ == "__main__":
    unittest.main()

