from __future__ import annotations

import argparse
from pathlib import Path

from image_index_model import ImageIndexer, load_dataset_from_folder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Entraîne un index d'images et lance une recherche par similarité."
    )
    parser.add_argument("--dataset", type=Path, required=True, help="Dossier dataset (un sous-dossier par classe).")
    parser.add_argument("--query", type=Path, required=True, help="Image de requête.")
    parser.add_argument("--top-k", type=int, default=5, help="Nombre de résultats retournés.")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    image_paths, labels = load_dataset_from_folder(args.dataset)
    indexer = ImageIndexer()
    indexer.index_images(image_paths, labels)

    print(f"Index construit avec {len(image_paths)} images.")
    print(f"Requête: {args.query}\n")

    results = indexer.query(args.query, k=args.top_k)
    for i, r in enumerate(results, start=1):
        print(f"{i:02d}. label={r.label:<20} distance={r.distance:.4f} path={r.image_path}")


if __name__ == "__main__":
    main()
