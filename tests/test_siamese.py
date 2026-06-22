import unittest
import numpy as np
import torch

from trustfacechain.models.siamese import SiameseNet, ContrastiveLoss, SiameseEmbedder, train_siamese_model
from trustfacechain.datasets import FacePair, FaceSample
from trustfacechain.metrics import evaluate_scores


class SiameseTest(unittest.TestCase):
    def test_siamese_net_shape(self):
        model = SiameseNet(embedding_dim=128)
        # Input shape: (Batch, Channel, Height, Width)
        x1 = torch.randn(4, 1, 112, 112)
        x2 = torch.randn(4, 1, 112, 112)
        out1, out2 = model(x1, x2)
        self.assertEqual(out1.shape, (4, 128))
        self.assertEqual(out2.shape, (4, 128))

    def test_contrastive_loss(self):
        loss_fn = ContrastiveLoss(margin=1.0)
        out1 = torch.tensor([[1.0, 0.0]], dtype=torch.float32)
        out2 = torch.tensor([[0.0, 1.0]], dtype=torch.float32)  # Distance = sqrt(2) ~ 1.414
        label_genuine = torch.tensor([[1.0]], dtype=torch.float32)
        label_impostor = torch.tensor([[0.0]], dtype=torch.float32)

        loss_gen = loss_fn(out1, out2, label_genuine)
        loss_imp = loss_fn(out1, out2, label_impostor)

        # For genuine, since distance is positive, loss is non-zero
        self.assertGreater(loss_gen.item(), 0.0)
        # For impostor, since distance (1.414) > margin (1.0), clamp makes it 0
        self.assertEqual(loss_imp.item(), 0.0)

    def test_siamese_embedder(self):
        embedder = SiameseEmbedder(model_path="data/cache/non_existent_model.pt")
        img = np.random.rand(112, 112).astype(np.float32)
        emb = embedder.embed(img)
        self.assertEqual(emb.shape, (128,))
        # Check that it's unit length normalized
        self.assertAlmostEqual(float(np.linalg.norm(emb)), 1.0, places=5)

    def test_train_siamese_model(self):
        # Create small mock training set
        left_sample = FaceSample(sample_id="s1", identity="personA", image=np.random.rand(112, 112).astype(np.float32))
        right_sample = FaceSample(sample_id="s2", identity="personA", image=np.random.rand(112, 112).astype(np.float32))
        pairs = [FacePair(left=left_sample, right=right_sample, label=1)]

        # Run 1 epoch of training
        model = train_siamese_model(
            epochs=1,
            batch_size=1,
            lr=0.01,
            train_pairs=pairs,
            save_path="data/cache/test_siamese_net.pt"
        )
        self.assertIsInstance(model, SiameseNet)


class ExtendedMetricsTest(unittest.TestCase):
    def test_extended_metrics(self):
        # A perfect verification prediction
        report = evaluate_scores(
            scores=[0.9, 0.8, 0.1, 0.2],
            labels=[1, 1, 0, 0]
        )
        self.assertAlmostEqual(report.best_precision, 1.0)
        self.assertAlmostEqual(report.best_recall, 1.0)
        self.assertAlmostEqual(report.best_f1_score, 1.0)
        self.assertAlmostEqual(report.auc, 1.0)

        # An imperfect prediction
        report_imperfect = evaluate_scores(
            scores=[0.9, 0.2, 0.8, 0.1], # 1 target is 0.2 (miss), 1 non-target is 0.8 (false alarm)
            labels=[1, 1, 0, 0]
        )
        self.assertLess(report_imperfect.auc, 1.0)


if __name__ == "__main__":
    unittest.main()
