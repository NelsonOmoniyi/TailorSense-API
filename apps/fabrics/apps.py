from django.apps import AppConfig


class FabricsConfig(AppConfig):
    """Register the fabrics app and configure its default model field type."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.fabrics'
