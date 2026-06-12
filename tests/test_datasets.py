import tempfile
import unittest
from pathlib import Path

from PIL import Image

from trustfacechain.datasets import load_pairs_csv, make_pairs, make_synthetic_face_dataset


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

    def test_load_pairs_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alice = root / "alice"
            bob = root / "bob"
            alice.mkdir()
            bob.mkdir()
            _write_image(alice / "one.png", color=60)
            _write_image(alice / "two.png", color=90)
            _write_image(bob / "one.png", color=140)
            csv_path = root / "pairs.csv"
            csv_path.write_text(
                "left_path,right_path,label,left_identity,right_identity\n"
                f"{alice / 'one.png'},{alice / 'two.png'},1,alice,alice\n"
                f"{alice / 'one.png'},{bob / 'one.png'},0,alice,bob\n",
                encoding="utf-8",
            )

            pairs = load_pairs_csv(csv_path)

        self.assertEqual(len(pairs), 2)
        self.assertEqual([pair.label for pair in pairs], [1, 0])
        self.assertEqual(pairs[0].left.identity, "alice")
        self.assertEqual(pairs[1].right.identity, "bob")

def _write_image(path: Path, *, color: int) -> None:
    Image.new("L", (24, 24), color=color).save(path)


if __name__ == "__main__":
    unittest.main()
