"""Command line helpers for TrustFaceChain."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trustfacechain.chain_sim import Revoked, TrustFaceChainSimulator
from trustfacechain.crypto import canonical_json_hash
from trustfacechain.benchmark import (
    benchmark_dataset,
    benchmark_embedder,
    write_report_json,
    write_summary_csv,
)
from trustfacechain.datasets import (
    load_folder_dataset,
    load_lfw_official_pairs,
    load_lfw_people_dataset,
    load_pairs_csv,
    make_synthetic_face_dataset,
)
from trustfacechain.metrics import evaluate_scores
from trustfacechain.models.classical import create_embedder, default_embedders
from trustfacechain.models.hash_embedder import DeterministicHashEmbedder
from trustfacechain.robustness import evaluate_robustness, write_robustness_csv
from trustfacechain.templates import TemplateProtector


def _cmd_hash_consent(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.path).read_text(encoding="utf-8"))
    print(canonical_json_hash(payload))
    return 0


def _cmd_smoke_benchmark(_: argparse.Namespace) -> int:
    embedder = DeterministicHashEmbedder(name="smoke-hash-embedder", embedding_dim=64)
    anchors = [
        b"alice enrollment",
        b"alice enrollment",
        b"bob enrollment",
        b"carol enrollment",
    ]
    probes = [
        b"alice enrollment",
        b"alice verification",
        b"bob verification",
        b"mallory verification",
    ]
    labels = [1, 1, 1, 0]
    scores = [
        embedder.score(embedder.embed(a), embedder.embed(p))
        for a, p in zip(anchors, probes, strict=True)
    ]
    report = evaluate_scores(scores=scores, labels=labels)
    print(json.dumps(report.to_dict(), indent=2))
    return 0


def _cmd_protect_template(args: argparse.Namespace) -> int:
    vector = [float(item) for item in args.vector.split(",")]
    protector = TemplateProtector(app_salt=args.app_salt.encode("utf-8"))
    protected = protector.protect(
        subject_id=args.subject_id,
        model_version=args.model_version,
        embedding=vector,
    )
    print(json.dumps(protected.to_public_record(), indent=2))
    return 0


def _selected_embedders(model_names: str | None) -> list[object]:
    if not model_names:
        return default_embedders()
    embedders: list[object] = []
    for raw_name in model_names.split(","):
        name = raw_name.strip().lower()
        if name in {"arcface", "arcface-l", "buffalo-l", "insightface", "arcface-insightface"}:
            from trustfacechain.models.deep_adapters import InsightFaceArcFaceEmbedder

            embedders.append(InsightFaceArcFaceEmbedder(model_pack="buffalo_l"))
        elif name in {"mobileface", "mobilefacenet", "buffalo-s", "arcface-s"}:
            from trustfacechain.models.deep_adapters import InsightFaceArcFaceEmbedder

            embedders.append(InsightFaceArcFaceEmbedder(model_pack="buffalo_s"))
        elif name in {"buffalo-m", "arcface-m"}:
            raise ValueError(
                "buffalo_m is downloaded but not supported by the FaceAnalysis adapter "
                "because this pack does not expose the expected detection model."
            )
        elif name in {"facenet", "facenet-pytorch"}:
            from trustfacechain.models.deep_adapters import FaceNetPytorchEmbedder

            embedders.append(FaceNetPytorchEmbedder())
        elif name in {"siamese", "siamese-cnn"}:
            from trustfacechain.models.siamese import SiameseEmbedder

            embedders.append(SiameseEmbedder())
        else:
            embedders.append(create_embedder(name))
    return embedders


def _print_benchmark_results(results) -> None:
    print(json.dumps([result.summary() for result in results], indent=2))


def _write_benchmark_outputs(args: argparse.Namespace, results) -> None:
    if args.csv:
        write_summary_csv(results, args.csv)
    if args.json:
        write_report_json(results, args.json)


def _cmd_benchmark_demo(args: argparse.Namespace) -> int:
    samples = make_synthetic_face_dataset(
        identities=args.identities,
        samples_per_identity=args.samples_per_identity,
        seed=args.seed,
    )
    results = benchmark_dataset(
        samples,
        _selected_embedders(args.models),
        pairs_per_identity=args.pairs_per_identity,
        seed=args.seed,
    )
    _write_benchmark_outputs(args, results)
    _print_benchmark_results(results)
    return 0


def _cmd_benchmark_folder(args: argparse.Namespace) -> int:
    samples = load_folder_dataset(args.root)
    results = benchmark_dataset(
        samples,
        _selected_embedders(args.models),
        pairs_per_identity=args.pairs_per_identity,
        impostor_pairs=args.impostor_pairs,
        seed=args.seed,
    )
    _write_benchmark_outputs(args, results)
    _print_benchmark_results(results)
    return 0


def _cmd_benchmark_lfw(args: argparse.Namespace) -> int:
    samples = load_lfw_people_dataset(
        min_faces_per_person=args.min_faces_per_person,
        max_samples=args.max_samples,
        data_home=args.data_home,
    )
    results = benchmark_dataset(
        samples,
        _selected_embedders(args.models),
        pairs_per_identity=args.pairs_per_identity,
        impostor_pairs=args.impostor_pairs,
        seed=args.seed,
    )
    _write_benchmark_outputs(args, results)
    _print_benchmark_results(results)
    return 0


def _cmd_benchmark_lfw_pairs(args: argparse.Namespace) -> int:
    pairs = load_lfw_official_pairs(
        max_pairs=args.max_pairs,
        data_home=args.data_home,
        balanced_subset=not args.unbalanced,
    )
    results = [benchmark_embedder(embedder, pairs) for embedder in _selected_embedders(args.models)]
    _write_benchmark_outputs(args, results)
    _print_benchmark_results(results)
    return 0


def _cmd_benchmark_pairs_csv(args: argparse.Namespace) -> int:
    pairs = load_pairs_csv(args.csv_path)
    results = [benchmark_embedder(embedder, pairs) for embedder in _selected_embedders(args.models)]
    _write_benchmark_outputs(args, results)
    _print_benchmark_results(results)
    return 0


def _cmd_robustness_demo(args: argparse.Namespace) -> int:
    samples = make_synthetic_face_dataset(
        identities=args.identities,
        samples_per_identity=args.samples_per_identity,
        seed=args.seed,
    )
    from trustfacechain.datasets import make_pairs

    pairs = make_pairs(samples, pairs_per_identity=args.pairs_per_identity, seed=args.seed)
    results = evaluate_robustness(pairs=pairs, embedders=_selected_embedders(args.models))
    write_robustness_csv(results, args.csv)
    print(json.dumps([result.summary() for result in results], indent=2))
    return 0


def _cmd_demo_chain_flow(_: argparse.Namespace) -> int:
    chain = TrustFaceChainSimulator()
    subject_id = "subject-demo-001"
    consent_hash = canonical_json_hash(
        {
            "subjectId": subject_id,
            "purpose": "Face verification capstone demo",
            "scope": ["enrollment", "verification", "audit"],
        }
    )
    chain.enroll_identity(
        subject_id=subject_id,
        template_commitment="0x" + "11" * 32,
        consent_hash=consent_hash,
        model_version="arcface-r100-v1",
    )
    chain.log_verification(
        subject_id=subject_id,
        verification_hash="0x" + "22" * 32,
        model_version="arcface-r100-v1",
        accepted=True,
    )
    chain.revoke_template(subject_id=subject_id, reason_hash="0x" + "33" * 32)
    blocked_after_revoke = False
    try:
        chain.log_verification(
            subject_id=subject_id,
            verification_hash="0x" + "44" * 32,
            model_version="arcface-r100-v1",
            accepted=True,
        )
    except Revoked:
        blocked_after_revoke = True

    print(
        json.dumps(
            {
                "blockedAfterRevoke": blocked_after_revoke,
                "events": [
                    {
                        "eventType": event.event_type,
                        "subjectId": event.subject_id,
                        "payload": event.payload,
                        "timestamp": event.timestamp,
                    }
                    for event in chain.events
                ],
            },
            indent=2,
        )
    )
    return 0


def _cmd_train_siamese(args: argparse.Namespace) -> int:
    from trustfacechain.datasets import load_lfw_people_dataset, make_pairs
    from trustfacechain.models.siamese import train_siamese_model

    print("Loading LFW training samples...")
    samples = load_lfw_people_dataset(
        min_faces_per_person=2,
        max_samples=args.max_samples,
        data_home=args.data_home,
    )

    print("Generating genuine and impostor pairs for training...")
    pairs = make_pairs(
        samples,
        pairs_per_identity=args.pairs_per_identity,
        impostor_pairs=args.impostor_pairs,
        seed=args.seed,
    )

    if args.num_pairs is not None:
        pairs = pairs[:args.num_pairs]

    train_siamese_model(
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        train_pairs=pairs,
        save_path=args.save_path,
    )
    print("Siamese training finished successfully.")
    return 0


def _cmd_ablation_study(args: argparse.Namespace) -> int:
    from trustfacechain.datasets import load_lfw_official_pairs
    from trustfacechain.ablation import run_ablation_suite

    print("Loading LFW pairs for ablation study...")
    pairs = load_lfw_official_pairs(
        max_pairs=args.max_pairs,
        data_home=args.data_home,
        balanced_subset=not args.unbalanced,
    )

    run_ablation_suite(pairs, output_csv=args.csv)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trustfacechain")
    subparsers = parser.add_subparsers(dest="command", required=True)

    hash_consent = subparsers.add_parser(
        "hash-consent",
        help="Hash a consent JSON file using canonical JSON.",
    )
    hash_consent.add_argument("path")
    hash_consent.set_defaults(func=_cmd_hash_consent)

    smoke = subparsers.add_parser(
        "smoke-benchmark",
        help="Run a dependency-free benchmark smoke test.",
    )
    smoke.set_defaults(func=_cmd_smoke_benchmark)

    protect = subparsers.add_parser(
        "protect-template",
        help="Create a public protected-template record from a comma vector.",
    )
    protect.add_argument("--subject-id", required=True)
    protect.add_argument("--model-version", required=True)
    protect.add_argument("--app-salt", required=True)
    protect.add_argument("--vector", required=True)
    protect.set_defaults(func=_cmd_protect_template)

    train_siamese = subparsers.add_parser(
        "train-siamese",
        help="Train a self-trained Siamese CNN model on LFW images.",
    )
    train_siamese.add_argument("--epochs", type=int, default=5)
    train_siamese.add_argument("--batch-size", type=int, default=32)
    train_siamese.add_argument("--lr", type=float, default=0.001)
    train_siamese.add_argument("--num-pairs", type=int, default=1000)
    train_siamese.add_argument("--pairs-per-identity", type=int, default=4)
    train_siamese.add_argument("--impostor-pairs", type=int)
    train_siamese.add_argument("--max-samples", type=int)
    train_siamese.add_argument("--data-home", default="data/cache/scikit_learn")
    train_siamese.add_argument("--seed", type=int, default=7)
    train_siamese.add_argument("--save-path", default="data/cache/siamese_net.pt")
    train_siamese.set_defaults(func=_cmd_train_siamese)

    demo = subparsers.add_parser(
        "benchmark-demo",
        help="Benchmark built-in lightweight recognizers on synthetic face-like data.",
    )
    demo.add_argument("--models", help="Comma list: pixel,dct,lbp,eigenfaces")
    demo.add_argument("--identities", type=int, default=8)
    demo.add_argument("--samples-per-identity", type=int, default=4)
    demo.add_argument("--pairs-per-identity", type=int, default=2)
    demo.add_argument("--seed", type=int, default=7)
    demo.add_argument("--csv")
    demo.add_argument("--json")
    demo.set_defaults(func=_cmd_benchmark_demo)

    folder = subparsers.add_parser(
        "benchmark-folder",
        help="Benchmark recognizers on root/person_name/image files.",
    )
    folder.add_argument("root")
    folder.add_argument("--models", help="Comma list: pixel,dct,lbp,eigenfaces")
    folder.add_argument("--pairs-per-identity", type=int, default=2)
    folder.add_argument("--impostor-pairs", type=int)
    folder.add_argument("--seed", type=int, default=7)
    folder.add_argument("--csv")
    folder.add_argument("--json")
    folder.set_defaults(func=_cmd_benchmark_folder)

    lfw = subparsers.add_parser(
        "benchmark-lfw",
        help="Benchmark recognizers on LFW through scikit-learn.",
    )
    lfw.add_argument("--models", help="Comma list: pixel,dct,lbp,eigenfaces")
    lfw.add_argument("--min-faces-per-person", type=int, default=2)
    lfw.add_argument("--max-samples", type=int)
    lfw.add_argument("--data-home", default="data/cache/scikit_learn")
    lfw.add_argument("--pairs-per-identity", type=int, default=1)
    lfw.add_argument("--impostor-pairs", type=int)
    lfw.add_argument("--seed", type=int, default=7)
    lfw.add_argument("--csv")
    lfw.add_argument("--json")
    lfw.set_defaults(func=_cmd_benchmark_lfw)

    lfw_pairs = subparsers.add_parser(
        "benchmark-lfw-pairs",
        help="Benchmark recognizers on LFW official pairs.txt protocol.",
    )
    lfw_pairs.add_argument("--models", help="Comma list: pixel,dct,lbp,eigenfaces")
    lfw_pairs.add_argument("--max-pairs", type=int)
    lfw_pairs.add_argument("--data-home", default="data/cache/scikit_learn")
    lfw_pairs.add_argument("--unbalanced", action="store_true")
    lfw_pairs.add_argument("--csv")
    lfw_pairs.add_argument("--json")
    lfw_pairs.set_defaults(func=_cmd_benchmark_lfw_pairs)

    pairs_csv = subparsers.add_parser(
        "benchmark-pairs-csv",
        help="Benchmark recognizers on an explicit left_path,right_path,label CSV.",
    )
    pairs_csv.add_argument("csv_path")
    pairs_csv.add_argument("--models", help="Comma list: pixel,dct,lbp,eigenfaces")
    pairs_csv.add_argument("--csv")
    pairs_csv.add_argument("--json")
    pairs_csv.set_defaults(func=_cmd_benchmark_pairs_csv)

    robust = subparsers.add_parser(
        "robustness-demo",
        help="Run corruption sensitivity checks on synthetic face-like data.",
    )
    robust.add_argument("--models", default="pixel,dct")
    robust.add_argument("--identities", type=int, default=6)
    robust.add_argument("--samples-per-identity", type=int, default=4)
    robust.add_argument("--pairs-per-identity", type=int, default=1)
    robust.add_argument("--seed", type=int, default=7)
    robust.add_argument("--csv", default="reports/robustness_demo.csv")
    robust.set_defaults(func=_cmd_robustness_demo)

    chain = subparsers.add_parser(
        "demo-chain-flow",
        help="Run a local enroll -> verify -> revoke contract simulation.",
    )
    chain.set_defaults(func=_cmd_demo_chain_flow)

    ablation = subparsers.add_parser(
        "ablation-study",
        help="Run systematic ablation studies on LFW official pairs.",
    )
    ablation.add_argument("--max-pairs", type=int, default=50)
    ablation.add_argument("--data-home", default="data/cache/scikit_learn")
    ablation.add_argument("--unbalanced", action="store_true")
    ablation.add_argument("--csv", default="reports/ablation_results.csv")
    ablation.set_defaults(func=_cmd_ablation_study)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
