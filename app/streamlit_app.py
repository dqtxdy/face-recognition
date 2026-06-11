from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from trustfacechain.benchmark import benchmark_dataset, write_report_json, write_summary_csv
from trustfacechain.chain_sim import Revoked, TrustFaceChainSimulator
from trustfacechain.crypto import canonical_json_hash, sha256_hex
from trustfacechain.datasets import make_synthetic_face_dataset
from trustfacechain.models.classical import DctEmbedder, EigenfacesEmbedder, LbpHistogramEmbedder, PixelEmbedder
from trustfacechain.models.hash_embedder import DeterministicHashEmbedder
from trustfacechain.templates import TemplateProtector


st.set_page_config(
    page_title="TrustFaceChain",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_state() -> None:
    if "chain" not in st.session_state:
        st.session_state.chain = TrustFaceChainSimulator()
    if "subject_id" not in st.session_state:
        st.session_state.subject_id = "subject-demo-001"
    if "template" not in st.session_state:
        st.session_state.template = None
    if "reference_embedding" not in st.session_state:
        st.session_state.reference_embedding = None


def render_status() -> None:
    template = st.session_state.template
    revoked = st.session_state.chain.is_revoked(st.session_state.subject_id)
    cols = st.columns(4)
    cols[0].metric("Subject", st.session_state.subject_id)
    cols[1].metric("Template", "Committed" if template else "None")
    cols[2].metric("Revoked", "Yes" if revoked else "No")
    cols[3].metric("Audit events", len(st.session_state.chain.events))


def enroll_identity(model_version: str, enrollment_phrase: str) -> None:
    subject_id = st.session_state.subject_id
    embedder = DeterministicHashEmbedder(name=model_version, embedding_dim=128)
    reference_embedding = embedder.embed(enrollment_phrase.encode("utf-8"))
    protector = TemplateProtector(app_salt=b"trustfacechain-demo")
    template = protector.protect(
        subject_id=subject_id,
        model_version=model_version,
        embedding=reference_embedding,
    )
    consent = {
        "subjectId": subject_id,
        "purpose": "Face verification capstone demo",
        "scope": ["enrollment", "verification", "audit"],
        "modelVersion": model_version,
        "templateStorage": "encrypted-off-chain",
        "rawImageStorage": "none",
    }
    st.session_state.chain.enroll_identity(
        subject_id=subject_id,
        template_commitment=template.commitment,
        consent_hash=canonical_json_hash(consent),
        model_version=model_version,
    )
    st.session_state.template = template
    st.session_state.reference_embedding = reference_embedding


def verify_identity(model_version: str, probe_phrase: str, threshold: float) -> tuple[float, bool]:
    if st.session_state.reference_embedding is None:
        raise RuntimeError("Enroll an identity before verification.")
    embedder = DeterministicHashEmbedder(name=model_version, embedding_dim=128)
    probe_embedding = embedder.embed(probe_phrase.encode("utf-8"))
    score = embedder.score(st.session_state.reference_embedding, probe_embedding)
    accepted = score >= threshold
    verification_hash = sha256_hex(
        f"{st.session_state.subject_id}:{model_version}:{score:.8f}:{accepted}".encode("utf-8")
    )
    st.session_state.chain.log_verification(
        subject_id=st.session_state.subject_id,
        verification_hash=verification_hash,
        model_version=model_version,
        accepted=accepted,
    )
    return score, accepted


def run_demo_benchmark() -> pd.DataFrame:
    samples = make_synthetic_face_dataset(identities=8, samples_per_identity=4, seed=7)
    results = benchmark_dataset(
        samples,
        [PixelEmbedder(), DctEmbedder(), LbpHistogramEmbedder(), EigenfacesEmbedder()],
        pairs_per_identity=2,
        seed=7,
    )
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)
    write_summary_csv(results, report_dir / "demo_metrics.csv")
    write_report_json(results, report_dir / "demo_report.json")
    return pd.DataFrame([result.summary() for result in results])


init_state()

st.sidebar.title("TrustFaceChain")
st.sidebar.caption("Privacy-preserving biometric verification")
selected_model = st.sidebar.selectbox(
    "Model version",
    ["arcface-r100-v1", "facenet-vggface2-v1", "mobilefacenet-v1"],
)
threshold = st.sidebar.slider("Decision threshold", -0.25, 1.0, 0.62, 0.01)

st.title("TrustFaceChain")
st.caption("Face matching stays off-chain. Consent, commitments, audit, and revocation are accountable.")
render_status()

tabs = st.tabs(["Enroll", "Verify", "Audit", "Evaluation", "Privacy"])

with tabs[0]:
    st.subheader("Enroll identity")
    st.write("The demo stores only a protected-template commitment in the local chain simulator.")
    enrollment_phrase = st.text_input(
        "Enrollment input",
        value="alice enrollment",
        help="Temporary stand-in for a captured face embedding until real camera/model integration lands.",
    )
    if st.button("Enroll identity", type="primary"):
        try:
            enroll_identity(selected_model, enrollment_phrase)
            st.success("Identity enrolled and commitment logged.")
        except Exception as error:
            st.error(str(error))

    if st.session_state.template:
        st.code(json.dumps(st.session_state.template.to_public_record(), indent=2), language="json")

with tabs[1]:
    st.subheader("Verify face")
    probe_phrase = st.text_input("Probe input", value="alice enrollment")
    if st.button("Run verification", type="primary"):
        try:
            score, accepted = verify_identity(selected_model, probe_phrase, threshold)
            st.metric("Similarity score", f"{score:.4f}")
            if accepted:
                st.success("Accepted. Verification event logged.")
            else:
                st.warning("Rejected. Verification event logged.")
        except Revoked:
            st.error("Template is revoked. Verification blocked.")
        except Exception as error:
            st.error(str(error))

    if st.button("Revoke template"):
        reason_hash = sha256_hex(b"demo revocation")
        try:
            st.session_state.chain.revoke_template(
                subject_id=st.session_state.subject_id,
                reason_hash=reason_hash,
            )
            st.warning("Template revoked. Future verification is blocked.")
        except Exception as error:
            st.error(str(error))

with tabs[2]:
    st.subheader("Audit trail")
    rows = [
        {
            "event": event.event_type,
            "subject": event.subject_id,
            "timestamp": event.timestamp,
            **event.payload,
        }
        for event in st.session_state.chain.events
    ]
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No audit events yet.")

with tabs[3]:
    st.subheader("Evaluation")
    metrics_path = Path("reports/demo_metrics.csv")
    deep_metrics_path = Path("reports/lfw_deep_smoke_metrics.csv")
    robustness_path = Path("reports/robustness_demo.csv")
    if st.button("Run local benchmark"):
        frame = run_demo_benchmark()
        st.success("Benchmark complete.")
        st.dataframe(frame, use_container_width=True, hide_index=True)
    elif metrics_path.exists():
        st.dataframe(pd.read_csv(metrics_path), use_container_width=True, hide_index=True)
    else:
        st.info("Run the local benchmark to populate metrics.")

    st.divider()
    st.subheader("Deep model smoke")
    if deep_metrics_path.exists():
        st.dataframe(pd.read_csv(deep_metrics_path), use_container_width=True, hide_index=True)
    else:
        st.info("Run `make deep-smoke` after installing optional InsightFace dependencies.")

    st.divider()
    st.subheader("Robustness report")
    if robustness_path.exists():
        robustness = pd.read_csv(robustness_path)
        st.dataframe(
            robustness[["corruption", "level", "model", "accuracy", "eer", "embed_seconds"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Run `make robustness-demo` to populate corruption sensitivity metrics.")

with tabs[4]:
    st.subheader("Privacy posture")
    st.markdown(
        """
        - Raw face images are not written to the chain.
        - Plain embeddings are not written to the chain.
        - Consent is represented by a hash.
        - Verification events include model version accountability.
        - Revocation blocks future verification.
        """
    )
