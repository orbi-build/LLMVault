"""Debug mode must come from LLMVAULT_DEBUG and stay off unless opted in.

The Werkzeug interactive debugger runs arbitrary Python, so `python app.py`
must not enable it by default (upstream CyberSunil/LLMVault#28).
"""
import os
import sys
import tempfile

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import config
config.DATA_FILE = os.path.join(tempfile.gettempdir(), "llmvault_debug_env_test_progress.json")

import app as server  # noqa: E402


def test_debug_off_when_unset():
    assert config.debug_enabled({}) is False


@pytest.mark.parametrize("value", ["", "  ", "0", "false", "no", "off"])
def test_debug_off_for_missing_or_falsey_values(value):
    assert config.debug_enabled({"LLMVAULT_DEBUG": value}) is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE", " True ", "True"])
def test_debug_on_for_1_and_true(value):
    assert config.debug_enabled({"LLMVAULT_DEBUG": value}) is True


def test_debug_enabled_reads_process_environment(monkeypatch):
    monkeypatch.delenv("LLMVAULT_DEBUG", raising=False)
    assert config.debug_enabled() is False

    monkeypatch.setenv("LLMVAULT_DEBUG", "1")
    assert config.debug_enabled() is True

    monkeypatch.setenv("LLMVAULT_DEBUG", "true")
    assert config.debug_enabled() is True


@pytest.mark.parametrize("debug", [True, False])
def test_main_forwards_config_debug_to_app_run(monkeypatch, debug):
    """The entry point starts the server with config.DEBUG, not a hardcoded flag."""
    monkeypatch.setattr(server.config, "LIVE_MODE_ENABLED", False)
    monkeypatch.setattr(server.config, "DEBUG", debug)
    captured = {}
    monkeypatch.setattr(server.app, "run", lambda **kwargs: captured.update(kwargs))

    server.main()

    assert captured["debug"] is debug
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 5000


def test_main_prints_live_banner_when_enabled(monkeypatch, capsys):
    monkeypatch.setattr(server.config, "LIVE_MODE_ENABLED", True)
    monkeypatch.setattr(server.model_registry, "startup_banner", lambda: "LIVE BANNER")
    monkeypatch.setattr(server.app, "run", lambda **kwargs: None)

    server.main()

    assert "LIVE BANNER" in capsys.readouterr().out
