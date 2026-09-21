from app.core.config import Settings


def test_settings_default_values():
    """Verify default setting configuration loads correctly."""
    settings = Settings()
    assert settings.APP_NAME == "LLM Evaluation & Benchmarking Platform"
    assert settings.PORT == 8000
    assert settings.POSTGRES_PORT == 5432
    assert "postgresql" in settings.DATABASE_URL
