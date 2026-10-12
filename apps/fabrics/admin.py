from django.contrib import admin

from .models import Fabric


@admin.register(Fabric)
class FabricAdmin(admin.ModelAdmin):
    list_display = (
        'fabric_name',
        'fiber_category',
        'weight',
        'stretch',
        'drape',
        'breathability',
        'opacity',
        'created_at',
        'updated_at',
    )
    search_fields = ('fabric_name', 'fiber_category')
    list_filter = ('fiber_category', 'stretch', 'drape', 'breathability', 'opacity')
