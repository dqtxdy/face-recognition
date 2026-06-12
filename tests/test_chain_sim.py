import unittest

from trustfacechain.chain_sim import (
    AlreadyEnrolled,
    NotAuthorized,
    Revoked,
    TrustFaceChainSimulator,
)


class ChainSimulatorTest(unittest.TestCase):
    def test_enroll_verify_revoke_flow(self):
        chain = TrustFaceChainSimulator()
        chain.enroll_identity(
            subject_id="subject",
            template_commitment="template",
            consent_hash="consent",
            model_version="arcface",
        )
        chain.log_verification(
            subject_id="subject",
            verification_hash="verification",
            model_version="arcface",
            accepted=True,
        )
        chain.revoke_template(subject_id="subject", reason_hash="reason")

        self.assertTrue(chain.is_revoked("subject"))
        self.assertEqual([event.event_type for event in chain.events], [
            "IdentityEnrolled",
            "VerificationLogged",
            "TemplateRevoked",
        ])
        with self.assertRaises(Revoked):
            chain.log_verification(
                subject_id="subject",
                verification_hash="blocked",
                model_version="arcface",
                accepted=True,
            )

    def test_duplicate_active_enrollment_fails(self):
        chain = TrustFaceChainSimulator()
        kwargs = {
            "subject_id": "subject",
            "template_commitment": "template",
            "consent_hash": "consent",
            "model_version": "arcface",
        }
        chain.enroll_identity(**kwargs)
        with self.assertRaises(AlreadyEnrolled):
            chain.enroll_identity(**kwargs)

    def test_only_owner_can_delegate_operator(self):
        chain = TrustFaceChainSimulator(owner="root")
        with self.assertRaises(NotAuthorized):
            chain.set_operator(caller="analyst", operator="desk-1", approved=True)

        chain.set_operator(caller="root", operator="desk-1", approved=True)
        chain.enroll_identity(
            caller="desk-1",
            subject_id="subject",
            template_commitment="template",
            consent_hash="consent",
            model_version="arcface",
        )
        self.assertIn("subject", chain.identities)

    def test_unauthorized_writer_cannot_mutate_chain(self):
        chain = TrustFaceChainSimulator(owner="root")
        with self.assertRaises(NotAuthorized):
            chain.enroll_identity(
                caller="attacker",
                subject_id="subject",
                template_commitment="template",
                consent_hash="consent",
                model_version="arcface",
            )


if __name__ == "__main__":
    unittest.main()
