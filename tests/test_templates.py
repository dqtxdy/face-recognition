import unittest

from trustfacechain.templates import TemplateProtector


class TemplateProtectorTest(unittest.TestCase):
    def test_same_salt_is_deterministic(self):
        protector = TemplateProtector(app_salt=b"capstone")
        left = protector.protect(
            subject_id="subject-a",
            model_version="arcface-r100-v1",
            embedding=[0.1, -0.2, 0.3],
            template_salt="fixed",
        )
        right = protector.protect(
            subject_id="subject-a",
            model_version="arcface-r100-v1",
            embedding=[0.1, -0.2, 0.3],
            template_salt="fixed",
        )
        self.assertEqual(left.commitment, right.commitment)

    def test_different_salt_changes_commitment(self):
        protector = TemplateProtector(app_salt=b"capstone")
        left = protector.protect(
            subject_id="subject-a",
            model_version="arcface-r100-v1",
            embedding=[0.1, -0.2, 0.3],
            template_salt="one",
        )
        right = protector.protect(
            subject_id="subject-a",
            model_version="arcface-r100-v1",
            embedding=[0.1, -0.2, 0.3],
            template_salt="two",
        )
        self.assertNotEqual(left.commitment, right.commitment)


if __name__ == "__main__":
    unittest.main()

