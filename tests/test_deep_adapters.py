import unittest

from trustfacechain.models.deep_adapters import (
    FaceNetPytorchEmbedder,
    InsightFaceArcFaceEmbedder,
    OptionalModelDependencyError,
)


class DeepAdaptersTest(unittest.TestCase):
    def test_missing_insightface_fails_helpfully(self):
        try:
            InsightFaceArcFaceEmbedder()
        except OptionalModelDependencyError as error:
            self.assertIn("insightface", str(error))

    def test_missing_facenet_fails_helpfully(self):
        try:
            FaceNetPytorchEmbedder()
        except OptionalModelDependencyError as error:
            self.assertIn("facenet-pytorch", str(error))


if __name__ == "__main__":
    unittest.main()

