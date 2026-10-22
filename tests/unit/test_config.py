from src.core.config import Settings


def test_settings_default_values():
    """Verify that default settings conform to the architecture specification."""
    settings = Settings()

    assert settings.PROJECT_NAME == "Distributed Automation Platform"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.CELERY_DEFAULT_QUEUE == "celery"
    # Visibility timeout must exceed task time limit
    assert settings.CELERY_VISIBILITY_TIMEOUT > settings.CELERY_TASK_TIME_LIMIT
    assert settings.CELERY_TASK_TIME_LIMIT > settings.CELERY_TASK_SOFT_TIME_LIMIT
    assert settings.HEARTBEAT_INTERVAL_SECONDS < settings.STALE_TIMEOUT_SECONDS
    assert settings.STALE_TIMEOUT_SECONDS < settings.OFFLINE_TIMEOUT_SECONDS


def test_settings_override():
    """Verify settings can be overridden cleanly for custom environments."""
    custom = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        STALE_TIMEOUT_SECONDS=45,
    )
    assert custom.ENVIRONMENT == "production"
    assert custom.DEBUG is False
    assert custom.STALE_TIMEOUT_SECONDS == 45
