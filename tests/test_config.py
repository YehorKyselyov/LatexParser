import os
import pytest

from latex_parser.config import Config
from latex_parser.renderer import LatexBackend


class TestConfigFromEnv:
    def test_valid_config(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_TOKEN", "test-token-123")
        monkeypatch.setenv("LATEX_BACKEND", "matplotlib")
        monkeypatch.setenv("MAX_EXPRESSIONS_PER_MESSAGE", "10")

        config = Config.from_env()

        assert config.telegram_token == "test-token-123"
        assert config.backend == LatexBackend.MATPLOTLIB
        assert config.max_expressions == 10

    def test_missing_token_raises(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)

        with pytest.raises(ValueError, match="TELEGRAM_TOKEN"):
            Config.from_env()

    def test_empty_token_raises(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_TOKEN", "   ")

        with pytest.raises(ValueError, match="TELEGRAM_TOKEN"):
            Config.from_env()

    def test_default_backend(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_TOKEN", "tok")
        monkeypatch.delenv("LATEX_BACKEND", raising=False)

        config = Config.from_env()
        assert config.backend == LatexBackend.MATPLOTLIB

    def test_invalid_backend_falls_back(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_TOKEN", "tok")
        monkeypatch.setenv("LATEX_BACKEND", "invalid_engine")

        config = Config.from_env()
        assert config.backend == LatexBackend.MATPLOTLIB

    def test_weasyprint_backend(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_TOKEN", "tok")
        monkeypatch.setenv("LATEX_BACKEND", "WeasyPrint")

        config = Config.from_env()
        assert config.backend == LatexBackend.WEASYPRINT

    def test_default_max_expressions(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_TOKEN", "tok")
        monkeypatch.delenv("MAX_EXPRESSIONS_PER_MESSAGE", raising=False)

        config = Config.from_env()
        assert config.max_expressions == 5

    def test_invalid_max_expressions_falls_back(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_TOKEN", "tok")
        monkeypatch.setenv("MAX_EXPRESSIONS_PER_MESSAGE", "abc")

        config = Config.from_env()
        assert config.max_expressions == 5

    def test_negative_max_expressions_falls_back(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_TOKEN", "tok")
        monkeypatch.setenv("MAX_EXPRESSIONS_PER_MESSAGE", "-1")

        config = Config.from_env()
        assert config.max_expressions == 5

    def test_config_is_frozen(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_TOKEN", "tok")

        config = Config.from_env()
        with pytest.raises(AttributeError):
            config.telegram_token = "new"
