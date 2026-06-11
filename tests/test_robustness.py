import unittest

import numpy as np

from trustfacechain.robustness import apply_corruption


class RobustnessTest(unittest.TestCase):
    def test_corruptions_preserve_shape(self):
        image = np.ones((32, 32), dtype=np.float32) * 0.5
        for corruption, level in [
            ("brightness_down", 0.2),
            ("brightness_up", 0.2),
            ("gaussian_noise", 0.05),
            ("blur", 1.0),
            ("jpeg", 60),
            ("downscale", 0.5),
            ("lower_occlusion", 0.25),
        ]:
            corrupted = apply_corruption(image, corruption=corruption, level=level)
            self.assertEqual(corrupted.shape, image.shape)
            self.assertGreaterEqual(float(corrupted.min()), 0.0)
            self.assertLessEqual(float(corrupted.max()), 1.0)


if __name__ == "__main__":
    unittest.main()

