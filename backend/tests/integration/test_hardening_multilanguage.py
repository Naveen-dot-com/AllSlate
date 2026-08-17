from backend.app.config import get_hardening_config


def test_supported_languages_are_configured():
    config = get_hardening_config()
    assert "en" in config.supported_languages
    assert "es" in config.supported_languages
