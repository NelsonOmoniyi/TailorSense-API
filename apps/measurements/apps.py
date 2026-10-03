from django.apps import AppConfig


class MeasurementsConfig(AppConfig):
    """Register the normalized measurement and garment-requirement domain."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.measurements'