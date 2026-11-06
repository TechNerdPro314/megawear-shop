from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'product_sku', 'price', 'quantity', 'total_price')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',                   # в списке можно, это не форма редактирования
        'customer_name',
        'customer_email',
        'total_amount',
        'status',
        'delivery_method',
        'created_at',
    ]
    list_filter = ['status', 'delivery_method', 'created_at']
    search_fields = ['id', 'customer_name', 'customer_email', 'customer_phone']
    readonly_fields = [
        'subtotal_amount',
        'discount_amount',
        'delivery_cost',
        'coupon_code',
        'total_amount',
        'created_at',
        'updated_at',
        'user',
    ]
    fieldsets = (
        ('Информация о заказчике', {
            'fields': (
                'user',
                'customer_name',
                'customer_email',
                'customer_phone',
            )
        }),
        ('Доставка', {
            'fields': (
                'delivery_method',
                'delivery_address',
            )
        }),
        ('Детали заказа', {
            'fields': (
                'subtotal_amount',
                'discount_amount',
                'delivery_cost',
                'coupon_code',
                'total_amount',
                'status',
                'payment_method',
            )
        }),
        ('Комментарии', {
            'fields': (
                'comment',
                'manager_comment',
            )
        }),
        ('Даты', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )
    inlines = [OrderItemInline]