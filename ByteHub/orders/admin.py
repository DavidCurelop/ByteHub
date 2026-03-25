from django.contrib import admin

from .models import Cart, CartItem, Order, OrderItem, Payment


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('get_subtotal',)

    @admin.display(description='Subtotal')
    def get_subtotal(self, obj):
        return obj.get_subtotal()


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'get_total', 'get_item_count', 'updated_at')
    list_select_related = ('user',)
    inlines = [CartItemInline]

    @admin.display(description='Total')
    def get_total(self, obj):
        return obj.get_total()

    @admin.display(description='Items')
    def get_item_count(self, obj):
        return obj.get_item_count()


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('get_subtotal',)

    @admin.display(description='Subtotal')
    def get_subtotal(self, obj):
        return obj.get_subtotal()


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'user', 'status', 'subtotal',
        'shipping_cost', 'total_amount', 'created_at',
    )
    list_filter = ('status',)
    list_select_related = ('user', 'shipping_address')
    readonly_fields = ('created_at',)
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'order', 'payment_method', 'status',
        'amount', 'paid_at',
    )
    list_filter = ('status', 'payment_method')
    list_select_related = ('order',)
    readonly_fields = ('paid_at',)
    search_fields = ('transaction_id',)
