"""Database model for the TailorSense fabric inventory."""

from django.db import models


class Fabric(models.Model):
    """A single fabric record used in garment planning and tailoring workflows."""

    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100, blank=True)
    composition = models.CharField(max_length=200, blank=True)
    color = models.CharField(max_length=100, blank=True)
    weight_gsm = models.PositiveIntegerField(default=0)
    price_per_meter = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    stock_units = models.PositiveIntegerField(default=0)
    supplier = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Keep listing and lookup behavior predictable for the UI and admin.
        ordering = ['name']

    def __str__(self):
        return self.name
