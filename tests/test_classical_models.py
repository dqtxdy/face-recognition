import unittest

from trustfacechain.benchmark import benchmark_dataset
from trustfacechain.datasets import make_synthetic_face_dataset
from trustfacechain.models.classical import DctEmbedder, EigenfacesEmbedder, LbpHistogramEmbedder, PixelEmbedder


class ClassicalModelsTest(unittest.TestCase):
    def test_benchmark_classical_models(self):
        samples = make_synthetic_face_dataset(identities=4, samples_per_identity=3)
        results = benchmark_dataset(
            samples,
            [PixelEmbedder(), DctEmbedder(), LbpHistogramEmbedder(), EigenfacesEmbedder()],
            pairs_per_identity=1,
        )
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertGreater(result.pairs, 0)
            self.assertGreaterEqual(result.report.best_accuracy, 0.0)
            self.assertLessEqual(result.report.best_accuracy, 1.0)


if __name__ == "__main__":
    unittest.main()

