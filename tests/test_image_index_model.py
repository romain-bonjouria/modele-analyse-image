from pathlib import Path

from image_index_model import ImageIndexer, load_dataset_from_folder


def _write_fake_image(path: Path, payload: bytes) -> None:
    path.write_bytes(payload)


def test_index_and_query_returns_closest_label(tmp_path: Path) -> None:
    red_dir = tmp_path / "red"
    blue_dir = tmp_path / "blue"
    red_dir.mkdir()
    blue_dir.mkdir()

    _write_fake_image(red_dir / "r1.jpg", b"\xe0\xe0\x10" * 100)
    _write_fake_image(red_dir / "r2.jpg", b"\xd0\xd0\x20" * 100)
    _write_fake_image(blue_dir / "b1.jpg", b"\x40\x40\x80" * 100)

    query = tmp_path / "query.jpg"
    _write_fake_image(query, b"\xe0\xe0\x10" * 100)

    image_paths, labels = load_dataset_from_folder(tmp_path)
    indexer = ImageIndexer()
    indexer.index_images(image_paths, labels)

    results = indexer.query(query, k=1)

    assert results[0].label == "red"


def test_load_dataset_raises_on_empty_folder(tmp_path: Path) -> None:
    (tmp_path / "classA").mkdir()

    try:
        load_dataset_from_folder(tmp_path)
        assert False, "A ValueError should have been raised"
    except ValueError as exc:
        assert "Aucune image" in str(exc)
