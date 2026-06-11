import base64
import io
import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet
from PIL import Image

from trustfacechain.product_service import (
    IdentityAlreadyActive,
    IdentityRevoked,
    InvalidBiometricInput,
    TrustFaceProductService,
)
from trustfacechain.store import ProductStore


class ProductServiceTest(unittest.TestCase):
    def _service(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return TrustFaceProductService(
            store=ProductStore(Path(tmp.name) / "api.db"),
            fernet=Fernet(Fernet.generate_key()),
        )

    def test_enroll_verify_revoke(self):
        service = self._service()
        enrollment = service.enroll(
            subject_id="subject-a",
            biometric_input="alice face",
            model_version="demo-hash-v1",
            consent={"purpose": "unit test"},
        )
        self.assertEqual(enrollment.subject_id, "subject-a")

        accepted = service.verify(
            subject_id="subject-a",
            biometric_input="alice face",
            threshold=0.5,
        )
        self.assertTrue(accepted.accepted)

        service.revoke(subject_id="subject-a", reason="test revocation")
        with self.assertRaises(IdentityRevoked):
            service.verify(
                subject_id="subject-a",
                biometric_input="alice face",
                threshold=0.5,
            )

    def test_duplicate_active_enrollment_rejected(self):
        service = self._service()
        kwargs = {
            "subject_id": "subject-a",
            "biometric_input": "alice face",
            "model_version": "demo-hash-v1",
            "consent": {"purpose": "unit test"},
        }
        service.enroll(**kwargs)
        with self.assertRaises(IdentityAlreadyActive):
            service.enroll(**kwargs)

    def test_image_enroll_verify_does_not_store_raw_image(self):
        service = self._service()
        image_payload = _tiny_png_base64()
        enrollment = service.enroll(
            subject_id="subject-image",
            image_base64=image_payload,
            model_version="demo-image-hash-v1",
            consent={"purpose": "unit test"},
        )
        self.assertEqual(enrollment.model_version, "demo-image-hash-v1")

        accepted = service.verify(
            subject_id="subject-image",
            image_base64=image_payload,
            threshold=0.5,
        )
        self.assertTrue(accepted.accepted)

        identity = service.get_identity("subject-image")
        self.assertIsNotNone(identity)
        self.assertNotIn(image_payload.encode("utf-8"), identity.encrypted_embedding)

    def test_rejects_ambiguous_biometric_payload(self):
        service = self._service()
        with self.assertRaises(InvalidBiometricInput):
            service.enroll(
                subject_id="subject-a",
                biometric_input="alice face",
                image_base64=_tiny_png_base64(),
                model_version="demo-image-hash-v1",
                consent={"purpose": "unit test"},
            )


def _tiny_png_base64() -> str:
    image = Image.new("RGB", (16, 16), color=(120, 80, 40))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


if __name__ == "__main__":
    unittest.main()
