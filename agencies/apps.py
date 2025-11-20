from django.apps import AppConfig


class AgenciesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agencies"

    def ready(self):
        """Import signals when the app is ready."""
        import agencies.signals  # noqa: F401
