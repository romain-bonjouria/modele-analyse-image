from __future__ import annotations

import os
import sys
from pathlib import Path


def _streamlit_args(app_path: Path) -> list[str]:
    """Construit les arguments streamlit pour démarrer l'app RAG."""
    return [
        "streamlit",
        "run",
        str(app_path),
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]


def main() -> None:
    try:
        from streamlit.web import cli as stcli
    except ImportError as exc:
        raise RuntimeError("Streamlit non installé. Installez les dépendances du projet.") from exc

    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

    # En mode source, streamlit_app.py est à côté de ce fichier.
    # En mode PyInstaller onefile, il est extrait dans _MEIPASS.
    app_path = base_dir / "streamlit_app.py"

    if not app_path.exists():
        raise FileNotFoundError(f"Impossible de trouver streamlit_app.py ({app_path})")

    os.environ.setdefault("PYTHONPATH", str(base_dir))
    sys.argv = _streamlit_args(app_path)
    raise SystemExit(stcli.main())


if __name__ == "__main__":
    main()
