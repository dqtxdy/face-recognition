import unittest

from trustfacechain.datasets import make_pairs, make_synthetic_face_dataset


class DatasetTest(unittest.TestCase):
    def test_make_synthetic_face_dataset(self):
        samples = make_synthetic_face_dataset(identities=3, samples_per_identity=2)
        self.assertEqual(len(samples), 6)
        self.assertEqual(samples[0].image.shape, (112, 112))

    def test_make_pairs_has_genuine_and_impostor(self):
        samples = make_synthetic_face_dataset(identities=3, samples_per_identity=3)
        pairs = make_pairs(samples, pairs_per_identity=1, seed=3)
        labels = {pair.label for pair in pairs}
        self.assertEqual(labels, {0, 1})


if __name__ == "__main__":
    unittest.main()

