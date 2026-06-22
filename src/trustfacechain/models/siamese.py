"""Siamese Network model and training pipeline."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Try importing torch. If not available, we fail gracefully when instantiated.
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Define dummy classes so type references don't fail immediately
    class nn:
        class Module:
            pass


class SiameseNet(nn.Module):
    """A lightweight convolutional Siamese neural network for face verification."""

    def __init__(self, embedding_dim: int = 128):
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required to initialize SiameseNet.")
        super().__init__()
        # Input size: (Batch, 1, 112, 112)
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
        self.pool1 = nn.MaxPool2d(2, 2)  # 112x112 -> 56x56
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.pool2 = nn.MaxPool2d(2, 2)  # 56x56 -> 28x28
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool3 = nn.MaxPool2d(2, 2)  # 28x28 -> 14x14
        self.fc1 = nn.Linear(64 * 14 * 14, 256)
        self.fc2 = nn.Linear(256, embedding_dim)

    def forward_once(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool1(F.relu(self.conv1(x)))
        x = self.pool2(F.relu(self.conv2(x)))
        x = self.pool3(F.relu(self.conv3(x)))
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

    def forward(self, input1: torch.Tensor, input2: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        output1 = self.forward_once(input1)
        output2 = self.forward_once(input2)
        return output1, output2


class ContrastiveLoss(nn.Module):
    """Contrastive loss function for pair-based distance learning.

    L = 0.5 * Y * D^2 + 0.5 * (1 - Y) * max(0, margin - D)^2
    where Y = 1 for genuine (same identity) and Y = 0 for impostor (different identity).
    """

    def __init__(self, margin: float = 1.0):
        super().__init__()
        self.margin = margin

    def forward(self, output1: torch.Tensor, output2: torch.Tensor, label: torch.Tensor) -> torch.Tensor:
        output1 = F.normalize(output1, p=2, dim=1)
        output2 = F.normalize(output2, p=2, dim=1)
        euclidean_distance = F.pairwise_distance(output1, output2, keepdim=True)
        loss_contrastive = torch.mean(
            label * torch.pow(euclidean_distance, 2)
            + (1 - label) * torch.pow(torch.clamp(self.margin - euclidean_distance, min=0.0), 2)
        )
        return loss_contrastive


class SiameseEmbedder:
    """FaceEmbedder adapter for the self-trained Siamese CNN model."""

    name = "siamese"
    version = "self-trained"
    embedding_dim = 128

    def __init__(self, model_path: str | Path = "data/cache/siamese_net.pt"):
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for SiameseEmbedder.")

        self.model_path = Path(model_path)
        self._device = torch.device("cpu")
        self._model = SiameseNet(embedding_dim=self.embedding_dim)

        if self.model_path.exists():
            try:
                state_dict = torch.load(self.model_path, map_location=self._device)
                self._model.load_state_dict(state_dict)
                logger.info(f"Loaded Siamese model weights from {self.model_path}")
            except Exception as e:
                logger.warning(f"Failed to load weights from {self.model_path}: {e}. Using random initialization.")
        else:
            logger.warning(f"Weights file {self.model_path} not found. Using random initialization.")

        self._model.to(self._device)
        self._model.eval()

    def fit(self, images: list[np.ndarray]) -> None:
        return None

    def embed(self, image: np.ndarray) -> np.ndarray:
        # Preprocess input image: resize to 112x112 and ensure grayscale
        from PIL import Image

        # Convert image to grayscale uint8 if not already
        if image.ndim == 3:
            # simple average or RGB to L conversion
            if image.shape[2] == 3:
                image = 0.2989 * image[:, :, 0] + 0.5870 * image[:, :, 1] + 0.1140 * image[:, :, 2]
            elif image.shape[2] == 4:
                image = 0.2989 * image[:, :, 0] + 0.5870 * image[:, :, 1] + 0.1140 * image[:, :, 2]
        
        if image.dtype != np.uint8:
            image = np.clip(image * 255.0, 0, 255).astype(np.uint8)

        pil_img = Image.fromarray(image, mode="L").resize((112, 112), Image.Resampling.BILINEAR)
        img_arr = np.asarray(pil_img, dtype=np.float32) / 255.0

        tensor = torch.tensor(img_arr, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(self._device)
        with torch.no_grad():
            embedding = self._model.forward_once(tensor)
            # L2 normalize the embedding
            embedding = F.normalize(embedding, p=2, dim=1)
            embedding_np = embedding.cpu().numpy()[0]

        from trustfacechain.image_io import normalize_vector
        return normalize_vector(embedding_np.astype(np.float32))

    def score(self, embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
        return float(np.dot(embedding_a, embedding_b))


def train_siamese_model(
    epochs: int = 5,
    batch_size: int = 32,
    lr: float = 0.001,
    train_pairs: list[FacePair] | None = None,
    save_path: str | Path = "data/cache/siamese_net.pt",
) -> SiameseNet:
    """Train the Siamese network on the provided face verification pairs."""
    if not TORCH_AVAILABLE:
        raise RuntimeError("PyTorch is required for training.")

    if not train_pairs:
        raise ValueError("Training pairs must be provided.")

    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    device = torch.device("cpu")
    model = SiameseNet(embedding_dim=128).to(device)
    criterion = ContrastiveLoss(margin=1.0)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    logger.info(f"Starting Siamese training on {len(train_pairs)} pairs for {epochs} epochs...")
    model.train()

    best_loss = float("inf")

    for epoch in range(epochs):
        # Shuffle pairs
        np.random.shuffle(train_pairs)
        epoch_loss = 0.0
        batches = len(train_pairs) // batch_size
        if len(train_pairs) % batch_size != 0:
            batches += 1

        for i in range(batches):
            batch_data = train_pairs[i * batch_size : (i + 1) * batch_size]
            left_imgs = []
            right_imgs = []
            labels = []

            for pair in batch_data:
                # Preprocess image arrays
                left_arr = pair.left.image
                right_arr = pair.right.image
                if left_arr.ndim == 3:
                    left_arr = left_arr[:, :, 0]
                if right_arr.ndim == 3:
                    right_arr = right_arr[:, :, 0]

                left_imgs.append(torch.tensor(left_arr, dtype=torch.float32).unsqueeze(0))
                right_imgs.append(torch.tensor(right_arr, dtype=torch.float32).unsqueeze(0))
                labels.append(pair.label)

            if not left_imgs:
                continue

            left_tensor = torch.stack(left_imgs).to(device)
            right_tensor = torch.stack(right_imgs).to(device)
            labels_tensor = torch.tensor(labels, dtype=torch.float32).unsqueeze(1).to(device)

            optimizer.zero_grad()
            out1, out2 = model(left_tensor, right_tensor)
            loss = criterion(out1, out2, labels_tensor)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item() * len(batch_data)

        epoch_loss /= len(train_pairs)
        logger.info(f"Epoch {epoch + 1}/{epochs} - Loss: {epoch_loss:.4f}")

        if epoch_loss < best_loss:
            best_loss = epoch_loss
            torch.save(model.state_dict(), save_path)
            logger.info(f"Saved new best model checkpoint to {save_path}")

    logger.info("Training complete.")
    return model
