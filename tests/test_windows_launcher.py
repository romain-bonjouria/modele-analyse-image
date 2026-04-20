from pathlib import Path

from windows_launcher import _default_ollama_locations, _streamlit_args


def test_streamlit_args_contains_run_and_app_path() -> None:
    app = Path("src/streamlit_app.py")
    args = _streamlit_args(app)

    assert args[0] == "streamlit"
    assert args[1] == "run"
    assert str(app) in args
    assert "--server.headless=true" in args


def test_default_ollama_locations_contains_program_files() -> None:
    locations = _default_ollama_locations()
    as_strings = [str(p) for p in locations]
    assert "C:/Program Files/Ollama" in as_strings


def test_default_ollama_locations_includes_localappdata_when_present(monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", "C:/Users/Test/AppData/Local")
    locations = _default_ollama_locations()
    assert str(locations[0]).endswith("AppData/Local/Programs/Ollama")
