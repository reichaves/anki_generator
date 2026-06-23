import os
import pytest
from pydantic import ValidationError
from unittest.mock import patch


def test_config_loading_success() -> None:
    with patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY": "test_key",
            "ANKI_CONNECT_URL": "http://test:8765",
            "LOG_LEVEL": "DEBUG",
        },
    ):
        from anki_generator.config import Settings

        settings_instance = Settings(_env_file=None)
        assert settings_instance.gemini_api_key == "test_key"
        assert settings_instance.anki_connect_url == "http://test:8765"
        assert settings_instance.log_level == "DEBUG"


def test_config_loading_missing_key() -> None:
    with patch.dict(os.environ, {}, clear=True):
        from anki_generator.config import Settings

        with pytest.raises(ValidationError):
            Settings(_env_file=None)
