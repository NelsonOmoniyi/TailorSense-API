from django.contrib import admin

from .models import Fabric


@admin.register(Fabric)
class FabricAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'composition',
        'construction',
        'weight_gsm',
        'stretch',
        'drape',
        'structure',
        'breathability',
        'opacity',
    )
    search_fields = ('name', 'category', 'composition', 'construction')
    list_filter = ('category', 'construction', 'stretch', 'drape', 'structure', 'breathability', 'opacity')
