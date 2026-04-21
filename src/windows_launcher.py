from __future__ import annotations

import os
import sys
from pathlib import Path


def _default_ollama_locations() -> list[Path]:
    candidates: list[Path] = []
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "Programs" / "Ollama")
    candidates.append(Path("C:/Program Files/Ollama"))
    return candidates


def _ensure_ollama_in_path() -> None:
    current_path = os.getenv("PATH", "")
    for location in _default_ollama_locations():
        ollama_exe = location / "ollama.exe"
        if ollama_exe.exists() and str(location) not in current_path:
            os.environ["PATH"] = f"{current_path};{location}"
            return


def _streamlit_args(app_path: Path) -> list[str]:
    """Construit les arguments streamlit pour démarrer l'app RAG."""
    return [
        "streamlit",
        "run",
        str(app_path),
        "--global.developmentMode=false",
        "--server.headless=false",
        "--server.port=8501",
        "--browser.serverAddress=localhost",
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

    _ensure_ollama_in_path()
    os.environ.setdefault("PYTHONPATH", str(base_dir))
    sys.argv = _streamlit_args(app_path)
    raise SystemExit(stcli.main())


if __name__ == "__main__":
    main()
