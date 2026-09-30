from django.contrib import admin

from .models import Fabric


@admin.register(Fabric)
class FabricAdmin(admin.ModelAdmin):
    list_display = (
        'fabric_name',
        'fiber_category',
        'fiber',
        'fabric_type',
        'composition',
        'construction',
        'weight',
        'stretch',
        'structure',
        'breathability',
        'opacity',
        'created_at',
        'updated_at',
    )
    search_fields = ('fabric_name', 'fiber_category', 'composition', 'construction')
    list_filter = ('fiber_category', 'construction', 'stretch', 'structure', 'breathability', 'opacity')
