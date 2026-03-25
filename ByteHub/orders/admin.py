from django.contrib import admin

from .models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('get_subtotal',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__email',)
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'payment_method',
        'amount',
        'status',
        'transaction_id',
        'paid_at',
    )
    list_filter = ('payment_method', 'status')
    search_fields = ('transaction_id', 'order__user__email')
