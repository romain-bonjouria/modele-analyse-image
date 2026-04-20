from pathlib import Path

from windows_launcher import _streamlit_args


def test_streamlit_args_contains_run_and_app_path() -> None:
    app = Path("src/streamlit_app.py")
    args = _streamlit_args(app)

    assert args[0] == "streamlit"
    assert args[1] == "run"
    assert str(app) in args
    assert "--server.headless=true" in args
