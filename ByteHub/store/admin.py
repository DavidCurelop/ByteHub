from django.contrib import admin

from .models import Address, Cart, CartItem, Order, OrderItem, Product


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


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'city', 'country', 'is_default')
    list_select_related = ('user',)
    search_fields = ('user__email', 'city', 'country')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at')
    list_select_related = ('user', 'shipping_address')
    search_fields = ('user__email',)
    list_filter = ('status',)
    readonly_fields = ('created_at',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'unit_price')
    list_select_related = ('order', 'product')
