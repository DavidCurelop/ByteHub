from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'price', 'stock', 'is_available',
    )
    list_select_related = ('category', 'created_by')
    list_filter = ('is_available', 'category')
    search_fields = ('name', 'brand')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']
