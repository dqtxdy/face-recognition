import base64
import io
import tempfile
import unittest
import asyncio
from pathlib import Path

import httpx
from PIL import Image

from trustfacechain.api import create_app


class ApiTest(unittest.TestCase):
    def _app_and_tmp(self, *, api_key: str | None = None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return create_app(
            db_path=Path(tmp.name) / "api.db",
            key_path=Path(tmp.name) / "fernet.key",
            api_key=api_key,
        )

    def test_health(self):
        async def run():
            async with self._client() as client:
                response = await client.get("/health")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["status"], "ok")

        asyncio.run(run())

    def test_enroll_verify_revoke_api_flow(self):
        async def run():
            async with self._client() as client:
                enroll = await client.post(
                    "/v1/enroll",
                    json={
                        "subject_id": "subject-a",
                        "biometric_input": "alice face",
                        "model_version": "demo-hash-v1",
                        "consent": {"purpose": "unit test"},
                    },
                )
                self.assertEqual(enroll.status_code, 200)
                self.assertIn("templateCommitment", enroll.json())

                verify = await client.post(
                    "/v1/verify",
                    json={
                        "subject_id": "subject-a",
                        "biometric_input": "alice face",
                        "threshold": 0.5,
                    },
                )
                self.assertEqual(verify.status_code, 200)
                self.assertTrue(verify.json()["accepted"])

                metrics = await client.get("/v1/metrics")
                self.assertEqual(metrics.status_code, 200)
                self.assertEqual(metrics.json()["identities"], 1)

                revoke = await client.post(
                    "/v1/revoke",
                    json={
                        "subject_id": "subject-a",
                        "reason": "test",
                    },
                )
                self.assertEqual(revoke.status_code, 200)

                blocked = await client.post(
                    "/v1/verify",
                    json={
                        "subject_id": "subject-a",
                        "biometric_input": "alice face",
                        "threshold": 0.5,
                    },
                )
                self.assertEqual(blocked.status_code, 423)

        asyncio.run(run())

    def test_image_enroll_verify_api_flow(self):
        async def run():
            image_payload = _tiny_png_base64()
            async with self._client() as client:
                enroll = await client.post(
                    "/v1/enroll",
                    json={
                        "subject_id": "subject-image",
                        "image_base64": image_payload,
                        "model_version": "demo-image-hash-v1",
                        "consent": {"purpose": "image unit test"},
                    },
                )
                self.assertEqual(enroll.status_code, 200)
                self.assertEqual(enroll.json()["modelVersion"], "demo-image-hash-v1")

                verify = await client.post(
                    "/v1/verify",
                    json={
                        "subject_id": "subject-image",
                        "image_base64": image_payload,
                        "threshold": 0.5,
                    },
                )
                self.assertEqual(verify.status_code, 200)
                self.assertTrue(verify.json()["accepted"])

        asyncio.run(run())

    def test_rejects_ambiguous_biometric_payload_api(self):
        async def run():
            async with self._client() as client:
                response = await client.post(
                    "/v1/enroll",
                    json={
                        "subject_id": "subject-a",
                        "biometric_input": "alice face",
                        "image_base64": _tiny_png_base64(),
                        "model_version": "demo-image-hash-v1",
                    },
                )
                self.assertEqual(response.status_code, 422)

        asyncio.run(run())

    def test_optional_api_key_auth(self):
        async def run():
            app = self._app_and_tmp(api_key="secret-key")
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                health = await client.get("/health")
                self.assertEqual(health.status_code, 200)

                blocked = await client.get("/v1/metrics")
                self.assertEqual(blocked.status_code, 401)

                allowed = await client.get(
                    "/v1/metrics",
                    headers={"X-TrustFace-Key": "secret-key"},
                )
                self.assertEqual(allowed.status_code, 200)

        asyncio.run(run())

    def _client(self):
        app = self._app_and_tmp()
        transport = httpx.ASGITransport(app=app)
        return httpx.AsyncClient(transport=transport, base_url="http://test")


def _tiny_png_base64() -> str:
    image = Image.new("RGB", (16, 16), color=(120, 80, 40))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


if __name__ == "__main__":
    unittest.main()
