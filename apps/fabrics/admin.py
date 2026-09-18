from django.contrib import admin

from .models import Fabric


@admin.register(Fabric)
class FabricAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'color', 'weight_gsm', 'price_per_meter', 'stock_units')
    search_fields = ('name', 'category', 'color', 'supplier')
    list_filter = ('category', 'color')
