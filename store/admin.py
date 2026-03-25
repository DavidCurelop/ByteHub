from django.contrib import admin

from .models import Cart, CartItem, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'price', 'stock', 'is_available',
    )
    list_select_related = ('category',)
    list_filter = ('is_available', 'category')
    search_fields = ('name', 'brand')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'updated_at')
    list_select_related = ('user',)
    search_fields = ('user__email',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity')
    list_select_related = ('cart', 'product')
    search_fields = ('product__name', 'cart__user__email')
