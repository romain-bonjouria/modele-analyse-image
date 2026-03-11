from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence


class BaseImageEmbedder:
    def encode(self, image_paths: Sequence[Path]) -> list[list[float]]:
        raise NotImplementedError


class ByteHistogramEmbedder(BaseImageEmbedder):
    """Offline embedder using normalized histogram of file bytes.

    Works without third-party dependencies; robust for constrained environments.
    """

    def __init__(self, bins: int = 256) -> None:
        if bins <= 0:
            raise ValueError("bins doit être > 0")
        self.bins = bins

    def _one(self, image_path: Path) -> list[float]:
        raw = Path(image_path).read_bytes()
        if not raw:
            return [0.0] * self.bins

        hist = [0] * self.bins
        for b in raw:
            bucket = (b * self.bins) // 256
            if bucket == self.bins:
                bucket -= 1
            hist[bucket] += 1

        norm = sum(v * v for v in hist) ** 0.5
        if norm == 0:
            return [0.0] * self.bins
        return [v / norm for v in hist]

    def encode(self, image_paths: Sequence[Path]) -> list[list[float]]:
        if not image_paths:
            raise ValueError("image_paths ne peut pas être vide.")
        return [self._one(Path(p)) for p in image_paths]


@dataclass
class SearchResult:
    image_path: str
    label: str
    distance: float


class ImageIndexer:
    def __init__(self, embedder: BaseImageEmbedder | None = None) -> None:
        self.embedder = embedder or ByteHistogramEmbedder()
        self._vectors: list[list[float]] = []
        self._paths: list[str] = []
        self._labels: list[str] = []

    def fit(self, image_paths: Sequence[Path], labels: Sequence[str], n_neighbors: int = 5) -> None:
        if len(image_paths) != len(labels):
            raise ValueError("image_paths et labels doivent avoir la même taille.")
        if len(image_paths) == 0:
            raise ValueError("Le dataset d'entraînement est vide.")
        if n_neighbors <= 0:
            raise ValueError("n_neighbors doit être > 0")

        self._vectors = self.embedder.encode(image_paths)
        self._paths = [str(Path(p)) for p in image_paths]
        self._labels = list(labels)

    def index_images(self, image_paths: Sequence[Path], labels: Sequence[str]) -> None:
        self.fit(image_paths=image_paths, labels=labels)

    @staticmethod
    def _cosine_distance(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        return 1.0 - dot

    def query(self, query_image: Path, k: int = 5) -> List[SearchResult]:
        if not self._vectors:
            raise RuntimeError("Le modèle doit être entraîné/indexé avant une requête.")
        if k <= 0:
            raise ValueError("k doit être > 0")

        query_vec = self.embedder.encode([Path(query_image)])[0]
        scored: list[tuple[int, float]] = []
        for idx, vec in enumerate(self._vectors):
            scored.append((idx, self._cosine_distance(query_vec, vec)))

        scored.sort(key=lambda x: x[1])
        top = scored[: min(k, len(scored))]

        return [
            SearchResult(
                image_path=self._paths[idx],
                label=self._labels[idx],
                distance=dist,
            )
            for idx, dist in top
        ]


def load_dataset_from_folder(dataset_root: Path) -> tuple[list[Path], list[str]]:
    image_paths: list[Path] = []
    labels: list[str] = []

    valid_suffixes = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"}
    for class_dir in sorted(p for p in Path(dataset_root).iterdir() if p.is_dir()):
        for image_path in sorted(class_dir.iterdir()):
            if image_path.suffix.lower() in valid_suffixes:
                image_paths.append(image_path)
                labels.append(class_dir.name)

    if not image_paths:
        raise ValueError(f"Aucune image trouvée dans {dataset_root}.")

    return image_paths, labels
