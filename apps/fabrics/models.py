"""Recommendation-focused fabric model for TailorSense."""

from django.db import models


class Fabric(models.Model):
    """A fabric record used to evaluate garment suitability for a user's measurements."""

    class PropertyLevel(models.TextChoices):
        NONE = 'none', 'None'
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    class Drape(models.TextChoices):
        FLOWING = 'flowing', 'Flowing'
        SOFT = 'soft', 'Soft'
        FIRM = 'firm', 'Firm'
        STIFF = 'stiff', 'Stiff'

    fabric_name = models.CharField(max_length=150)
    image = models.ImageField(upload_to='fabrics/', blank=True)
    fiber_category = models.CharField(max_length=100, blank=True)
    weight = models.CharField(max_length=100, blank=True)
    stretch = models.CharField(
        max_length=20,
        choices=PropertyLevel.choices,
        default=PropertyLevel.NONE,
        blank=True,
    )
    drape = models.CharField(
        max_length=20,
        choices=Drape.choices,
        default=Drape.SOFT,
        blank=True,
    )
    breathability = models.CharField(
        max_length=20,
        choices=PropertyLevel.choices,
        default=PropertyLevel.NONE,
        blank=True,
    )
    opacity = models.CharField(
        max_length=20,
        choices=PropertyLevel.choices,
        default=PropertyLevel.NONE,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fabric_name']

    def __str__(self):
        return self.fabric_name



